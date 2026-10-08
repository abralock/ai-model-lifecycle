"""pricing.py — hardcoded OpenRouter price table for the Gate 1 candidate models.

Prices are USD per 1,000,000 tokens (per-million), split into four buckets so the
report can price cache reads/writes correctly:

    input        — normal (uncached) prompt tokens
    output       — completion tokens
    cache_read   — prompt tokens served from the provider prompt-cache
    cache_write  — prompt tokens written to the provider prompt-cache

Source: OpenRouter model catalog (see OPENROUTER_REFERENCE.md). These are the
*base* slugs used by the harness (no :batch / -pro variants).

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
    cache_write: float = 0.0


# USD per 1M tokens. Anthropic prompt-cache reads are ~10% of input price, writes
# ~125% of input price — reflected below.
PRICES: dict[str, Price] = {
    "anthropic/claude-opus-4.8": Price(input=15.0, output=75.0, cache_read=1.50, cache_write=18.75),
    "anthropic/claude-opus-5.5": Price(input=15.0, output=75.0, cache_read=1.50, cache_write=18.75),
    # --- placeholders for the remaining matrix (adjust when enabled) ---
    "anthropic/claude-sonnet-5": Price(input=3.0, output=15.0, cache_read=0.30, cache_write=3.75),
    "anthropic/claude-sonnet-5.5": Price(input=3.0, output=15.0, cache_read=0.30, cache_write=3.75),
    "anthropic/claude-sonnet-4.6": Price(input=3.0, output=15.0, cache_read=0.30, cache_write=3.75),
    "anthropic/claude-haiku-4.5": Price(input=1.0, output=5.0, cache_read=0.10, cache_write=1.25),
    "anthropic/claude-haiku-5.5": Price(input=1.0, output=5.0, cache_read=0.10, cache_write=1.25),
    "openai/gpt-5.6-sol": Price(input=5.0, output=20.0),
    "openai/gpt-6-sol": Price(input=5.0, output=20.0),
    "openai/gpt-5.6-luna": Price(input=2.0, output=8.0),
    "openai/gpt-6-luna": Price(input=2.0, output=8.0),
    "openai/gpt-5.6-terra": Price(input=2.0, output=8.0),
    "openai/gpt-6-terra": Price(input=2.0, output=8.0),
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
