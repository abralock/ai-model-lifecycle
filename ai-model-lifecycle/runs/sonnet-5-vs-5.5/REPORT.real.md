# Gate 1 Scorecard — sonnet-5-vs-5.5 · real suite

> Generated: 2026-10-13T09:11:10+00:00  
> Current: **Claude Sonnet 5** (`anthropic/claude-sonnet-5`)  
> Target: **Claude Sonnet 5.5** (`anthropic/claude-sonnet-5.5`)  
> Run: 20261013T081118Z  ·  runs loaded: 12  ·  live scoring: on  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 50.0% | 33.3% | -33.3% 🔴 |
| Pass rate 95% CI (Wilson) | 19–81% | 10–70% | — |
| Passes / scored runs | 3/6 | 2/6 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | Amazon Bedrock ×6 | Amazon Bedrock ×6 | — |
| Cost source | billed by OpenRouter (6/6) | billed by OpenRouter (6/6) | — |
| Time (mean latency, s) | 220.14 | 241.49 | +9.7% 🔴 |
| Cost (total USD) | $2.9211 | $3.3230 | +13.8% 🔴 |
| Cost / run (USD) | $0.4868 | $0.5538 | +13.8% 🔴 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 544,533 | 544,545 | +0.0% 🔴 |
| output tokens | 183,200 | 223,391 | +21.9% 🔴 |
| · of which thinking | 81,016 | 198,485 | +145.0% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 727,733 | 767,936 | +5.5% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 242,578 | 383,968 | +58.3% 🔴 |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.9737 | $1.6615 | +70.6% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 3/3 ✅ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r1b_jhipster_boot3.20261013T081118Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r1b_jhipster_boot3.20261013T081118Z.r1.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5 | `anthropic__claude-sonnet-5.r1b_jhipster_boot3.20261013T081118Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 | `anthropic__claude-sonnet-5.5.r1b_jhipster_boot3.20261013T081118Z.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Claude Sonnet 5.5 | `anthropic__claude-sonnet-5.5.r1b_jhipster_boot3.20261013T081118Z.r1.json` | failed checks: boot3, java17, javax_free, build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 | `anthropic__claude-sonnet-5.5.r1b_jhipster_boot3.20261013T081118Z.r2.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 | `anthropic__claude-sonnet-5.5.r2_gwt_to_angular.20261013T081118Z.json` | failed checks: parity (parity 7 passed, 1 failed) |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Sonnet 5 | 2.0 | 10.0 | 0.1 | 2.5 |
| Claude Sonnet 5.5 | 2.0 | 10.0 | 0.1 | 2.5 |

## Overall score (current = 100 baseline)

- Quality component: 66.7  (w=0.5)
- Cost component:    87.9  (w=0.3, clamped to 50–150)
- Time component:    91.2  (w=0.2, clamped to 50–150)
- **Overall: 77.9**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
