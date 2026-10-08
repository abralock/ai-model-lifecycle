# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-08T16:40:58+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Runs loaded: 24  ·  live scoring: on

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 91.7% | 58.3% | -36.4% 🔴 |
| Passes / runs | 11/12 | 7/12 | — |
| Time (mean latency, s) | 26.38 | 39.61 | +50.2% 🔴 |
| Cost (total USD) | $0.9780 | $1.1765 | +20.3% 🔴 |

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 27,753 | 27,777 | +0.1% 🔴 |
| output tokens | 33,569 | 53,269 | +58.7% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 61,322 | 81,046 | +32.2% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 5,575 | 11,578 | +107.7% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0889 | $0.1681 | +89.0% 🔴 |

## Per-case quality

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | PASS | FAIL |
| r3_oracle_to_postgres | PASS | PASS |
| r4_schema_load_optimize | FAIL | FAIL |
| r5_etl_dashboard | PASS | PASS |

### Price reference (USD / 1M tokens)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 63.6  (w=0.5)
- Cost component:    52.9  (w=0.3)
- Time component:    66.6  (w=0.2)
- **Overall: 61.0**  → target < baseline ⚠️
