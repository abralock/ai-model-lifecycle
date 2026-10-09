# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-09T01:12:38+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Run date: 20261009  ·  runs loaded: 8  ·  live scoring: on

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 100.0% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 51–100% | 51–100% | — |
| Passes / scored runs | 4/4 | 4/4 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Time (mean latency, s) | 27.40 | 38.61 | +40.9% 🔴 |
| Cost (total USD) | $0.3752 | $0.4383 | +16.8% 🔴 |
| Cost / run (USD) | $0.0938 | $0.1096 | +16.8% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 4 vs 4). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 15,467 | 15,475 | +0.1% 🔴 |
| output tokens | 11,916 | 18,820 | +57.9% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 27,383 | 34,295 | +25.2% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 6,846 | 8,574 | +25.2% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0938 | $0.1096 | +16.8% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 1/1 ✅ | 1/1 ✅ |
| r3_oracle_to_postgres | 1/1 ✅ | 1/1 ✅ |
| r4_schema_load_optimize | 1/1 ✅ | 1/1 ✅ |
| r5_etl_dashboard | 1/1 ✅ | 1/1 ✅ |

### Price reference (USD / 1M tokens)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    85.6  (w=0.3)
- Time component:    71.0  (w=0.2)
- **Overall: 89.9**  → target < baseline ⚠️
