"""tests/test_provider_and_cost.py — provider pinning, billed cost, capped score.

1. Provider pinning: OpenRouter routes each request to some provider (Amazon
   Bedrock, Claude Platform on AWS, Azure, ...). Comparing two models served by
   different providers measures the providers' speed, not the models'. The
   harness pins a provider (default from models.yaml, overridable per pair) and
   sends it on every call with fallbacks off.
2. Recorded provider: each run file stores the provider OpenRouter actually used.
3. Billed cost: each run file stores what OpenRouter billed (usage.cost); the
   report uses it instead of the hand-typed price table whenever present.
4. Capped score: cost and time components are clamped, and a target with a lower
   pass rate is never reported as "target >= baseline".

All offline: litellm is replaced by a fake.
"""

from __future__ import annotations

import json
import sys
import types

import pytest

import common
import report
import runner
from common import load_config

PAIR = "haiku-4.5-vs-5.5"


# --------------------------------------------------------------------------- #
# 1. provider preferences from models.yaml                                     #
# --------------------------------------------------------------------------- #
def _cfg(tmp_path, yaml_text):
    p = tmp_path / "models.yaml"
    p.write_text(yaml_text)
    return load_config(p)


PAIRS_YAML = """
pairs:
  - id: a
    current: {id: x/a1, name: A1}
    target:  {id: x/a2, name: A2}
  - id: b
    current: {id: x/b1, name: B1}
    target:  {id: x/b2, name: B2}
    provider: {order: [OpenAI], allow_fallbacks: false}
  - id: c
    current: {id: x/c1, name: C1}
    target:  {id: x/c2, name: C2}
    provider: null
defaults:
  provider: {order: [Amazon Bedrock], allow_fallbacks: false}
"""


def test_provider_default_override_and_disable(tmp_path):
    cfg = _cfg(tmp_path, PAIRS_YAML)
    assert cfg.provider_for("a") == {"order": ["Amazon Bedrock"], "allow_fallbacks": False}
    assert cfg.provider_for("b") == {"order": ["OpenAI"], "allow_fallbacks": False}
    assert cfg.provider_for("c") is None          # explicit null = let OpenRouter route


def test_repo_config_pins_claude_pairs_to_one_provider():
    cfg = load_config()
    for pair in cfg.pairs:
        if pair.current.id.startswith("anthropic/"):
            prefs = cfg.provider_for(pair.id)
            assert prefs and len(prefs["order"]) == 1 and prefs["allow_fallbacks"] is False


# --------------------------------------------------------------------------- #
# 2 + 3. the call sends the pin, records provider and billed cost              #
# --------------------------------------------------------------------------- #
class _FakeLitellm(types.SimpleNamespace):
    def __init__(self, provider="Amazon Bedrock", cost=0.0123):
        super().__init__(drop_params=False, calls=[])
        self._provider, self._cost = provider, cost

    def completion(self, **kw):
        self.calls.append(kw)
        msg = types.SimpleNamespace(content="### FILE: x.sql\n```sql\nSELECT 1;\n```\n")
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150, "cost": self._cost}
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=msg, finish_reason="stop")],
            usage=usage, provider=self._provider)


@pytest.fixture
def fake_litellm(monkeypatch):
    fake = _FakeLitellm()
    monkeypatch.setitem(sys.modules, "litellm", fake)
    monkeypatch.setenv("OPENROUTER_TOKEN", "sk-or-v1-test")
    return fake


def test_call_sends_provider_pin_and_records_provider_and_cost(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target", run_id="20261009T000000Z")

    sent = fake_litellm.calls[0]["extra_body"]
    assert sent["provider"] == cfg.provider_for(PAIR)
    assert sent["usage"] == {"include": True}
    assert res.provider == "Amazon Bedrock"
    assert res.billed_cost_usd == pytest.approx(0.0123)
    assert res.provider_requested == cfg.provider_for(PAIR)

    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["provider"] == "Amazon Bedrock" and saved["billed_cost_usd"] == pytest.approx(0.0123)


def test_unpinned_pair_sends_no_provider(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    monkeypatch.setattr(cfg, "provider_for", lambda pair_id: None)
    pair = cfg.get_pair(PAIR)
    runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target", run_id="20261009T000000Z")
    assert "provider" not in fake_litellm.calls[0]["extra_body"]


# --------------------------------------------------------------------------- #
# report: billed cost, provider display, capped score                          #
# --------------------------------------------------------------------------- #
def _rec(role, slug, ok=True, billed=None, provider="Amazon Bedrock", latency=10.0, out=1000):
    return {"case_id": "r3_oracle_to_postgres", "role": role, "model_slug": slug,
            "model_name": slug, "ok": ok, "input_tokens": 1000, "output_tokens": out,
            "cache_read_tokens": 0, "cache_write_tokens": 0, "total_tokens": 1000 + out,
            "latency_s": latency, "output_text": "", "billed_cost_usd": billed, "provider": provider,
            # a failed ANSWER (scored as FAIL), not an infra error (excluded)
            "error": None if ok else "empty completion (finish_reason=length)"}


def test_report_prefers_billed_cost_over_price_table():
    runs = [_rec("current", "anthropic/claude-haiku-4.5", billed=0.5),
            _rec("current", "anthropic/claude-haiku-4.5", billed=None)]
    a = report.aggregate(runs, score=False)[("anthropic/claude-haiku-4.5", "current")]
    table = report.cost_usd("anthropic/claude-haiku-4.5", 1000, 1000, 0, 0)
    assert a.cost_usd == pytest.approx(0.5 + table)
    assert a.billed_runs == 1


def test_report_flags_different_providers():
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [_rec("current", pair.current.id, billed=0.01, provider="Amazon Bedrock"),
            _rec("target", pair.target.id, billed=0.01, provider="Claude Platform on AWS")]
    md = report.render_pair(cfg, PAIR, report.aggregate(runs, score=False), runs, score=False)
    assert "Amazon Bedrock" in md and "Claude Platform on AWS" in md
    assert "different providers" in md


def test_same_provider_no_warning():
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [_rec("current", pair.current.id, billed=0.01), _rec("target", pair.target.id, billed=0.01)]
    md = report.render_pair(cfg, PAIR, report.aggregate(runs, score=False), runs, score=False)
    assert "different providers" not in md
    assert "billed by OpenRouter" in md


def test_cost_and_time_components_are_capped():
    assert report.component(1.0, 0.01) == report.COMPONENT_MAX     # 100x cheaper -> capped
    assert report.component(1.0, 100.0) == report.COMPONENT_MIN    # 100x dearer -> floored
    assert report.component(1.0, 2.0) == pytest.approx(50.0)
    assert report.component(2.0, 1.0) == pytest.approx(150.0)
    assert report.component(1.0, 0.0) == 100.0                       # no data -> neutral


def test_cheaper_target_with_lower_quality_is_not_an_upgrade():
    """The Haiku case: 4x cheaper but fewer passes must not read as target >= baseline."""
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = ([_rec("current", pair.current.id, ok=True, billed=0.04)] * 3
            + [_rec("current", pair.current.id, ok=False, billed=0.04)]
            + [_rec("target", pair.target.id, ok=True, billed=0.01)] * 2
            + [_rec("target", pair.target.id, ok=False, billed=0.01)] * 2)
    md = report.render_pair(cfg, PAIR, report.aggregate(runs, score=False), runs, score=False)
    assert "target ≥ baseline ✅" not in md
    assert "lower pass rate" in md


def test_price_table_matches_openrouter_list_prices():
    """Checked 2026-10-09; previously placeholders (Sonnet 5/5.5 1.5x, Haiku 5.5 10x too high)."""
    from pricing import get_price

    for slug, (i, o) in {
        "anthropic/claude-sonnet-5": (2.0, 10.0), "anthropic/claude-sonnet-5.5": (2.0, 10.0),
        "anthropic/claude-sonnet-4.6": (3.0, 15.0), "anthropic/claude-haiku-4.5": (1.0, 5.0),
        "anthropic/claude-haiku-5.5": (0.10, 0.50),
    }.items():
        p = get_price(slug)
        assert (p.input, p.output) == (i, o), slug
