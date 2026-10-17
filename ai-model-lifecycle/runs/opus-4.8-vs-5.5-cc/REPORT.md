# Gate 1 Scorecard — opus-4.8-vs-5.5-cc

> Generated: 2026-10-17T00:27:59+00:00  
> Current: **Claude Opus 4.8 (CC)** (`claude-opus-4-8`)  
> Target: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Run: 20261017T000912Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 100.0% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 76–100% | 76–100% | — |
| Passes / scored runs | 12/12 | 12/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×12 | claude-code ×12 | — |
| Cost source | Claude Code estimate at API prices (12/12) | Claude Code estimate at API prices (12/12) | — |
| Time (mean latency, s) | 34.99 | 48.59 | +38.9% 🔴 |
| Cost (total USD) | $1.6057 | $1.5011 | -6.5% 🟢 |
| Cost / run (USD) | $0.1338 | $0.1251 | -6.5% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 53,405 | 53,411 | +0.0% 🔴 |
| output tokens | 42,870 | 66,443 | +55.0% 🔴 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 0 | 32,682 | n/a |
| cache-write tokens | 53,381 | 20,705 | -61.2% 🟢 |
| **total token spend** | 96,275 | 119,854 | +24.5% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 8,023 | 9,988 | +24.5% 🔴 |
| Cache hit-rate % | 0.0% | 61.2% | n/a |
| Cost / successful task (USD) | $0.1338 | $0.1251 | -6.5% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 3/3 ✅ |
| r4_schema_load_optimize | 3/3 ✅ | 3/3 ✅ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    107.0  (w=0.3, clamped to 50–150)
- Time component:    72.0  (w=0.2, clamped to 50–150)
- **Overall: 96.5**  → target < baseline ⚠️
