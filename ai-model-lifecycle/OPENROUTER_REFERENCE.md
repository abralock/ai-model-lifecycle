# OpenRouter Reference — Model Availability, Timeline & Cost

> Status: **DRAFT — reference**
> Author: Ash 🏗️ (architect)
> Date: 2026-10-08
> Source: OpenRouter live catalog (`/api/v1/models`, 468 models), fetched 2026-10-08

This document captures the verified findings for running the **Gate 1 New Model Evaluation**
on OpenRouter: (1) confirmed model slugs, (2) development timeline, (3) cost prediction.

---

## 1. Model Availability — all 12 confirmed live on OpenRouter

Verified against the live catalog. The `4.8` / `5.5` / `Sol` / `Luna` / `Terra` version
strings are **real, current OpenRouter slugs** (not internal aliases).

| # | Current → Target | Current slug | Target slug | Status |
|---|---|---|---|---|
| 1 | Claude Opus 4.8 → 5.5 | `anthropic/claude-opus-4.8` | `anthropic/claude-opus-5.5` | ✅ live |
| 2 | Claude Sonnet 5 → 5.5 | `anthropic/claude-sonnet-5` | `anthropic/claude-sonnet-5.5` | ✅ live |
| 3 | Claude Sonnet 4.6 → 5.5 | `anthropic/claude-sonnet-4.6` | `anthropic/claude-sonnet-5.5` | ✅ live |
| 4 | Claude Haiku 4.5 → 5.5 | `anthropic/claude-haiku-4.5` | `anthropic/claude-haiku-5.5` | ✅ live |
| 5 | GPT-5.6 Sol → GPT-6 Sol | `openai/gpt-5.6-sol` | `openai/gpt-6-sol` | ✅ live |
| 6 | GPT-5.6 Luna → GPT-6 Luna | `openai/gpt-5.6-luna` | `openai/gpt-6-luna` | ✅ live |
| 7 | GPT-5.6 Terra → GPT-6 Terra | `openai/gpt-5.6-terra` | `openai/gpt-6-terra` | ✅ live |

### Notes
- Several models also have `-pro` and `:batch` variants. We use the **base slugs** above.
- Rows 2 and 3 ("Sonnet 5 → 5.5" and "Sonnet 4.6 → 5.5") are **two separate pairs** in the
  matrix — both are valid and independently runnable.
- The harness uses `litellm`, which accepts these OpenRouter IDs directly as `model=` strings.

---

## 2. Development Timeline

Assumes Phase 0 inputs (test artifacts) arrive without delays.

| Owner | Scope | Effort |
|---|---|---|
| **Pikachu** ⚡ | Harness (`litellm` runner), scorers, judge, report generator | 3–4 days |
| **Charmander** 🔥 | E2E validation + scoring-math checks + eval CI | 1–2 days |
| **Squirtle** 🐢 | Docker dev box + Postgres/Oracle/dashboard containers + secrets | 1–2 days |
| **Ash** 🏗️ | Architecture, review, baseline lock, final verification | ongoing (parallel) |

**Total: ~1 week (≈ 7–9 working days) to first live run** across all 7 pairs.
Full automation polish (CI auto re-run, dashboards) can follow incrementally.

---

## 3. Cost Prediction (OpenRouter)

> These are **estimates**, gated by two unknown inputs: (a) test-artifact token volume,
> (b) repeats per case. Refine once artifacts are available.

### Cost drivers
1. **Input token volume** — dominated by heavy cases: R4 (bulk-load "huge records") and
   C2 (100–200k token repo slice).
2. **Repeats per case** — temp=0 single run vs. 3× for variance. 3× triples cost.

### Estimate (per full matrix run — 7 pairs × 16 cases × 3 repeats)

| Component | Est. tokens | Est. cost |
|---|---|---|
| Input (heavy cases bind) | ~5–15M tokens | $3–15 |
| Output (code gen is verbose) | ~2–5M tokens | $2–10 |
| Cache (low hit on unique prompts) | minor | $1–3 |
| **Total per complete matrix run** | | **~$10–40** |

### Total budget recommendation
| Phase | Est. cost |
|---|---|
| Development + calibration + first live run | $50–150 |
| Steady state (per new-model release) | $10–40 |

**Recommendation:** top up **$100–200** for development + first run, with buffer.

> Note: Opus-tier models (`opus-4.8`/`5.5`) dominate cost — roughly 5–10× Haiku pricing.
> If budget-constrained: trim heavy cases or reduce repeats to 2×.

---

## 4. Refinement needed for an exact figure

To produce a precise (non-range) cost number, provide:
1. **Approx. size of test artifacts** — Boot module class count; R4 record count; C2 repo-slice size.
2. **Repeats per case** — 1× / 2× / 3×.
3. **Initial run scope** — all 12 models at once, or 7 "current" baselines first (cheaper baseline lock).
