# Gate 1 Scorecard — qwen3.8-flash-vs-glm-5.3-flash

> Generated: 2026-10-15T10:17:35+00:00  
> Current: **Qwen3.8 Flash** (`qwen3.8-flash`)  
> Target: **GLM-5.3 Flash** (`glm-5.3-flash`)  
> Run: 20261015T081949Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 50.0% | 50.0% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 25–75% | 25–75% | — |
| Passes / scored runs | 6/12 | 6/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | opencode-go ×12 | opencode-go ×12 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 437.15 | 19.75 | -95.5% 🟢 |
| Cost (total USD) | $0.1418 | $0.0121 | -91.5% 🟢 |
| Cost / run (USD) | $0.0118 | $0.0010 | -91.5% 🟢 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 28,428 | 25,848 | -9.1% 🟢 |
| output tokens | 292,280 | 16,380 | -94.4% 🟢 |
| · of which thinking | 266,066 | 0 | -100.0% 🟢 |
| cache-read tokens | 8,192 | 0 | -100.0% 🟢 |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 320,708 | 42,228 | -86.8% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 53,451 | 7,038 | -86.8% 🟢 |
| Cache hit-rate % | 100.0% | 0.0% | -100.0% 🔴 |
| Cost / successful task (USD) | $0.0236 | $0.0020 | -91.5% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 0/3 ❌ | 0/3 ❌ |
| r4_schema_load_optimize | 1/3 ⚠️ | 1/3 ⚠️ |
| r5_etl_dashboard | 2/3 ⚠️ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261015T081949Z.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261015T081949Z.r1.json` | result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r3_oracle_to_postgres.20261015T081949Z.r2.json` | oracle tokens: (+),DUAL,NVL(,ROWNUM,VARCHAR2,sysdate; result set != golden |
| Qwen3.8 Flash | `qwen3.8-flash.r4_schema_load_optimize.20261015T081949Z.json` | failed checks: adds_index, script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| Qwen3.8 Flash | `qwen3.8-flash.r4_schema_load_optimize.20261015T081949Z.r2.json` | failed checks: adds_index, script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| Qwen3.8 Flash | `qwen3.8-flash.r5_etl_dashboard.20261015T081949Z.r2.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261015T081949Z.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261015T081949Z.r1.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261015T081949Z.r2.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r4_schema_load_optimize.20261015T081949Z.r1.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| GLM-5.3 Flash | `glm-5.3-flash.r4_schema_load_optimize.20261015T081949Z.r2.json` | failed checks: adds_index, loaded, index_scan, no_seq_scan_orders, latency_ok |
| GLM-5.3 Flash | `glm-5.3-flash.r5_etl_dashboard.20261015T081949Z.r1.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Qwen3.8 Flash | 0.15 | 0.47 | 0.016 | 0.2 |
| GLM-5.3 Flash | 0.15 | 0.5 | 0.03 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 125.0**  → target ≥ baseline ✅
