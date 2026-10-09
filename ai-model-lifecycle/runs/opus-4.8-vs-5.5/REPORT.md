# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-09T02:41:28+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Run: 20261009T022349Z  ·  runs loaded: 24  ·  live scoring: on  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 75.0% | -25.0% 🔴 |
| Pass rate 95% CI (Wilson) | 76–100% | 47–91% | — |
| Passes / scored runs | 12/12 | 9/12 | Fisher p = 0.217 |
| Infra errors (excluded) | 0 | 0 | — |
| Time (mean latency, s) | 27.48 | 44.99 | +63.7% 🔴 |
| Cost (total USD) | $1.1340 | $1.4781 | +30.3% 🔴 |
| Cost / run (USD) | $0.0945 | $0.1232 | +30.3% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.22, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 46,518 | 46,542 | +0.1% 🔴 |
| output tokens | 36,057 | 64,598 | +79.2% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 82,575 | 111,140 | +34.6% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 6,881 | 12,349 | +79.5% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0945 | $0.1642 | +73.8% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 1/3 ⚠️ |
| r4_schema_load_optimize | 3/3 ✅ | 2/3 ⚠️ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 5.5 | `anthropic__claude-opus-5.5.r3_oracle_to_postgres.20261009T022349Z.json` | result set != golden |
| Claude Opus 5.5 | `anthropic__claude-opus-5.5.r3_oracle_to_postgres.20261009T022349Z.r2.json` | result set != golden |
| Claude Opus 5.5 | `anthropic__claude-opus-5.5.r4_schema_load_optimize.20261009T022349Z.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |

### Price reference (USD / 1M tokens)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 75.0  (w=0.5)
- Cost component:    76.7  (w=0.3)
- Time component:    61.1  (w=0.2)
- **Overall: 72.7**  → target < baseline ⚠️
