# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-09T02:12:43+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Run: 20261009T014939Z  ·  runs loaded: 8  ·  live scoring: on  
> Newer partial run(s) not scored here: 20261009T015807Z (see `report.py --run <id>`).  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 75.0% | 100.0% | +33.3% 🟢 |
| Pass rate 95% CI (Wilson) | 30–95% | 51–100% | — |
| Passes / scored runs | 3/4 | 4/4 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Time (mean latency, s) | 28.22 | 48.47 | +71.7% 🔴 |
| Cost (total USD) | $0.3824 | $0.5230 | +36.8% 🔴 |
| Cost / run (USD) | $0.0956 | $0.1308 | +36.8% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 4 vs 4). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 15,506 | 15,514 | +0.1% 🔴 |
| output tokens | 12,196 | 23,048 | +89.0% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 27,702 | 38,562 | +39.2% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 9,234 | 9,640 | +4.4% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.1275 | $0.1308 | +2.6% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 1/1 ✅ | 1/1 ✅ |
| r3_oracle_to_postgres | 1/1 ✅ | 1/1 ✅ |
| r4_schema_load_optimize | 0/1 ❌ | 1/1 ✅ |
| r5_etl_dashboard | 1/1 ✅ | 1/1 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 4.8 | `anthropic__claude-opus-4.8.r4_schema_load_optimize.20261009T014939Z.json` | failed checks: index_scan, no_seq_scan_orders |

### Price reference (USD / 1M tokens)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 133.3  (w=0.5)
- Cost component:    73.1  (w=0.3)
- Time component:    58.2  (w=0.2)
- **Overall: 100.2**  → target ≥ baseline ✅
