# Gate 1 Scorecard — haiku-4.5-vs-5.5-cc

> Generated: 2026-10-16T14:36:22+00:00  
> Current: **Claude Haiku 4.5 (CC)** (`claude-haiku-4-5`)  
> Target: **Claude Haiku 5.5 (CC)** (`claude-haiku-5-5`)  
> Run: 20261016T141027Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 66.7% | 58.3% | -12.5% 🔴 |
| Pass rate 95% CI (Wilson) | 39–86% | 32–81% | — |
| Passes / scored runs | 8/12 | 7/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×12 | claude-code ×12 | — |
| Cost source | Claude Code estimate at API prices (12/12) | Claude Code estimate at API prices (12/12) | — |
| Time (mean latency, s) | 65.92 | 26.17 | -60.3% 🟢 |
| Cost (total USD) | $0.6766 | $0.0436 | -93.6% 🟢 |
| Cost / run (USD) | $0.0564 | $0.0036 | -93.6% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 38,904 | 53,437 | +37.4% 🔴 |
| output tokens | 124,062 | 79,542 | -35.9% 🟢 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 0 | 35,901 | n/a |
| cache-write tokens | 17,409 | 17,512 | +0.6% 🔴 |
| **total token spend** | 162,966 | 132,979 | -18.4% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 20,371 | 18,997 | -6.7% 🟢 |
| Cache hit-rate % | 0.0% | 67.2% | n/a |
| Cost / successful task (USD) | $0.0846 | $0.0062 | -92.6% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 2/3 ⚠️ | 3/3 ✅ |
| r3_oracle_to_postgres | 1/3 ⚠️ | 1/3 ⚠️ |
| r4_schema_load_optimize | 2/3 ⚠️ | 0/3 ❌ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r1_springboot2to3.20261016T141027Z.r1.json` | failed checks: compile, tests, tests_executed, hidden_tests |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r3_oracle_to_postgres.20261016T141027Z.json` | result set != golden |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r3_oracle_to_postgres.20261016T141027Z.r1.json` | result set != golden |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r4_schema_load_optimize.20261016T141027Z.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r3_oracle_to_postgres.20261016T141027Z.r1.json` | result set != golden |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r3_oracle_to_postgres.20261016T141027Z.r2.json` | result set != golden |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r4_schema_load_optimize.20261016T141027Z.json` | failed checks: index_scan, no_seq_scan_orders |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r4_schema_load_optimize.20261016T141027Z.r1.json` | failed checks: index_scan, no_seq_scan_orders |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r4_schema_load_optimize.20261016T141027Z.r2.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |

## Overall score (current = 100 baseline)

- Quality component: 87.5  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 118.8**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
