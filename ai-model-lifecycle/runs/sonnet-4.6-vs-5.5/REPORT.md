# Gate 1 Scorecard — sonnet-4.6-vs-5.5

> Generated: 2026-10-09T04:06:13+00:00  
> Current: **Claude Sonnet 4.6** (`anthropic/claude-sonnet-4.6`)  
> Target: **Claude Sonnet 5.5** (`anthropic/claude-sonnet-5.5`)  
> Run: 20261009T034234Z  ·  runs loaded: 24  ·  live scoring: on  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 75.0% | 100.0% | +33.3% 🟢 |
| Pass rate 95% CI (Wilson) | 47–91% | 76–100% | — |
| Passes / scored runs | 9/12 | 12/12 | Fisher p = 0.217 |
| Infra errors (excluded) | 0 | 0 | — |
| Time (mean latency, s) | 32.46 | 27.25 | -16.0% 🟢 |
| Cost (total USD) | $0.5710 | $0.9421 | +65.0% 🔴 |
| Cost / run (USD) | $0.0476 | $0.0785 | +65.0% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.22, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 32,883 | 46,542 | +41.5% 🔴 |
| output tokens | 31,489 | 53,501 | +69.9% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 64,372 | 100,043 | +55.4% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 7,152 | 8,337 | +16.6% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0634 | $0.0785 | +23.8% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 2/3 ⚠️ | 3/3 ✅ |
| r4_schema_load_optimize | 2/3 ⚠️ | 3/3 ✅ |
| r5_etl_dashboard | 2/3 ⚠️ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 4.6 | `anthropic__claude-sonnet-4.6.r3_oracle_to_postgres.20261009T034234Z.json` | result set != golden |
| Claude Sonnet 4.6 | `anthropic__claude-sonnet-4.6.r4_schema_load_optimize.20261009T034234Z.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| Claude Sonnet 4.6 | `anthropic__claude-sonnet-4.6.r5_etl_dashboard.20261009T034234Z.r2.json` | failed checks: etl_runs, log_mismatch_zero, idempotent |

### Price reference (USD / 1M tokens)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Sonnet 4.6 | 3.0 | 15.0 | 0.3 | 3.75 |
| Claude Sonnet 5.5 | 3.0 | 15.0 | 0.3 | 3.75 |

## Overall score (current = 100 baseline)

- Quality component: 133.3  (w=0.5)
- Cost component:    60.6  (w=0.3)
- Time component:    119.1  (w=0.2)
- **Overall: 108.7**  → target ≥ baseline ✅
