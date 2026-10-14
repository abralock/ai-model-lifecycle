"""tests/test_go_gateway.py — non-OpenRouter gateways (OpenCode Go).

Models with `api: <name>` in models.yaml are called through that gateway (an
OpenAI-compatible chat-completions API, e.g. OpenCode Go) instead of
OpenRouter: no provider pinning, no usage.cost request, the gateway id is
recorded as the provider, and cost comes from the pricing.py table (Go's list
prices count against the subscription quota; it does not bill per call).

All offline: litellm is replaced by a fake.
"""

from __future__ import annotations

import json
import sys
import types

import pytest

import common
import pricing
import report
import runner
from common import load_config

PAIR = "glm-5.2-vs-5.3"


# --------------------------------------------------------------------------- #
# config                                                                       #
# --------------------------------------------------------------------------- #
GO_YAML = """
pairs:
  - id: g
    current: {id: glm-5.2, name: GLM-5.2, api: opencode-go, params: {reasoning_effort: low}}
    target:  {id: glm-5.3, name: GLM-5.3, api: opencode-go, params: {reasoning_effort: low}}
  - id: o
    current: {id: x/a1, name: A1}
    target:  {id: x/a2, name: A2}
apis:
  opencode-go:
    base_url: https://opencode.ai/inference/go/v1
    api_key_env: OPENCODE_GO_API_KEY
    family: chat
"""


def _cfg(tmp_path, yaml_text=GO_YAML):
    p = tmp_path / "models.yaml"
    p.write_text(yaml_text)
    return load_config(p)


def test_config_parses_apis_and_model_api(tmp_path):
    cfg = _cfg(tmp_path)
    pair = cfg.get_pair("g")
    api = cfg.api_for(pair.target)
    assert api is not None
    assert api.id == "opencode-go"
    assert api.base_url == "https://opencode.ai/inference/go/v1"
    assert api.family == "chat"
    assert pair.target.params == {"reasoning_effort": "low"}
    # models without `api:` stay on the OpenRouter route
    assert cfg.api_for(cfg.get_pair("o").target) is None


def test_dangling_api_reference_fails_loudly(tmp_path):
    cfg = _cfg(tmp_path, GO_YAML.replace("api: opencode-go,", "api: nope,"))
    with pytest.raises(KeyError, match="unknown api 'nope'"):
        cfg.api_for(cfg.get_pair("g").target)


def test_repo_go_pairs_resolve_and_are_priced():
    """Every `api:` model in the repo models.yaml must resolve its gateway and
    have a real pricing row (not the conservative DEFAULT_PRICE fallback)."""
    cfg = load_config()
    go_pairs = [p for p in cfg.pairs if p.current.api or p.target.api]
    assert go_pairs, "expected at least one OpenCode Go pair in models.yaml"
    for pair in go_pairs:
        for m in (pair.current, pair.target):
            assert m.api, f"{pair.id}: both models must use the same gateway"
            api = cfg.api_for(m)
            assert api is not None and api.base_url and api.api_key_env
            assert pricing.get_price(m.id) is not pricing.DEFAULT_PRICE, m.id


# --------------------------------------------------------------------------- #
# the call                                                                     #
# --------------------------------------------------------------------------- #
class _FakeLitellm(types.SimpleNamespace):
    def __init__(self):
        super().__init__(drop_params=False, calls=[])

    def completion(self, **kw):
        self.calls.append(kw)
        msg = types.SimpleNamespace(content="### FILE: x.sql\n```sql\nSELECT 1;\n```\n")
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=msg, finish_reason="stop")],
            usage=usage)


@pytest.fixture
def fake_litellm(monkeypatch):
    fake = _FakeLitellm()
    monkeypatch.setitem(sys.modules, "litellm", fake)
    monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-go-test")
    monkeypatch.delenv("OPENROUTER_TOKEN", raising=False)
    return fake


def test_go_call_uses_openai_compatible_route(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261014T000000Z")

    sent = fake_litellm.calls[0]
    assert sent["model"] == "openai/glm-5.3"
    assert sent["api_base"] == "https://opencode.ai/inference/go/v1"
    assert sent["api_key"] == "sk-go-test"
    # Go asks clients to identify themselves and send a stable session id
    assert sent["extra_headers"]["User-Agent"]
    assert sent["extra_headers"]["x-opencode-session"] == "20261014T000000Z"
    # OpenRouter extensions are not sent to other gateways
    assert "extra_body" not in sent
    # per-model params from models.yaml are merged into the call (GLM on Go is
    # thinking-only; reasoning_effort: low keeps it from thinking away the
    # whole output budget)
    assert sent["reasoning_effort"] == "low"

    assert res.ok and res.provider == "opencode-go"
    assert res.provider_requested is None
    assert res.billed_cost_usd is None
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["provider"] == "opencode-go" and saved["ok"] is True


def test_go_call_without_key_is_clean_infra_error(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.delenv("OPENCODE_GO_API_KEY")
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, "r3_oracle_to_postgres", pair.target, "target",
                          run_id="20261014T000000Z")
    assert not res.ok and "OPENCODE_GO_API_KEY not set" in (res.error or "")
    assert not fake_litellm.calls                       # never hit the network
    assert report.is_infra_error({"ok": res.ok, "error": res.error})


def test_go_dry_run_needs_no_key(tmp_path, monkeypatch, fake_litellm):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.delenv("OPENCODE_GO_API_KEY")
    cfg = load_config()
    results = runner.run_pair(cfg, PAIR, dry_run=True, run_id="20261014T000000Z")
    assert results and all(r.ok for r in results)       # payload shapes built fine
    assert not fake_litellm.calls                       # never hit the network
    assert not list(tmp_path.rglob("*.json"))           # a dry run writes nothing


def test_deepseek_style_cache_tokens_are_counted():
    resp = types.SimpleNamespace(usage={
        "prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150,
        "prompt_cache_hit_tokens": 80,
    })
    i, o, cr, cw, tot = runner._extract_usage(resp)
    assert (i, o, cr, cw, tot) == (100, 50, 80, 0, 150)


# --------------------------------------------------------------------------- #
# report                                                                       #
# --------------------------------------------------------------------------- #
def _rec(role, slug, ok=True, latency=10.0):
    return {"case_id": "r3_oracle_to_postgres", "role": role, "model_slug": slug,
            "model_name": slug, "ok": ok, "input_tokens": 1000, "output_tokens": 500,
            "cache_read_tokens": 0, "cache_write_tokens": 0, "total_tokens": 1500,
            "latency_s": latency, "output_text": "", "billed_cost_usd": None,
            "provider": "opencode-go", "error": None if ok else "empty completion"}


def test_report_scores_go_pair_like_any_other():
    """Same metrics, same methodology: pass rates, time, cost (price table),
    capped components, overall score — only the cost source line differs."""
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [_rec("current", pair.current.id), _rec("target", pair.target.id, latency=8.0)]
    aggs = report.aggregate(runs, score=False)
    md = report.render_pair(cfg, PAIR, aggs, runs, score=False)

    expected = pricing.cost_usd("glm-5.3", 1000, 500, 0, 0)
    assert aggs[(pair.target.id, "target")].cost_usd == pytest.approx(expected)
    assert "price table (pricing.py)" in md
    assert "opencode-go" in md and "different providers" not in md
    # both models pass -> an overall score is produced with the standard weights
    assert "Overall score (current = 100 baseline)" in md
    ov = report.overall_score(aggs[(pair.current.id, "current")],
                              aggs[(pair.target.id, "target")])
    assert ov is not None and ov.quality == 100.0 and ov.time == pytest.approx(125.0)
