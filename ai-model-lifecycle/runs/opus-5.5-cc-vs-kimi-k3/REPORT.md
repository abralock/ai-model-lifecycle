# Gate 1 Scorecard — opus-5.5-cc-vs-kimi-k3

> Generated: 2026-10-26T03:01:37+00:00  
> Current: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Target: **Kimi K3** (`kimi-k3`)  
> Run: 20261026T013635Z  ·  runs loaded: 24  ·  live scoring: on  
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
| Time (mean latency, s) | 39.85 | 32.17 | -19.3% 🟢 |
| Cost (total USD) | $1.3010 | $0.8921 | -31.4% 🟢 |
| Cost / run (USD) | $0.1084 | $0.0743 | -31.4% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.32, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 53,410 | 27,888 | -47.8% 🟢 |
| output tokens | 57,692 | 53,540 | -7.2% 🟢 |
| · of which thinking | 15,747 | 35,998 | +128.6% 🔴 |
| cache-read tokens | 35,901 | 17,728 | -50.6% 🟢 |
| cache-write tokens | 17,485 | 0 | -100.0% 🟢 |
| **total token spend** | 111,102 | 81,428 | -26.7% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 10,100 | 10,178 | +0.8% 🔴 |
| Cache hit-rate % | 67.2% | 100.0% | +48.7% 🟢 |
| Cost / successful task (USD) | $0.1183 | $0.1115 | -5.7% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 0/3 ❌ |
| r4_schema_load_optimize | 2/3 ⚠️ | 2/3 ⚠️ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r4_schema_load_optimize.20261026T013635Z.r1.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |
| Kimi K3 | `kimi-k3.r3_oracle_to_postgres.20261026T013635Z.json` | result set != golden |
| Kimi K3 | `kimi-k3.r3_oracle_to_postgres.20261026T013635Z.r1.json` | result set != golden |
| Kimi K3 | `kimi-k3.r3_oracle_to_postgres.20261026T013635Z.r2.json` | result set != golden |
| Kimi K3 | `kimi-k3.r4_schema_load_optimize.20261026T013635Z.r2.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Kimi K3 | 3.0 | 15.0 | 0.3 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 72.7  (w=0.5)
- Cost component:    145.8  (w=0.3, clamped to 50–150)
- Time component:    123.9  (w=0.2, clamped to 50–150)
- **Overall: 104.9**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
