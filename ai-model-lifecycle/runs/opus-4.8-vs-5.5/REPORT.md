# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-08T15:38:23+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Runs loaded: 8  ·  live scoring: on

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 75.0% | 75.0% | +0.0% 🟢 |
| Passes / runs | 3/4 | 3/4 | — |
| Time (mean latency, s) | 28.51 | 43.53 | +52.7% 🔴 |
| Cost (total USD) | $0.3461 | $0.4227 | +22.1% 🔴 |

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 8,123 | 8,131 | +0.1% 🔴 |
| output tokens | 12,220 | 19,510 | +59.7% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 20,343 | 27,641 | +35.9% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 6,781 | 9,214 | +35.9% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.1154 | $0.1409 | +22.1% 🔴 |

## Per-case quality

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | PASS | PASS |
| r3_oracle_to_postgres | PASS | PASS |
| r4_schema_load_optimize | PASS | PASS |
| r5_etl_dashboard | FAIL | FAIL |

### Price reference (USD / 1M tokens)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    81.9  (w=0.3)
- Time component:    65.5  (w=0.2)
- **Overall: 87.7**  → target < baseline ⚠️
