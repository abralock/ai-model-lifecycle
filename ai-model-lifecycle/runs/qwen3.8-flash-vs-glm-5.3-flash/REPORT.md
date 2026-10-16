# Gate 1 Scorecard — qwen3.8-flash-vs-glm-5.3-flash

> Generated: 2026-10-16T09:32:54+00:00  
> Current: **Qwen3.8 Flash** (`qwen3.8-flash`)  
> Target: **GLM-5.3 Flash** (`glm-5.3-flash`)  
> Run: 20261016T075024Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 41.7% | 58.3% | +40.0% 🟢 |
| Pass rate 95% CI (Wilson) | 19–68% | 32–81% | — |
| Passes / scored runs | 5/12 | 7/12 | Fisher p = 0.684 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | opencode-go ×12 | opencode-go ×12 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 326.21 | 37.51 | -88.5% 🟢 |
| Cost (total USD) | $0.1271 | $0.0127 | -90.0% 🟢 |
| Cost / run (USD) | $0.0106 | $0.0011 | -90.0% 🟢 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.68, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 28,428 | 25,848 | -9.1% 🟢 |
| output tokens | 260,872 | 16,675 | -93.6% 🟢 |
| · of which thinking | 234,209 | 23 | -100.0% 🟢 |
| cache-read tokens | 13,056 | 17,080 | +30.8% 🔴 |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 289,300 | 42,523 | -85.3% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 57,860 | 6,075 | -89.5% 🟢 |
| Cache hit-rate % | 100.0% | 100.0% | +0.0% 🟢 |
| Cost / successful task (USD) | $0.0254 | $0.0018 | -92.8% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 2/3 ⚠️ | 3/3 ✅ |
| r3_oracle_to_postgres | 0/3 ❌ | 0/3 ❌ |
| r4_schema_load_optimize | 2/3 ⚠️ | 3/3 ✅ |
| r5_etl_dashboard | 1/3 ⚠️ | 1/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Qwen3.8 Flash | `qwen3.8-flash.r1_springboot2to3.20261016T075024Z.r2.json` | failed checks: tests, tests_executed |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261016T075024Z.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261016T075024Z.r1.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261016T075024Z.r2.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r4_schema_load_optimize.20261016T075024Z.r2.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| Qwen3.8 Flash | `qwen3.8-flash.r5_etl_dashboard.20261016T075024Z.r1.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| Qwen3.8 Flash | `qwen3.8-flash.r5_etl_dashboard.20261016T075024Z.r2.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261016T075024Z.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261016T075024Z.r1.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261016T075024Z.r2.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r5_etl_dashboard.20261016T075024Z.r1.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| GLM-5.3 Flash | `glm-5.3-flash.r5_etl_dashboard.20261016T075024Z.r2.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Qwen3.8 Flash | 0.15 | 0.47 | 0.016 | 0.2 |
| GLM-5.3 Flash | 0.15 | 0.5 | 0.03 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 140.0  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 145.0**  → target ≥ baseline ✅
