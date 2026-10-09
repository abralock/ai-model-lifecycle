# Gate 1 Scorecard — haiku-4.5-vs-5.5

> Generated: 2026-10-09T14:22:37+00:00  
> Current: **Claude Haiku 4.5** (`anthropic/claude-haiku-4.5`)  
> Target: **Claude Haiku 5.5** (`anthropic/claude-haiku-5.5`)  
> Run: 20261009T040952Z  ·  runs loaded: 24  ·  live scoring: on  
> Newer partial run(s) not scored here: 20261009T141722Z, 20261009T132552Z (see `report.py --run <id>`).  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 75.0% | 66.7% | -11.1% 🔴 |
| Pass rate 95% CI (Wilson) | 47–91% | 39–86% | — |
| Passes / scored runs | 9/12 | 8/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | not recorded ×12 | not recorded ×12 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 10.99 | 21.19 | +92.9% 🔴 |
| Cost (total USD) | $0.1549 | $0.0384 | -75.2% 🟢 |
| Cost / run (USD) | $0.0129 | $0.0032 | -75.2% 🟢 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 32,871 | 46,542 | +41.6% 🔴 |
| output tokens | 24,405 | 67,536 | +176.7% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 57,276 | 114,078 | +99.2% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 6,364 | 14,260 | +124.1% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0172 | $0.0048 | -72.1% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 3/3 ✅ |
| r4_schema_load_optimize | 3/3 ✅ | 0/3 ❌ |
| r5_etl_dashboard | 0/3 ❌ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r5_etl_dashboard.20261009T040952Z.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r5_etl_dashboard.20261009T040952Z.r1.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r5_etl_dashboard.20261009T040952Z.r2.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r4_schema_load_optimize.20261009T040952Z.json` | failed checks: index_scan, no_seq_scan_orders |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r4_schema_load_optimize.20261009T040952Z.r1.json` | failed checks: index_scan, no_seq_scan_orders |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r4_schema_load_optimize.20261009T040952Z.r2.json` | failed checks: index_scan, no_seq_scan_orders |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r5_etl_dashboard.20261009T040952Z.r1.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Haiku 4.5 | 1.0 | 5.0 | 0.1 | 1.25 |
| Claude Haiku 5.5 | 0.1 | 0.5 | 0.005 | 0.125 |

## Overall score (current = 100 baseline)

- Quality component: 88.9  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    51.8  (w=0.2, clamped to 50–150)
- **Overall: 99.8**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
