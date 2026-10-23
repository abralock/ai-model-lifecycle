# Gate 1 Scorecard — opus-5.5-cc-vs-qwen3.8-flash

> Generated: 2026-10-23T09:14:51+00:00  
> Current: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Target: **Qwen3.8 Flash** (`qwen3.8-flash`)  
> Run: 20261023T061221Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 30.0% | -70.0% 🔴 |
| Pass rate 95% CI (Wilson) | 76–100% | 11–60% | — |
| Passes / scored runs | 12/12 | 3/10 | Fisher p = 0.001 |
| Infra errors (excluded) | 0 | 2 | — |
| Provider (runs) | claude-code ×12 | opencode-go ×10 | — |
| Cost source | Claude Code estimate at API prices (12/12) | price table (pricing.py) | — |
| Time (mean latency, s) | 39.85 | 409.35 | +927.3% 🔴 |
| Cost (total USD) | $1.3313 | $0.1245 | -90.6% 🟢 |
| Cost / run (USD) | $0.1109 | $0.0125 | -88.8% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 53,412 | 21,987 | -58.8% 🟢 |
| output tokens | 57,952 | 257,875 | +345.0% 🔴 |
| · of which thinking | 16,332 | 235,481 | +1341.8% 🔴 |
| cache-read tokens | 32,682 | 1,024 | -96.9% 🟢 |
| cache-write tokens | 20,706 | 0 | -100.0% 🟢 |
| **total token spend** | 111,364 | 279,862 | +151.3% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 9,280 | 93,287 | +905.2% 🔴 |
| Cache hit-rate % | 61.2% | 100.0% | +63.4% 🟢 |
| Cost / successful task (USD) | $0.1109 | $0.0415 | -62.6% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 2/2 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 0/3 ❌ |
| r4_schema_load_optimize | 3/3 ✅ | 1/3 ⚠️ |
| r5_etl_dashboard | 3/3 ✅ | 0/2 ❌ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Qwen3.8 Flash | `qwen3.8-flash.r1_springboot2to3.20261023T061221Z.r1.json` | INFRA ERROR: Timeout: litellm.Timeout: AnthropicException - litellm.Timeout: Connection timed out after 1800.0 seconds. |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261023T061221Z.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261023T061221Z.r1.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261023T061221Z.r2.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r4_schema_load_optimize.20261023T061221Z.json` | no SQL found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r4_schema_load_optimize.20261023T061221Z.r2.json` | no SQL found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r5_etl_dashboard.20261023T061221Z.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| Qwen3.8 Flash | `qwen3.8-flash.r5_etl_dashboard.20261023T061221Z.r1.json` | INFRA ERROR: Timeout: litellm.Timeout: AnthropicException - litellm.Timeout: Connection timed out after 1800.0 seconds. |
| Qwen3.8 Flash | `qwen3.8-flash.r5_etl_dashboard.20261023T061221Z.r2.json` | no SQL found in model output |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Qwen3.8 Flash | 0.15 | 0.47 | 0.016 | 0.2 |

## Overall score (current = 100 baseline)

- Quality component: 30.0  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    50.0  (w=0.2, clamped to 50–150)
- **Overall: 70.0**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
