# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-09T14:19:35+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Run: 20261009T022349Z  ·  runs loaded: 24  ·  live scoring: on  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 91.7% | -8.3% 🔴 |
| Pass rate 95% CI (Wilson) | 76–100% | 65–99% | — |
| Passes / scored runs | 12/12 | 11/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | not recorded ×12 | not recorded ×12 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 27.48 | 44.99 | +63.7% 🔴 |
| Cost (total USD) | $1.1340 | $1.4781 | +30.3% 🔴 |
| Cost / run (USD) | $0.0945 | $0.1232 | +30.3% 🔴 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 46,518 | 46,542 | +0.1% 🔴 |
| output tokens | 36,057 | 64,598 | +79.2% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 82,575 | 111,140 | +34.6% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 6,881 | 10,104 | +46.8% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0945 | $0.1344 | +42.2% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 3/3 ✅ |
| r4_schema_load_optimize | 3/3 ✅ | 2/3 ⚠️ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 5.5 | `anthropic__claude-opus-5.5.r4_schema_load_optimize.20261009T022349Z.json` | failed checks: script_runs, loaded, index_scan, no_seq_scan_orders, latency_ok |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 91.7  (w=0.5)
- Cost component:    76.7  (w=0.3, clamped to 50–150)
- Time component:    61.1  (w=0.2, clamped to 50–150)
- **Overall: 81.1**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
