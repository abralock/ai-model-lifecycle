# Gate 1 Scorecard — opus-5.5-cc-vs-glm-5.3

> Generated: 2026-10-23T00:22:39+00:00  
> Current: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Target: **GLM-5.3** (`glm-5.3`)  
> Run: 20261023T000856Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 83.3% | -16.7% 🔴 |
| Pass rate 95% CI (Wilson) | 76–100% | 55–95% | — |
| Passes / scored runs | 12/12 | 10/12 | Fisher p = 0.478 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×12 | opencode-go ×12 | — |
| Cost source | Claude Code estimate at API prices (12/12) | price table (pricing.py) | — |
| Time (mean latency, s) | 42.98 | 14.38 | -66.6% 🟢 |
| Cost (total USD) | $1.3428 | $0.1164 | -91.3% 🟢 |
| Cost / run (USD) | $0.1119 | $0.0097 | -91.3% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.48, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 53,417 | 25,938 | -51.4% 🟢 |
| output tokens | 59,779 | 17,566 | -70.6% 🟢 |
| · of which thinking | 17,752 | 33 | -99.8% 🟢 |
| cache-read tokens | 35,901 | 10,710 | -70.2% 🟢 |
| cache-write tokens | 17,492 | 0 | -100.0% 🟢 |
| **total token spend** | 113,196 | 43,504 | -61.6% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 9,433 | 4,350 | -53.9% 🟢 |
| Cache hit-rate % | 67.2% | 100.0% | +48.7% 🟢 |
| Cost / successful task (USD) | $0.1119 | $0.0116 | -89.6% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 2/3 ⚠️ |
| r4_schema_load_optimize | 3/3 ✅ | 3/3 ✅ |
| r5_etl_dashboard | 3/3 ✅ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| GLM-5.3 | `glm-5.3.r3_oracle_to_postgres.20261023T000856Z.json` | result set != golden |
| GLM-5.3 | `glm-5.3.r5_etl_dashboard.20261023T000856Z.r2.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| GLM-5.3 | 1.4 | 4.4 | 0.26 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 83.3  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 116.7**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
