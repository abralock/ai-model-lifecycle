# Gate 1 Scorecard — glm-5.2-vs-5.3

> Generated: 2026-10-14T13:28:15+00:00  
> Current: **GLM-5.2** (`glm-5.2`)  
> Target: **GLM-5.3** (`glm-5.3`)  
> Run: 20261014T132733Z  ·  runs loaded: 2  ·  live scoring: on  
> ⚠️ **Partial run** — missing cases: r1_springboot2to3, r4_schema_load_optimize, r5_etl_dashboard. Not a full Gate 1 scorecard.  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 100.0% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 21–100% | 21–100% | — |
| Passes / scored runs | 1/1 | 1/1 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | opencode-go ×1 | opencode-go ×1 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 12.55 | 9.50 | -24.3% 🟢 |
| Cost (total USD) | $0.0082 | $0.0083 | +1.7% 🔴 |
| Cost / run (USD) | $0.0082 | $0.0083 | +1.7% 🔴 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 1 vs 1). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 1,596 | 1,596 | +0.0% 🟢 |
| output tokens | 1,355 | 1,293 | -4.6% 🟢 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 10 | 1,595 | +15850.0% 🔴 |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 2,951 | 2,889 | -2.1% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 2,951 | 2,889 | -2.1% 🟢 |
| Cache hit-rate % | 100.0% | 100.0% | +0.0% 🟢 |
| Cost / successful task (USD) | $0.0082 | $0.0083 | +1.7% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r3_oracle_to_postgres | 1/1 ✅ | 1/1 ✅ |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| GLM-5.2 | 1.4 | 4.4 | 0.26 | 0.0 |
| GLM-5.3 | 1.4 | 4.4 | 0.26 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    98.3  (w=0.3, clamped to 50–150)
- Time component:    132.1  (w=0.2, clamped to 50–150)
- **Overall: 105.9**  → target ≥ baseline ✅
