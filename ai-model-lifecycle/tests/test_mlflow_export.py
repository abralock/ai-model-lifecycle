"""tests/test_mlflow_export.py — optional MLflow export of Gate 1 results.

Offline: a throwaway SQLite MLflow store in tmp_path and a fake scorer, so no
server, Postgres or Maven is needed. Skipped when mlflow isn't installed
(it is optional: requirements-mlflow.txt).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

mlflow = pytest.importorskip("mlflow")      # conftest already leaves this file out without mlflow

import common  # noqa: E402
import mlflow_export  # noqa: E402
import report  # noqa: E402
from common import load_config  # noqa: E402

PAIR = "haiku-4.5-vs-5.5"
RID = "20261010T000000Z"


def _write_run(runs_dir, cfg, *, cases=None, rid=RID, thinking=False):
    pair = cfg.get_pair(PAIR)
    d = runs_dir / PAIR
    d.mkdir(parents=True, exist_ok=True)
    for role, m in (("current", pair.current), ("target", pair.target)):
        for case in cases or cfg.cases:
            rec = {"pair_id": PAIR, "case_id": case, "model_slug": m.id, "model_name": m.name,
                   "role": role, "rep": 0, "run_id": rid, "input_tokens": 100, "output_tokens": 50,
                   "cache_read_tokens": 0, "cache_write_tokens": 0, "total_tokens": 150,
                   "provider": "Amazon Bedrock", "billed_cost_usd": 0.01 if role == "current" else 0.002,
                   "latency_s": 10.0 if role == "current" else 20.0,
                   "output_text": f"answer {role} {case}", "ok": True, "error": None}
            if thinking:
                rec.update(reasoning_requested={"effort": "medium" if role == "current" else "low"},
                           reasoning_tokens=20 if role == "current" else 30,
                           thinking_time_s=4.0 if role == "current" else 8.0)
            (d / f"{m.id.replace('/', '__')}.{case}.{rid}.json").write_text(json.dumps(rec))


def _fake_scorer(calls):
    def score(case_id, output_text, slug):
        calls.append((case_id, output_text))
        bad = output_text.startswith("answer target") and case_id.startswith("r4")
        return SimpleNamespace(passed=not bad, reason="failed checks: index_scan" if bad else "ok")
    return score


@pytest.fixture
def env(tmp_path, monkeypatch):
    cfg = load_config()
    monkeypatch.chdir(tmp_path)                    # MLflow writes artifacts to ./mlruns
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(report, "score_case", report.score_case)       # restored after the test
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'mlflow.db'}")
    calls: list = []
    score = mlflow_export.ScoreCache(path=tmp_path / "cache.json", scorer=_fake_scorer(calls))
    yield SimpleNamespace(cfg=cfg, runs=tmp_path / "runs", score=score, calls=calls)
    mlflow.set_tracking_uri(None)


def _runs(level):
    exp = mlflow.get_experiment_by_name(f"Gate1 / {PAIR}")
    return mlflow.search_runs([exp.experiment_id], output_format="list",
                              filter_string=f"tags.level = '{level}'")


def test_export_logs_parent_and_one_child_per_call(env):
    _write_run(env.runs, env.cfg)
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "loaded"

    (parent,) = _runs("run")
    n_cases = len(env.cfg.cases)
    assert parent.data.tags["harness_run_id"] == RID
    assert parent.data.tags["cost_source"] == "billed"
    assert parent.data.tags["providers"] == "Amazon Bedrock"
    m = parent.data.metrics

    # one run per model, with the SAME metric names so MLflow charts compare them
    models = {r.data.tags["role"]: r for r in _runs("model")}
    assert set(models) == {"current", "target"}
    assert all(r.data.tags["mlflow.parentRunId"] == parent.info.run_id for r in models.values())
    cm, tm = models["current"].data.metrics, models["target"].data.metrics
    assert set(cm) == set(tm)
    assert cm["passes"] == n_cases and tm["passes"] == n_cases - 1
    assert cm["cost_usd"] == pytest.approx(0.01 * n_cases)
    assert tm["pass_rate_r4"] == 0.0 and cm["pass_rate_r4"] == 1.0
    assert models["current"].data.tags["mlflow.runColor"] == mlflow_export.CURRENT_COLOR
    assert models["target"].data.tags["mlflow.runColor"] == mlflow_export.TARGET_COLOR

    # the pair run carries current_X / target_X pairs for side-by-side charts
    assert m["current_passes"] == n_cases and m["target_passes"] == n_cases - 1
    assert m["current_cost_component"] == 100.0 and m["current_quality_component"] == 100.0
    assert {f"current_{k}" for k in cm} == {k for k in m if k.startswith("current_")}
    assert {f"target_{k}" for k in tm} == {k for k in m if k.startswith("target_")}

    # overall score is the same number report.py prints
    runs = common.load_runs(PAIR, run=RID)
    aggs = report.aggregate(runs, score=True)
    pair = env.cfg.get_pair(PAIR)
    ov = report.overall_score(aggs[(pair.current.id, "current")], aggs[(pair.target.id, "target")])
    assert m["overall_score"] == pytest.approx(ov.overall)
    assert parent.data.tags["verdict"] == ov.verdict
    assert m["target_cost_component"] == pytest.approx(ov.cost)
    assert tm["cost_component"] == pytest.approx(ov.cost) and cm["cost_component"] == 100.0

    children = _runs("call")
    assert len(children) == 2 * n_cases
    for c in children:                          # calls sit under their model's run
        assert c.data.tags["mlflow.parentRunId"] == models[c.data.params["role"]].info.run_id
    fails = [c for c in children if c.data.tags["result"] == "FAIL"]
    assert len(fails) == 1 and fails[0].data.params["case"].startswith("r4")
    assert fails[0].data.tags["failure_reason"] == "failed checks: index_scan"

    arts = {a.path for a in mlflow.MlflowClient().list_artifacts(parent.info.run_id)}
    assert {"REPORT.md", "calls.json", "comparison.png"} <= arts


def test_export_logs_thinking_time_and_reasoning_effort(env):
    _write_run(env.runs, env.cfg, thinking=True)
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "loaded"

    models = {r.data.tags["role"]: r for r in _runs("model")}
    assert models["current"].data.params["reasoning_effort"] == "medium"
    assert models["target"].data.params["reasoning_effort"] == "low"
    assert models["current"].data.metrics["mean_thinking_time_s"] == pytest.approx(4.0)
    assert models["target"].data.metrics["mean_thinking_time_s"] == pytest.approx(8.0)
    assert models["current"].data.metrics["reasoning_tokens"] == 20 * len(env.cfg.cases)
    assert models["target"].data.metrics["reasoning_tokens"] == 30 * len(env.cfg.cases)

    calls = _runs("call")
    assert {c.data.params["reasoning_effort"] for c in calls} == {"medium", "low"}
    for call in calls:
        expected = 4.0 if call.data.params["role"] == "current" else 8.0
        assert call.data.metrics["thinking_time_s"] == pytest.approx(expected)
        assert call.data.metrics["reasoning_tokens"] > 0


def test_export_is_idempotent_and_scores_each_answer_once(env):
    _write_run(env.runs, env.cfg)
    mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score)
    n = len(env.calls)
    assert n == 2 * len(env.cfg.cases)                     # cached across aggregate + children
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "exists"
    assert len(env.calls) == n
    assert len(_runs("run")) == 1
    # the same run from another source (e.g. a teammate) is a separate entry
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "teammate", env.score) == "loaded"
    assert len(env.calls) == n


def test_partial_run_is_not_exported(env):
    _write_run(env.runs, env.cfg, cases=env.cfg.cases[:1])
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "incomplete"
    assert mlflow.get_experiment_by_name(f"Gate1 / {PAIR}") is None


def test_repeat_number_from_field_or_legacy_filename():
    assert mlflow_export._rep({"rep": 2}) == 3
    assert mlflow_export._rep({"_file": "x.r1_springboot2to3.20261008.r2.json"}) == 3   # legacy: no rep field
    assert mlflow_export._rep({"_file": "x.r1_springboot2to3.20261008.json"}) == 1


def test_overall_score_none_when_a_model_passes_nothing():
    a = report.ModelAgg(model_slug="x", model_name="x", role="current")
    b = report.ModelAgg(model_slug="y", model_name="y", role="target", runs=4, passes=2)
    assert report.overall_score(a, b) is None


def test_real_suite_gets_its_own_experiment_and_report(env):
    real = load_config(suite="real")
    _write_run(env.runs, real)
    assert mlflow_export.export_run(mlflow, real, PAIR, RID, "local", env.score) == "loaded"
    assert mlflow.get_experiment_by_name(f"Gate1 / {PAIR}") is None      # sanity charts untouched
    exp = mlflow.get_experiment_by_name(f"Gate1 / {PAIR} · real")
    (parent,) = mlflow.search_runs([exp.experiment_id], output_format="list",
                                   filter_string="tags.level = 'run'")
    assert parent.data.tags["suite"] == "real"
    assert {"current_pass_rate_r1b", "current_pass_rate_r2"} <= set(parent.data.metrics)
    arts = {a.path for a in mlflow.MlflowClient().list_artifacts(parent.info.run_id)}
    assert "REPORT.real.md" in arts and "REPORT.md" not in arts
    # the same run id seen from the sanity suite is not one of its runs
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "incomplete"


def test_unverified_result_is_not_cached(tmp_path):
    calls: list = []

    def scorer(case_id, output_text, slug):
        calls.append(case_id)
        return SimpleNamespace(passed=False, reason="failed checks: build (unverified: missing cache)")

    cache = mlflow_export.ScoreCache(path=tmp_path / "cache.json", scorer=scorer)
    assert cache("r2_gwt_to_angular", "answer", "m").passed is False
    cache("r2_gwt_to_angular", "answer", "m")
    assert len(calls) == 2 and not (tmp_path / "cache.json").exists()


def test_a_changed_hidden_test_invalidates_cached_verdicts(tmp_path, monkeypatch):
    """Hidden test fixtures decide a verdict as much as scorer code does, so
    they are part of the cache key (fixed 2026-10-31: r1b's forwarding test)."""
    import score_cache
    (tmp_path / "scorers" / "fixtures").mkdir(parents=True)
    (tmp_path / "scorers" / "r1b_scorer.py").write_text("x = 1\n")
    test = tmp_path / "scorers" / "fixtures" / "ClientForwardControllerTest.java"
    test.write_text("class A {}")
    monkeypatch.setattr(score_cache, "HARNESS_DIR", tmp_path)
    before = score_cache._scorer_fingerprint()
    test.write_text("class B {}")
    assert score_cache._scorer_fingerprint() != before


# --------------------------------------------------------------------------- #
# descriptive timing metrics (docs/METRICS_PLAN.md)                            #
# --------------------------------------------------------------------------- #
def _timed_rec(*, ok=True, latency=10.0, thinking=None, execution=None):
    rec = {"case_id": "r3_oracle_to_postgres", "role": "target", "model_slug": "m",
           "model_name": "m", "ok": ok, "error": None if ok else "empty completion",
           "input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0,
           "cache_write_tokens": 0, "total_tokens": 2, "latency_s": latency,
           "output_text": "x", "billed_cost_usd": None, "provider": "opencode-go"}
    if thinking is not None:
        rec["thinking_time_s"] = thinking
    if execution is not None:
        rec["execution_time_s"] = execution
    return rec


def test_model_metrics_exports_descriptive_timing_fields():
    a = report.aggregate([_timed_rec(latency=10.0, thinking=4.0, execution=2.0),
                          _timed_rec(ok=False, latency=99.0)],
                         score=False)[("m", "target")]
    m = mlflow_export.model_metrics(a, None, budgets=[30, 60])
    assert m["mean_ttfs_s"] == pytest.approx(10.0)
    assert m["pass_at_30s"] == pytest.approx(0.5)
    assert m["pass_at_60s"] == pytest.approx(0.5)
    assert m["execution_thinking_time_ratio"] == pytest.approx(0.5)
    assert m["paired_timing_runs"] == 1


def test_model_metrics_omits_unavailable_timing_fields():
    """Missing measurements are omitted, never logged as zero."""
    a = report.aggregate([_timed_rec(ok=False, latency=5.0)], score=False)[("m", "target")]
    m = mlflow_export.model_metrics(a, None, budgets=[30])
    assert "mean_ttfs_s" not in m                      # no pass -> no TTFS
    assert "execution_thinking_time_ratio" not in m    # no paired timing
    assert m["pass_at_30s"] == 0.0                     # a true zero, not missing


def test_role_reasoning_effort_handles_empty_and_mixed():
    runs = [{"role": "current", "reasoning_requested": {"effort": "low"}},
            {"role": "current", "reasoning_requested": {"effort": "low"}}]
    assert mlflow_export._role_reasoning_effort(runs, "current") == "low"
    assert mlflow_export._role_reasoning_effort(runs, "target") == "not recorded"
    runs.append({"role": "current", "reasoning_requested": {"effort": "high"}})
    assert mlflow_export._role_reasoning_effort(runs, "current") == "mixed"


def test_call_timing_guard_rejects_bool():
    """report.py's aggregate excludes bool thinking_time_s; the export must
    agree with the scorecard on the same record."""
    assert mlflow_export._timing(4.0) == 4.0
    assert mlflow_export._timing(True) is None
    assert mlflow_export._timing(None) is None
    assert mlflow_export._timing("3") is None
