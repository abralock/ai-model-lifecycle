# Gate 1 Scorecard — sonnet-5.5-cc-vs-deepseek-v4-pro

> Generated: 2026-10-24T04:16:14+00:00  
> Current: **Claude Sonnet 5.5 (CC)** (`claude-sonnet-5-5`)  
> Target: **DeepSeek V4 Pro** (`deepseek-v4-pro`)  
> Run: 20261024T024226Z  ·  runs loaded: 24  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 32,000  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 91.7% | 66.7% | -27.3% 🔴 |
| Pass rate 95% CI (Wilson) | 65–99% | 39–86% | — |
| Passes / scored runs | 11/12 | 8/12 | Fisher p = 0.317 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×12 | opencode-go ×12 | — |
| Cost source | Claude Code estimate at API prices (12/12) | price table (pricing.py) | — |
| Time (mean latency, s) | 20.84 | 159.27 | +664.3% 🔴 |
| Cost (total USD) | $0.4815 | $0.4184 | -13.1% 🟢 |
| Cost / run (USD) | $0.0401 | $0.0349 | -13.1% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.32, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 53,466 | 28,449 | -46.8% 🟢 |
| output tokens | 40,767 | 201,649 | +394.6% 🔴 |
| · of which thinking | 9,755 | 184,630 | +1792.7% 🔴 |
| cache-read tokens | 35,901 | 18,432 | -48.7% 🟢 |
| cache-write tokens | 17,541 | 0 | -100.0% 🟢 |
| **total token spend** | 94,233 | 230,098 | +144.2% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 8,567 | 28,762 | +235.7% 🔴 |
| Cache hit-rate % | 67.2% | 100.0% | +48.9% 🟢 |
| Cost / successful task (USD) | $0.0438 | $0.0523 | +19.5% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 2/3 ⚠️ |
| r3_oracle_to_postgres | 3/3 ✅ | 1/3 ⚠️ |
| r4_schema_load_optimize | 2/3 ⚠️ | 2/3 ⚠️ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r4_schema_load_optimize.20261024T024226Z.r1.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| DeepSeek V4 Pro | `deepseek-v4-pro.r1_springboot2to3.20261024T024226Z.r1.json` | failed checks: tests, tests_executed |
| DeepSeek V4 Pro | `deepseek-v4-pro.r3_oracle_to_postgres.20261024T024226Z.json` | result set != golden |
| DeepSeek V4 Pro | `deepseek-v4-pro.r3_oracle_to_postgres.20261024T024226Z.r1.json` | result set != golden |
| DeepSeek V4 Pro | `deepseek-v4-pro.r4_schema_load_optimize.20261024T024226Z.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| DeepSeek V4 Pro | 0.66 | 1.98 | 0.022 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 72.7  (w=0.5)
- Cost component:    115.1  (w=0.3, clamped to 50–150)
- Time component:    50.0  (w=0.2, clamped to 50–150)
- **Overall: 80.9**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
