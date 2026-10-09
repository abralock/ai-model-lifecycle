# Gate 1 Scorecard — sonnet-5-vs-5.5

> Generated: 2026-10-09T14:20:35+00:00  
> Current: **Claude Sonnet 5** (`anthropic/claude-sonnet-5`)  
> Target: **Claude Sonnet 5.5** (`anthropic/claude-sonnet-5.5`)  
> Run: 20261009T025500Z  ·  runs loaded: 24  ·  live scoring: on  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 83.3% | 100.0% | +20.0% 🟢 |
| Pass rate 95% CI (Wilson) | 55–95% | 76–100% | — |
| Passes / scored runs | 10/12 | 12/12 | Fisher p = 0.478 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | not recorded ×12 | not recorded ×12 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 29.14 | 26.39 | -9.4% 🟢 |
| Cost (total USD) | $0.5490 | $0.6198 | +12.9% 🔴 |
| Cost / run (USD) | $0.0458 | $0.0516 | +12.9% 🔴 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.48, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 46,518 | 46,542 | +0.1% 🔴 |
| output tokens | 45,600 | 52,671 | +15.5% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 92,118 | 99,213 | +7.7% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 9,212 | 8,268 | -10.2% 🟢 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0549 | $0.0516 | -5.9% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 1/3 ⚠️ | 3/3 ✅ |
| r4_schema_load_optimize | 3/3 ✅ | 3/3 ✅ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r3_oracle_to_postgres.20261009T025500Z.json` | result set != golden |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r3_oracle_to_postgres.20261009T025500Z.r1.json` | result set != golden |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Sonnet 5 | 2.0 | 10.0 | 0.1 | 2.5 |
| Claude Sonnet 5.5 | 2.0 | 10.0 | 0.1 | 2.5 |

## Overall score (current = 100 baseline)

- Quality component: 120.0  (w=0.5)
- Cost component:    88.6  (w=0.3, clamped to 50–150)
- Time component:    110.4  (w=0.2, clamped to 50–150)
- **Overall: 108.7**  → target ≥ baseline ✅
