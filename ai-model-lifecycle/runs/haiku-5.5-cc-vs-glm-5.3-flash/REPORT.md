# Gate 1 Scorecard — haiku-5.5-cc-vs-glm-5.3-flash

> Generated: 2026-10-24T06:26:14+00:00  
> Current: **Claude Haiku 5.5 (CC)** (`claude-haiku-5-5`)  
> Target: **GLM-5.3 Flash** (`glm-5.3-flash`)  
> Run: 20261024T061427Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 58.3% | 50.0% | -14.3% 🔴 |
| Pass rate 95% CI (Wilson) | 32–81% | 25–75% | — |
| Passes / scored runs | 7/12 | 6/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×12 | opencode-go ×12 | — |
| Cost source | Claude Code estimate at API prices (12/12) | price table (pricing.py) | — |
| Time (mean latency, s) | 26.13 | 14.59 | -44.2% 🟢 |
| Cost (total USD) | $0.0430 | $0.0121 | -71.7% 🟢 |
| Cost / run (USD) | $0.0036 | $0.0010 | -71.7% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 53,441 | 25,938 | -51.5% 🟢 |
| output tokens | 78,176 | 16,261 | -79.2% 🟢 |
| · of which thinking | 45,320 | 0 | -100.0% 🟢 |
| cache-read tokens | 35,901 | 3,840 | -89.3% 🟢 |
| cache-write tokens | 17,516 | 0 | -100.0% 🟢 |
| **total token spend** | 131,617 | 42,199 | -67.9% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 18,802 | 7,033 | -62.6% 🟢 |
| Cache hit-rate % | 67.2% | 100.0% | +48.8% 🟢 |
| Cost / successful task (USD) | $0.0061 | $0.0020 | -67.0% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 1/3 ⚠️ | 0/3 ❌ |
| r4_schema_load_optimize | 0/3 ❌ | 1/3 ⚠️ |
| r5_etl_dashboard | 3/3 ✅ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r3_oracle_to_postgres.20261024T061427Z.json` | result set != golden |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r3_oracle_to_postgres.20261024T061427Z.r2.json` | result set != golden |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r4_schema_load_optimize.20261024T061427Z.json` | failed checks: index_scan, no_seq_scan_orders |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r4_schema_load_optimize.20261024T061427Z.r1.json` | failed checks: index_scan, no_seq_scan_orders |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r4_schema_load_optimize.20261024T061427Z.r2.json` | failed checks: adds_index, loaded, index_scan, no_seq_scan_orders |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261024T061427Z.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261024T061427Z.r1.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r3_oracle_to_postgres.20261024T061427Z.r2.json` | result set != golden |
| GLM-5.3 Flash | `glm-5.3-flash.r4_schema_load_optimize.20261024T061427Z.json` | failed checks: index_scan, no_seq_scan_orders |
| GLM-5.3 Flash | `glm-5.3-flash.r4_schema_load_optimize.20261024T061427Z.r2.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| GLM-5.3 Flash | `glm-5.3-flash.r5_etl_dashboard.20261024T061427Z.json` | failed checks: etl_runs, reconciliation_zero, log_mismatch_zero, dataset_loads, idempotent |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| GLM-5.3 Flash | 0.15 | 0.5 | 0.03 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 85.7  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 117.9**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
