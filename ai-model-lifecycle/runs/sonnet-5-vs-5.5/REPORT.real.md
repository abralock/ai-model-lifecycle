# Gate 1 Scorecard — sonnet-5-vs-5.5 · real suite

> Generated: 2026-10-13T10:29:43+00:00  
> Current: **Claude Sonnet 5** (`anthropic/claude-sonnet-5`)  
> Target: **Claude Sonnet 5.5** (`anthropic/claude-sonnet-5.5`)  
> Run: 20261013T093223Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 50.0% | 50.0% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 19–81% | 19–81% | — |
| Passes / scored runs | 3/6 | 3/6 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | Amazon Bedrock ×6 | Amazon Bedrock ×6 | — |
| Cost source | billed by OpenRouter (6/6) | billed by OpenRouter (6/6) | — |
| Time (mean latency, s) | 201.27 | 288.14 | +43.2% 🔴 |
| Cost (total USD) | $2.7280 | $4.0293 | +47.7% 🔴 |
| Cost / run (USD) | $0.4547 | $0.6716 | +47.7% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 544,533 | 544,545 | +0.0% 🔴 |
| output tokens | 163,893 | 294,025 | +79.4% 🔴 |
| · of which thinking | 76,775 | 193,724 | +152.3% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 708,426 | 838,570 | +18.4% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 236,142 | 279,523 | +18.4% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.9093 | $1.3431 | +47.7% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 3/3 ✅ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r1b_jhipster_boot3.20261013T093223Z.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r1b_jhipster_boot3.20261013T093223Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r1b_jhipster_boot3.20261013T093223Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 | `anthropic__claude-sonnet-5.5.r1b_jhipster_boot3.20261013T093223Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 | `anthropic__claude-sonnet-5.5.r1b_jhipster_boot3.20261013T093223Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 | `anthropic__claude-sonnet-5.5.r1b_jhipster_boot3.20261013T093223Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Sonnet 5 | 2.0 | 10.0 | 0.1 | 2.5 |
| Claude Sonnet 5.5 | 2.0 | 10.0 | 0.1 | 2.5 |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    67.7  (w=0.3, clamped to 50–150)
- Time component:    69.9  (w=0.2, clamped to 50–150)
- **Overall: 84.3**  → target < baseline ⚠️
