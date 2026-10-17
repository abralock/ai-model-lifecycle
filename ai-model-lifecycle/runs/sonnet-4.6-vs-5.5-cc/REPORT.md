# Gate 1 Scorecard — sonnet-4.6-vs-5.5-cc

> Generated: 2026-10-17T03:43:03+00:00  
> Current: **Claude Sonnet 4.6 (CC)** (`claude-sonnet-4-6`)  
> Target: **Claude Sonnet 5.5 (CC)** (`claude-sonnet-5-5`)  
> Run: 20261017T025905Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 91.7% | 100.0% | +9.1% 🟢 |
| Pass rate 95% CI (Wilson) | 65–99% | 76–100% | — |
| Passes / scored runs | 11/12 | 12/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×12 | claude-code ×12 | — |
| Cost source | Claude Code estimate at API prices (12/12) | Claude Code estimate at API prices (12/12) | — |
| Time (mean latency, s) | 124.43 | 85.25 | -31.5% 🟢 |
| Cost (total USD) | $1.4920 | $0.4829 | -67.6% 🟢 |
| Cost / run (USD) | $0.1243 | $0.0402 | -67.6% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 41,005 | 65,362 | +59.4% 🔴 |
| output tokens | 84,000 | 41,270 | -50.9% 🟢 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 2,446 | 49,023 | +1904.2% 🔴 |
| cache-write tokens | 38,520 | 16,311 | -57.7% 🟢 |
| **total token spend** | 125,005 | 106,632 | -14.7% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 11,364 | 8,886 | -21.8% 🟢 |
| Cache hit-rate % | 6.0% | 75.0% | +1156.7% 🟢 |
| Cost / successful task (USD) | $0.1356 | $0.0402 | -70.3% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 2/3 ⚠️ | 3/3 ✅ |
| r4_schema_load_optimize | 3/3 ✅ | 3/3 ✅ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 4.6 (CC) | `claude-sonnet-4-6.r3_oracle_to_postgres.20261017T025905Z.json` | result set != golden |

## Overall score (current = 100 baseline)

- Quality component: 109.1  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    146.0  (w=0.2, clamped to 50–150)
- **Overall: 128.7**  → target ≥ baseline ✅
