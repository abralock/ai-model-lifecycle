"""tests/test_cross_gateway.py — closed-weight vs open-weight pairs across gateways.

A cross-gateway pair runs its current model through one gateway (Claude Code on
the claude.ai subscription) and its target through another (OpenCode Go). The
mechanism is per-model `api:` in models.yaml — already supported — so these
tests pin down the pieces that must stay honest:

1. The repo config ships the cross-gateway pairs with the right routing.
2. The Claude Code preflight still runs when only ONE side is claude-code.
3. The scorecard explains the pair instead of telling the user to "pin one
   provider" (that advice is wrong here: the routes differ by design).
4. The price-reference table never prints the DEFAULT_PRICE fallback for the
   Claude Code side (its cost is the CLI's estimate, not pricing.py).

All offline: no network, no `claude` binary.
"""

from __future__ import annotations

import pytest

import report
import runner
from common import load_config
from pricing import DEFAULT_PRICE, get_price

PAIR = "opus-5.5-cc-vs-glm-5.3"


# --------------------------------------------------------------------------- #
# 1. repo config                                                               #
# --------------------------------------------------------------------------- #
def test_repo_config_cross_gateway_pairs():
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    cur_api, tgt_api = cfg.api_for(pair.current), cfg.api_for(pair.target)
    assert cur_api is not None and cur_api.family == "claude-code"
    assert tgt_api is not None and tgt_api.id == "opencode-go" and tgt_api.family == "chat"
    # GLM-5.x on Go is thinking-only; without the cap it burns the output budget.
    assert (pair.target.params or {}).get("reasoning_effort") == "low"
    # The open-weight side must have a real pricing row (its cost source).
    assert get_price(pair.target.id) is not DEFAULT_PRICE


def test_repo_config_cross_gateway_deepseek_pair():
    cfg = load_config()
    pair = cfg.get_pair("sonnet-5.5-cc-vs-deepseek-v4-pro")
    assert cfg.api_for(pair.current).family == "claude-code"
    # DeepSeek on Go speaks the default chat dialect, no thinking params.
    tgt_api = cfg.api_for(pair.target)
    assert tgt_api.id == "opencode-go" and tgt_api.family == "chat"
    assert pair.target.params is None
    assert get_price(pair.target.id) is not DEFAULT_PRICE


def test_repo_config_cross_gateway_qwen_pair():
    cfg = load_config()
    pair = cfg.get_pair("opus-5.5-cc-vs-qwen3.8-flash")
    assert cfg.api_for(pair.current).family == "claude-code"
    # Qwen on Go only speaks the Anthropic messages dialect.
    tgt_api = cfg.api_for(pair.target)
    assert tgt_api.id == "opencode-go" and tgt_api.family == "messages"
    # No thinking params (Qwen ignores them all); slow calls need the floor.
    assert pair.target.params is None
    assert cfg.timeout_s_for(pair.id) >= 1200
    assert get_price(pair.target.id) is not DEFAULT_PRICE


# --------------------------------------------------------------------------- #
# 2. preflight fires on a half-claude-code pair                                #
# --------------------------------------------------------------------------- #
def test_preflight_runs_when_only_current_is_claude_code(monkeypatch):
    called = []

    def fake_preflight():
        called.append(True)
        raise runner.ClaudeCodeNotReady("not logged in (test)")

    monkeypatch.setattr(runner, "claude_code_preflight", fake_preflight)
    cfg = load_config()
    with pytest.raises(runner.ClaudeCodeNotReady):
        runner.run_pair(cfg, PAIR, case="r3_oracle_to_postgres", run_id="20261023T000000Z")
    assert called  # checked before any call was attempted


# --------------------------------------------------------------------------- #
# 3 + 4. the scorecard                                                         #
# --------------------------------------------------------------------------- #
def _rec(role, slug, name, provider, estimate=None, latency=10.0):
    return {"case_id": "r3_oracle_to_postgres", "role": role, "model_slug": slug,
            "model_name": name, "ok": True, "input_tokens": 1000, "output_tokens": 1000,
            "cache_read_tokens": 0, "cache_write_tokens": 0, "total_tokens": 2000,
            "latency_s": latency, "output_text": "", "billed_cost_usd": None,
            "cost_estimate_usd": estimate, "provider": provider, "error": None}


def _cross_md():
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [_rec("current", pair.current.id, pair.current.name, "claude-code", estimate=0.09),
            _rec("target", pair.target.id, pair.target.name, "opencode-go")]
    return report.render_pair(cfg, PAIR, report.aggregate(runs, score=False), runs, score=False)


def test_cross_gateway_note_replaces_provider_warning():
    md = _cross_md()
    assert "Cross-gateway pair" in md
    assert "claude-code" in md and "opencode-go" in md
    # The pin-one-provider advice is wrong for this pair and must not appear.
    assert "different providers" not in md
    # Each side keeps its own honest cost label.
    assert "Claude Code estimate at API prices (1/1)" in md
    assert "price table (pricing.py)" in md


def test_same_gateway_pairs_keep_the_provider_warning():
    # The warning logic for ordinary pairs is untouched: same-config-gateway
    # models served by different providers still warn.
    cfg = load_config()
    pair = cfg.get_pair("haiku-4.5-vs-5.5")
    runs = [_rec("current", pair.current.id, pair.current.name, "Amazon Bedrock"),
            _rec("target", pair.target.id, pair.target.name, "Claude Platform on AWS")]
    md = report.render_pair(cfg, "haiku-4.5-vs-5.5", report.aggregate(runs, score=False),
                            runs, score=False)
    assert "different providers" in md
    assert "Cross-gateway pair" not in md


def test_price_reference_skips_the_claude_code_side():
    md = _cross_md()
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    # The open-weight model's list price is shown; the Claude Code model has no
    # pricing.py row (cost is the CLI's estimate) so no DEFAULT_PRICE row for it.
    price = get_price(pair.target.id)
    assert f"| {pair.target.name} | {price.input} |" in md
    assert f"| {pair.current.name} | {DEFAULT_PRICE.input} |" not in md
