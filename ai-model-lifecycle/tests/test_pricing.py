"""tests/test_pricing.py — the Claude 5.5 API prices in pricing.py.

Claude Code reports each finished session's cost per model (`modelUsage`,
`costUSD`, at list prices). The price table must reproduce it, so that a
session stopped at the time limit, which Claude Code never prices, can be
priced from its session record on the same basis.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import agentic
import pricing

RUNS = Path(__file__).resolve().parent.parent / "runs"


def _model_usage_as_request(mu: dict) -> dict:
    """A `modelUsage` entry in the shape of one request's `usage`."""
    return {"input_tokens": mu["inputTokens"], "output_tokens": mu["outputTokens"],
            "cache_read_input_tokens": mu["cacheReadInputTokens"],
            "cache_creation_input_tokens": mu["cacheCreationInputTokens"],
            "cache_creation": {
                "ephemeral_5m_input_tokens": mu.get("cacheCreationEphemeral5mInputTokens", 0),
                "ephemeral_1h_input_tokens": mu.get("cacheCreationEphemeral1hInputTokens", 0)}}


def test_opus_high_10min_matches_claude_code():
    # r1b 10-min run 2, Opus 5.5 high (20261105T154938Z): Claude Code's figure
    # for the Opus part of the session, with 1-hour cache writes.
    mu = {"inputTokens": 88, "outputTokens": 17992, "cacheReadInputTokens": 1892430,
          "cacheCreationInputTokens": 48771, "cacheCreationEphemeral1hInputTokens": 48771}
    assert pricing.usage_cost_usd("claude-opus-5-5", _model_usage_as_request(mu)) \
        == pytest.approx(1.128846, abs=1e-6)


def test_haiku_side_calls_match_claude_code():
    # The same session's Haiku side calls: 5-minute cache writes, short prompts.
    mu = {"inputTokens": 8, "outputTokens": 1256, "cacheReadInputTokens": 872,
          "cacheCreationInputTokens": 92237, "cacheCreationEphemeral5mInputTokens": 92237}
    # Priced as one request this would cross 100K, so price it unsplit at base rates.
    p = pricing.get_price("claude-haiku-5-5")
    base = (8 * p.input + 1256 * p.output + 872 * p.cache_read + 92237 * p.cache_write) / 1e6
    assert base == pytest.approx(0.012167145, abs=1e-6)


def test_haiku_long_context_tier_is_per_request():
    short = {"input_tokens": 10, "cache_read_input_tokens": 90_000, "output_tokens": 1000}
    long = {"input_tokens": 10, "cache_read_input_tokens": 110_000, "output_tokens": 1000}
    cost = pricing.usage_cost_usd
    assert cost("claude-haiku-5-5", short) == pytest.approx((10 * 0.10 + 90_000 * 0.01 + 1000 * 0.50) / 1e6)
    assert cost("claude-haiku-5-5", long) == pytest.approx(5 * (10 * 0.10 + 110_000 * 0.01 + 1000 * 0.50) / 1e6)
    # Opus and Sonnet have no long-context tier
    assert cost("claude-opus-5-5", long) == pytest.approx((10 * 4 + 110_000 * 0.20 + 1000 * 20) / 1e6)


def test_cache_writes_without_split_are_5_minute():
    usage = {"cache_creation_input_tokens": 1_000_000}
    assert pricing.usage_cost_usd("claude-sonnet-5-5", usage) == pytest.approx(2.50)
    usage["cache_creation"] = {"ephemeral_1h_input_tokens": 1_000_000, "ephemeral_5m_input_tokens": 0}
    assert pricing.usage_cost_usd("claude-sonnet-5-5", usage) == pytest.approx(4.00)


def _finished_sessions():
    for path in sorted(RUNS.glob("*/agentic/*/*.stream.jsonl")):
        result = None
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(ev, dict) and ev.get("type") == "result" and ev.get("modelUsage"):
                result = ev
        if result:
            yield path, result["modelUsage"]


def test_table_reproduces_every_finished_opus_and_sonnet_session():
    """Totals are exact for Opus and Sonnet (no long-context tier). Haiku's
    totals cannot be checked this way: its tier is per request."""
    checked = 0
    for path, usage in _finished_sessions():
        for model, mu in usage.items():
            if model not in ("claude-opus-5-5", "claude-sonnet-5-5"):
                continue
            mine = pricing.usage_cost_usd(model, _model_usage_as_request(mu))
            assert mine == pytest.approx(mu["costUSD"], rel=1e-4, abs=1e-6), (path.name, model)
            checked += 1
    if checked == 0:
        pytest.skip("no finished Claude Code sessions under runs/")


def _reply(mid: str, model: str, output: int, **usage) -> str:
    return json.dumps({"type": "assistant", "message": {
        "id": mid, "model": model, "usage": {"output_tokens": output, **usage}}}) + "\n"


def test_session_cost_prices_each_reply_once_at_its_final_output():
    lines = [
        _reply("a", "claude-sonnet-5-5", 5, input_tokens=2, cache_read_input_tokens=10_000,
               cache_creation_input_tokens=1000,
               cache_creation={"ephemeral_1h_input_tokens": 1000, "ephemeral_5m_input_tokens": 0}),
        _reply("a", "claude-sonnet-5-5", 400, input_tokens=2, cache_read_input_tokens=10_000,
               cache_creation_input_tokens=1000,
               cache_creation={"ephemeral_1h_input_tokens": 1000, "ephemeral_5m_input_tokens": 0}),
        _reply("b", "<synthetic>", 0),
        "not json\n",
    ]
    expected = (2 * 2 + 400 * 10 + 10_000 * 0.10 + 1000 * 4) / 1e6
    assert agentic.session_cost_usd(lines) == pytest.approx(expected)
    assert agentic.session_output_tokens(lines) == 400


def test_session_cost_unknown_model_or_empty_is_none():
    assert agentic.session_cost_usd([]) is None
    assert agentic.session_cost_usd([_reply("a", "claude-unknown-9", 10, input_tokens=5)]) is None
