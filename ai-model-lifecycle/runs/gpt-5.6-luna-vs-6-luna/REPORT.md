# Gate 1 Scorecard — gpt-5.6-luna-vs-6-luna

> Generated: 2026-10-15T04:09:44+00:00  
> Current: **GPT-5.6 Luna** (`gpt-5.6-luna`)  
> Target: **GPT-6 Luna** (`gpt-6-luna`)  
> Run: 20261015T033007Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 100.0% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 76–100% | 76–100% | — |
| Passes / scored runs | 12/12 | 12/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | opencode-go-responses ×12 | opencode-go-responses ×12 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 28.21 | 30.82 | +9.2% 🔴 |
| Cost (total USD) | $0.0477 | $0.0207 | -56.5% 🟢 |
| Cost / run (USD) | $0.0040 | $0.0017 | -56.5% 🟢 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 26,283 | 26,283 | +0.0% 🟢 |
| output tokens | 35,018 | 35,779 | +2.2% 🔴 |
| · of which thinking | 18,352 | 19,595 | +6.8% 🔴 |
| cache-read tokens | 19,118 | 19,118 | +0.0% 🟢 |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 61,301 | 62,062 | +1.2% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 5,108 | 5,172 | +1.2% 🔴 |
| Cache hit-rate % | 100.0% | 100.0% | +0.0% 🟢 |
| Cost / successful task (USD) | $0.0040 | $0.0017 | -56.5% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 3/3 ✅ |
| r4_schema_load_optimize | 3/3 ✅ | 3/3 ✅ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| GPT-5.6 Luna | 0.2 | 1.2 | 0.02 | 0.25 |
| GPT-6 Luna | 0.1 | 0.5 | 0.01 | 0.125 |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    91.5  (w=0.2, clamped to 50–150)
- **Overall: 113.3**  → target ≥ baseline ✅
