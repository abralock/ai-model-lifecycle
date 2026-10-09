# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-09T02:02:32+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Run: 20261009T015807Z  ·  runs loaded: 6  ·  live scoring: on

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 66.7% | 100.0% | +50.0% 🟢 |
| Pass rate 95% CI (Wilson) | 21–94% | 44–100% | — |
| Passes / scored runs | 2/3 | 3/3 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Time (mean latency, s) | 25.75 | 50.10 | +94.6% 🔴 |
| Cost (total USD) | $0.2070 | $0.3591 | +73.5% 🔴 |
| Cost / run (USD) | $0.0690 | $0.1197 | +73.5% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 3 vs 3). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 5,457 | 5,463 | +0.1% 🔴 |
| output tokens | 7,188 | 16,862 | +134.6% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 12,645 | 22,325 | +76.6% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 6,322 | 7,442 | +17.7% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.1035 | $0.1197 | +15.7% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r4_schema_load_optimize | 2/3 ⚠️ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 4.8 | `anthropic__claude-opus-4.8.r4_schema_load_optimize.20261009T015807Z.r2.json` | no SQL found in model output |

### Price reference (USD / 1M tokens)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 150.0  (w=0.5)
- Cost component:    57.6  (w=0.3)
- Time component:    51.4  (w=0.2)
- **Overall: 102.6**  → target ≥ baseline ✅
