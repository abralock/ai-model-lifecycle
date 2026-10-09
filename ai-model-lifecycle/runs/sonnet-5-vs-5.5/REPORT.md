# Gate 1 Scorecard — sonnet-5-vs-5.5

> Generated: 2026-10-09T15:16:25+00:00  
> Current: **Claude Sonnet 5** (`anthropic/claude-sonnet-5`)  
> Target: **Claude Sonnet 5.5** (`anthropic/claude-sonnet-5.5`)  
> Run: 20261009T150204Z  ·  runs loaded: 24  ·  live scoring: on  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 66.7% | 100.0% | +50.0% 🟢 |
| Pass rate 95% CI (Wilson) | 39–86% | 76–100% | — |
| Passes / scored runs | 8/12 | 12/12 | Fisher p = 0.093 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | Amazon Bedrock ×12 | Amazon Bedrock ×12 | — |
| Cost source | billed by OpenRouter (12/12) | billed by OpenRouter (12/12) | — |
| Time (mean latency, s) | 28.97 | 26.80 | -7.5% 🟢 |
| Cost (total USD) | $0.5478 | $0.6124 | +11.8% 🔴 |
| Cost / run (USD) | $0.0457 | $0.0510 | +11.8% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.09, n = 12 vs 12). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 46,518 | 46,542 | +0.1% 🔴 |
| output tokens | 45,481 | 51,935 | +14.2% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 91,999 | 98,477 | +7.0% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 11,500 | 8,206 | -28.6% 🟢 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0685 | $0.0510 | -25.5% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1_springboot2to3 | 3/3 ✅ | 3/3 ✅ |
| r3_oracle_to_postgres | 0/3 ❌ | 3/3 ✅ |
| r4_schema_load_optimize | 2/3 ⚠️ | 3/3 ✅ |
| r5_etl_dashboard | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r3_oracle_to_postgres.20261009T150204Z.json` | result set != golden |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r3_oracle_to_postgres.20261009T150204Z.r1.json` | result set != golden |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r3_oracle_to_postgres.20261009T150204Z.r2.json` | result set != golden |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r4_schema_load_optimize.20261009T150204Z.json` | failed checks: index_scan, no_seq_scan_orders |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Sonnet 5 | 2.0 | 10.0 | 0.1 | 2.5 |
| Claude Sonnet 5.5 | 2.0 | 10.0 | 0.1 | 2.5 |

## Overall score (current = 100 baseline)

- Quality component: 150.0  (w=0.5)
- Cost component:    89.5  (w=0.3, clamped to 50–150)
- Time component:    108.1  (w=0.2, clamped to 50–150)
- **Overall: 123.5**  → target ≥ baseline ✅
