"""pricing.py — hardcoded OpenRouter price table for the Gate 1 candidate models.

Prices are USD per 1,000,000 tokens (per-million), split into four buckets so the
report can price cache reads/writes correctly:

    input        — normal (uncached) prompt tokens
    output       — completion tokens
    cache_read   — prompt tokens served from the provider prompt-cache
    cache_write  — prompt tokens written to the provider prompt-cache

Source: OpenRouter model catalog (see OPENROUTER_REFERENCE.md). These are the
*base* slugs used by the harness (no :batch / -pro variants).

Runs made since billed-cost recording use OpenRouter's billed cost
(`billed_cost_usd` in each run file) instead; this table is the fallback for
older runs and for offline tests.

Keep this table tiny and explicit — it is deliberately not fetched at runtime so
scoring/reporting stays deterministic and offline-testable. Add a row per new
model when extending the matrix.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    """USD per 1,000,000 tokens for each usage bucket."""

    input: float
    output: float
    cache_read: float = 0.0
    cache_write: float = 0.0            # 5-minute cache write (the API default)
    cache_write_1h: float = 0.0         # 1-hour cache write (0: priced as cache_write)
    long_context_over: int = 0          # a prompt over this many tokens is priced at
    long_context_factor: float = 1.0    # every bucket x this factor (1: no long tier)


# USD per 1M tokens.
#
# The Claude 5.5 rows are Anthropic API list prices, checked 2026-11-06 against
# Claude Code's own `costUSD` (the `modelUsage` of every finished Claude Code
# session under runs/): with these rates the per-model cost is reproduced
# exactly for all 43 Opus 5.5 and 43 Sonnet 5.5 sessions, and for the Haiku 5.5
# sessions whose prompts stayed under 100K tokens (tests/test_pricing.py).
# * Claude Code writes the main model's prompt cache for 1 hour (2x input);
#   side calls use the 5-minute cache (1.25x input). Both are priced here.
# * Haiku 5.5 bills a request whose prompt is over 100K tokens at 5x every rate
#   ($0.50 / $2.50); its 60-minute agentic sessions are mostly such requests,
#   which the flat rate missed by 4-5x. Use usage_cost_usd() per request.
# The older rows keep the 5% read / 125% write convention, not published figures.
_OPUS_55 = Price(input=4.0, output=20.0, cache_read=0.20, cache_write=5.00, cache_write_1h=8.0)
_SONNET_55 = Price(input=2.0, output=10.0, cache_read=0.10, cache_write=2.50, cache_write_1h=4.0)
_HAIKU_55 = Price(input=0.10, output=0.50, cache_read=0.01, cache_write=0.125, cache_write_1h=0.20,
                  long_context_over=100_000, long_context_factor=5.0)
PRICES: dict[str, Price] = {
    "anthropic/claude-opus-4.8": Price(input=5.0, output=25.0, cache_read=0.25, cache_write=6.25),
    "anthropic/claude-opus-5.5": _OPUS_55,
    "anthropic/claude-sonnet-5": Price(input=2.0, output=10.0, cache_read=0.10, cache_write=2.50),
    "anthropic/claude-sonnet-5.5": _SONNET_55,
    "anthropic/claude-sonnet-4.6": Price(input=3.0, output=15.0, cache_read=0.30, cache_write=3.75),
    "anthropic/claude-haiku-4.5": Price(input=1.0, output=5.0, cache_read=0.10, cache_write=1.25),
    "anthropic/claude-haiku-5.5": _HAIKU_55,
    # The same models under the ids Claude Code reports (agentic runs).
    "claude-opus-5-5": _OPUS_55,
    "claude-sonnet-5-5": _SONNET_55,
    "claude-haiku-5-5": _HAIKU_55,
    # --- placeholders for the remaining matrix (adjust when enabled) ---
    "openai/gpt-5.6-sol": Price(input=5.0, output=20.0),
    "openai/gpt-6-sol": Price(input=5.0, output=20.0),
    "openai/gpt-5.6-luna": Price(input=2.0, output=8.0),
    "openai/gpt-6-luna": Price(input=2.0, output=8.0),
    "openai/gpt-5.6-terra": Price(input=2.0, output=8.0),
    "openai/gpt-6-terra": Price(input=2.0, output=8.0),
    # --- OpenCode Go models (models.yaml `apis: opencode-go`) -----------------
    # Go list prices (https://opencode.ai/v2/docs/console/go, checked
    # 2026-10-14), keyed by the bare Go model id. These count against the
    # subscription's monthly quota — they are not marginal billing, so the
    # cost axis of a Go pair reads "quota spend at list price". Go reports no
    # cache-write price ("-") -> 0.0.
    "glm-5.2": Price(input=1.40, output=4.40, cache_read=0.26, cache_write=0.0),
    "glm-5.3": Price(input=1.40, output=4.40, cache_read=0.26, cache_write=0.0),
    "glm-5.3-flash": Price(input=0.15, output=0.50, cache_read=0.03, cache_write=0.0),
    # DeepSeek off-peak prices below; peak hours (01:00-04:00 and 06:00-10:00
    # UTC, Mon-Fri) are billed 2x by Go and are not modeled here.
    "deepseek-v4.1-flash": Price(input=0.15, output=0.60, cache_read=0.003, cache_write=0.0),
    "deepseek-v4-pro": Price(input=0.66, output=1.98, cache_read=0.022, cache_write=0.0),
    # Other chat-completions models on Go, ready for future pairs:
    "kimi-k2.7-code": Price(input=0.95, output=4.00, cache_read=0.19, cache_write=0.0),
    "kimi-k3": Price(input=3.00, output=15.00, cache_read=0.30, cache_write=0.0),
    "longcat-2.0": Price(input=0.30, output=1.20, cache_read=0.006, cache_write=0.0),
    "mimo-v2.6-flash": Price(input=0.14, output=0.28, cache_read=0.0028, cache_write=0.0),
    "mimo-v2.6-pro": Price(input=0.435, output=0.87, cache_read=0.003625, cache_write=0.0),
    # GPT Luna on Go (Responses API only; api: opencode-go-responses). Go list
    # prices for the <=272K-context tier, checked 2026-10-15 on the Go docs
    # page; the >272K tier (2x input / 1.5x output) is not modeled — Gate 1
    # prompts stay well under 272K.
    "gpt-5.6-luna": Price(input=0.20, output=1.20, cache_read=0.02, cache_write=0.25),
    "gpt-6-luna": Price(input=0.10, output=0.50, cache_read=0.01, cache_write=0.125),
    # Qwen3.x on Go is Anthropic-messages only (family: messages via a
    # model-level override, keeping the opencode-go provider string).
    "qwen3.8-flash": Price(input=0.15, output=0.47, cache_read=0.016, cache_write=0.20),
}

# Fallback used when a model slug is not in the table. Keeps the report from
# crashing on an unknown model — it just prices conservatively and warns.
DEFAULT_PRICE = Price(input=3.0, output=15.0, cache_read=0.30, cache_write=3.75)


def get_price(model_id: str) -> Price:
    """Return the Price for `model_id`, falling back to DEFAULT_PRICE."""
    return PRICES.get(model_id, DEFAULT_PRICE)


def cost_usd(
    model_id: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Compute USD cost for a usage record against the model's price buckets."""
    p = get_price(model_id)
    return (
        input_tokens * p.input
        + output_tokens * p.output
        + cache_read_tokens * p.cache_read
        + cache_write_tokens * p.cache_write
    ) / 1_000_000.0


def usage_cost_usd(model_id: str, usage: dict) -> float:
    """USD cost of one API request from its Anthropic `usage` object.

    Splits cache writes into 5-minute and 1-hour (`usage.cache_creation`; when
    absent, all writes are 5-minute) and applies the model's long-context tier
    to the whole request when its prompt (fresh input + cache reads + cache
    writes) is over the threshold. Sum it per request: the tier is per request,
    so it cannot be applied to a session's totals.
    """
    p = get_price(model_id)
    fresh = int(usage.get("input_tokens") or 0)
    read = int(usage.get("cache_read_input_tokens") or 0)
    written = int(usage.get("cache_creation_input_tokens") or 0)
    split = usage.get("cache_creation") or {}
    w1h = int(split.get("ephemeral_1h_input_tokens") or 0) if split else 0
    w5m = int(split.get("ephemeral_5m_input_tokens") or 0) if split else written
    factor = (p.long_context_factor
              if p.long_context_over and fresh + read + written > p.long_context_over else 1.0)
    return factor * (
        fresh * p.input
        + int(usage.get("output_tokens") or 0) * p.output
        + read * p.cache_read
        + w5m * p.cache_write
        + w1h * (p.cache_write_1h or p.cache_write)
    ) / 1_000_000.0
