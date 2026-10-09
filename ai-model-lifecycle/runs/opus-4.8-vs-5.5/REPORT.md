# Gate 1 Scorecard — opus-4.8-vs-5.5

> Generated: 2026-10-09T14:57:19+00:00  
> Current: **Claude Opus 4.8** (`anthropic/claude-opus-4.8`)  
> Target: **Claude Opus 5.5** (`anthropic/claude-opus-5.5`)  
> Run: 20261009T143648Z  ·  runs loaded: 24  ·  live scoring: on  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 100.0% | 100.0% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 76–100% | 76–100% | — |
| Passes / scored runs | 12/12 | 12/12 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | Amazon Bedrock ×12 | Amazon Bedrock ×12 | — |
| Cost source | billed by OpenRouter (12/12) | billed by OpenRouter (12/12) | — |
| Time (mean latency, s) | 25.86 | 62.31 | +141.0% 🔴 |
| Cost (total USD) | $1.1209 | $1.3870 | +23.7% 🔴 |
| Cost / run (USD) | $0.0934 | $0.1156 | +23.7% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 46,518 | 46,542 | +0.1% 🔴 |
| output tokens | 35,532 | 60,040 | +69.0% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 82,050 | 106,582 | +29.9% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 6,838 | 8,882 | +29.9% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0934 | $0.1156 | +23.7% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 3/3 ✅ | 3/3 ✅ |
| r4_schema_load_optimize | 3/3 ✅ | 3/3 ✅ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 5.0 | 25.0 | 0.25 | 6.25 |
| Claude Opus 5.5 | 4.0 | 20.0 | 0.2 | 5.0 |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    80.8  (w=0.3, clamped to 50–150)
- Time component:    50.0  (w=0.2, clamped to 50–150)
- **Overall: 84.2**  → target < baseline ⚠️
