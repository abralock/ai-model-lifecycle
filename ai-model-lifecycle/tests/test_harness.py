"""tests/test_harness.py — smoke tests for the Gate 1 harness foundation.

These run offline (no OpenRouter call). DB-backed scorer tests are marked and
auto-skip when Postgres is unreachable.

    pytest -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from common import CASES_DIR, REPO_ROOT, load_config, run_path
from pricing import cost_usd, get_price
from scorers.base import parse_deletes, parse_files
from scorers.dispatch import score_case
from runner import build_prompt

CONFIG = load_config()
REQUIRED_CASES = {
    "r1_springboot2to3": ["pom.xml", "README.md", "prompt.md"],
    "r3_oracle_to_postgres": [
        "procedures/sp_customer_tier.sql",
        "procedures/sp_monthly_report.sql",
        "golden_postgres.sql",
        "golden_output.csv",
        "seed.sql",
        "prompt.md",
    ],
    "r4_schema_load_optimize": ["schema.sql", "seed.py", "target_query.sql", "prompt.md"],
    "r5_etl_dashboard": ["etl_spec.md", "dashboard_schema.sql", "prompt.md"],
}


# --------------------------------------------------------------------------- #
# config / matrix                                                              #
# --------------------------------------------------------------------------- #
def test_config_parses_and_has_pilot_pair():
    pair = CONFIG.get_pair("opus-4.8-vs-5.5")
    assert pair.current.id == "anthropic/claude-opus-4.8"
    assert pair.target.id == "anthropic/claude-opus-5.5"


def test_all_configured_cases_have_dirs():
    for case_id in CONFIG.cases:
        assert (CASES_DIR / case_id).is_dir(), f"missing case dir: {case_id}"


def test_defaults_are_deterministic():
    assert CONFIG.temperature == 0
    assert CONFIG.max_tokens > 0


# --------------------------------------------------------------------------- #
# case artifacts (verification item c)                                         #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("case_id,required", REQUIRED_CASES.items())
def test_case_has_required_files(case_id, required):
    for rel in required:
        assert (CASES_DIR / case_id / rel).is_file(), f"missing {case_id}/{rel}"


def test_r1_module_has_java_and_factories():
    r1 = CASES_DIR / "r1_springboot2to3"
    javas = list(r1.rglob("*.java"))
    assert len(javas) >= 8, "R1 should ship ~8-10 Java files"
    assert (r1 / "src/main/resources/META-INF/spring.factories").is_file()
    # input must actually use javax.* (that's the whole point of the case)
    blob = "\n".join(p.read_text() for p in javas)
    assert "javax." in blob


# --------------------------------------------------------------------------- #
# prompt assembly                                                              #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("case_id", list(REQUIRED_CASES))
def test_build_prompt_inlines_task_and_listing(case_id):
    prompt = build_prompt(case_id)
    assert len(prompt) > 100
    # the case file listing is always attached
    assert f"CASE FILE LISTING ({case_id})" in prompt


# --------------------------------------------------------------------------- #
# output parsing                                                               #
# --------------------------------------------------------------------------- #
def test_parse_files_and_deletes():
    txt = "### FILE: a/b.sql\n```sql\nSELECT 1;\n```\n### DELETE: x/old.txt\n"
    assert parse_files(txt) == {"a/b.sql": "SELECT 1;\n"}
    assert parse_deletes(txt) == ["x/old.txt"]


def test_run_path_is_filesystem_safe():
    p = run_path("pair-x", "anthropic/claude-opus-4.8", "r1_springboot2to3", run_dt="20261009")
    assert "/" not in p.name
    assert p.name == "anthropic__claude-opus-4.8.r1_springboot2to3.20261009.json"


# --------------------------------------------------------------------------- #
# scorers: never crash, always structured                                      #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("case_id", list(REQUIRED_CASES) + ["unknown_case"])
def test_scorers_return_structured_result_on_empty(case_id):
    r = score_case(case_id, "", "test/model")
    assert r.passed is False
    assert r.score == 0.0
    assert r.reason  # non-empty reason, no exception


def test_r1_scorer_static_pass_and_fail(monkeypatch):
    from scorers import r1_scorer
    from tests.r1_reference import reference_output

    monkeypatch.setattr(r1_scorer, "_maven_argv", lambda project: None)  # static only
    r = r1_scorer.score(reference_output(), model_slug="t/m")
    assert r.checks["boot3_pom"] and r.checks["javax_free"] and r.checks["factories_gone"]

    r2 = r1_scorer.score(reference_output(migrate=False), model_slug="t/m")
    assert not r2.passed and not r2.checks["boot3_pom"] and not r2.checks["javax_free"]


def test_r1_prompt_inlines_sources():
    prompt = build_prompt("r1_springboot2to3")
    assert "--- ARTIFACT: pom.xml ---" in prompt
    assert "--- ARTIFACT: src/main/java/com/example/demo/config/WebConfig.java ---" in prompt
    assert "import javax.servlet.Filter;" in prompt


# --------------------------------------------------------------------------- #
# pricing / cost                                                               #
# --------------------------------------------------------------------------- #
def test_cost_math():
    # 1M input @ 5 USD + 1M output @ 25 USD (opus-4.8, verified 2026-10-08)
    c = cost_usd("anthropic/claude-opus-4.8", input_tokens=1_000_000, output_tokens=1_000_000)
    assert abs(c - 30.0) < 1e-9
    # 1M input @ 4 USD + 1M output @ 20 USD (opus-5.5, verified 2026-10-08)
    c2 = cost_usd("anthropic/claude-opus-5.5", input_tokens=1_000_000, output_tokens=1_000_000)
    assert abs(c2 - 24.0) < 1e-9


def test_unknown_model_uses_default_price():
    from pricing import DEFAULT_PRICE
    assert get_price("does/not-exist") == DEFAULT_PRICE
    assert get_price("does/not-exist").input == DEFAULT_PRICE.input


# --------------------------------------------------------------------------- #
# report: runs on empty + sample data without crashing (item e)                #
# --------------------------------------------------------------------------- #
def test_report_renders_empty():
    import report

    md = report.render_pair(CONFIG, "opus-4.8-vs-5.5", {}, [], score=False)
    assert "Gate 1 Scorecard" in md
    assert "No run data yet" in md


def test_report_renders_sample():
    import report

    runs = [
        {
            "case_id": "r3_oracle_to_postgres",
            "model_slug": "anthropic/claude-opus-4.8",
            "model_name": "Claude Opus 4.8",
            "role": "current",
            "ok": True,
            "input_tokens": 1000,
            "output_tokens": 200,
            "cache_read_tokens": 500,
            "cache_write_tokens": 50,
            "total_tokens": 1200,
            "latency_s": 3.0,
            "output_text": "",
        },
        {
            "case_id": "r3_oracle_to_postgres",
            "model_slug": "anthropic/claude-opus-5.5",
            "model_name": "Claude Opus 5.5",
            "role": "target",
            "ok": True,
            "input_tokens": 900,
            "output_tokens": 180,
            "cache_read_tokens": 480,
            "cache_write_tokens": 45,
            "total_tokens": 1080,
            "latency_s": 2.5,
            "output_text": "",
        },
    ]
    aggs = report.aggregate(runs, score=False)
    md = report.render_pair(CONFIG, "opus-4.8-vs-5.5", aggs, runs, score=False)
    assert "Raw token counts" in md
    assert "Normalized views" in md
    assert "Overall score" in md


# --------------------------------------------------------------------------- #
# report statistics / bookkeeping                                              #
# --------------------------------------------------------------------------- #
def test_wilson_and_fisher():
    import report

    lo, hi = report.wilson_ci(7, 12)
    assert 0.31 < lo < 0.33 and 0.80 < hi < 0.82
    assert report.wilson_ci(0, 0) == (0.0, 0.0)
    # 11/12 vs 7/12 — the pilot gap — is not significant
    assert abs(report.fisher_exact_p(11, 1, 7, 5) - 0.155) < 0.001
    assert report.fisher_exact_p(12, 0, 0, 12) < 1e-5


def test_infra_errors_excluded_and_per_case_counts():
    import report

    base = {"case_id": "r3_oracle_to_postgres", "model_slug": "m/a", "model_name": "A",
            "role": "current", "latency_s": 2.0, "output_tokens": 10, "output_text": ""}
    runs = [
        dict(base, ok=True),
        dict(base, ok=False, error="empty completion (finish_reason=length)"),
        dict(base, ok=False, error="RateLimitError: 429"),
    ]
    a = report.aggregate(runs, score=False)[("m/a", "current")]
    assert a.infra_errors == 1
    assert a.runs == 2 and a.passes == 1          # empty completion is a model FAIL
    assert a.case_results["r3_oracle_to_postgres"] == [1, 2]


def test_load_runs_uses_single_date(tmp_path, monkeypatch):
    import common

    d = tmp_path / "p"
    d.mkdir()
    for name in ("m.c.20261008.json", "m.c.20261008.r1.json", "m.c.20261009.json"):
        (d / name).write_text(json.dumps({"case_id": "c"}))
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    assert [r["_file"] for r in common.load_runs("p")] == ["m.c.20261009.json"]
    assert len(common.load_runs("p", date="20261008")) == 2
