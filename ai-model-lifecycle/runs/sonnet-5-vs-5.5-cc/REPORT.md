# Gate 1 Scorecard — sonnet-5-vs-5.5-cc

> Generated: 2026-10-17T03:22:32+00:00  
> Current: **Claude Sonnet 5 (CC)** (`claude-sonnet-5`)  
> Target: **Claude Sonnet 5.5 (CC)** (`claude-sonnet-5-5`)  
> Run: 20261017T024725Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 83.3% | 100.0% | +20.0% 🟢 |
| Pass rate 95% CI (Wilson) | 55–95% | 76–100% | — |
| Passes / scored runs | 10/12 | 12/12 | Fisher p = 0.478 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×12 | claude-code ×12 | — |
| Cost source | Claude Code estimate at API prices (12/12) | Claude Code estimate at API prices (12/12) | — |
| Time (mean latency, s) | 37.32 | 20.96 | -43.8% 🟢 |
| Cost (total USD) | $0.7849 | $0.5062 | -35.5% 🟢 |
| Cost / run (USD) | $0.0654 | $0.0422 | -35.5% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.48, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 54,171 | 53,462 | -1.3% 🟢 |
| output tokens | 56,824 | 41,985 | -26.1% 🟢 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 0 | 32,682 | n/a |
| cache-write tokens | 54,147 | 20,756 | -61.7% 🟢 |
| **total token spend** | 110,995 | 95,447 | -14.0% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 11,100 | 7,954 | -28.3% 🟢 |
| Cache hit-rate % | 0.0% | 61.2% | n/a |
| Cost / successful task (USD) | $0.0785 | $0.0422 | -46.3% 🟢 |

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
| Claude Sonnet 5 (CC) | `claude-sonnet-5.r3_oracle_to_postgres.20261017T024725Z.r1.json` | result set != golden |
| Claude Sonnet 5 (CC) | `claude-sonnet-5.r3_oracle_to_postgres.20261017T024725Z.r2.json` | result set != golden |

## Overall score (current = 100 baseline)

- Quality component: 120.0  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 135.0**  → target ≥ baseline ✅
