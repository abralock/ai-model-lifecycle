# Gate 1 Scorecard — haiku-4.5-vs-5.5 · real suite

> Generated: 2026-10-13T05:51:52+00:00  
> Current: **Claude Haiku 4.5** (`anthropic/claude-haiku-4.5`)  
> Target: **Claude Haiku 5.5** (`anthropic/claude-haiku-5.5`)  
> Run: 20261013T052330Z  ·  runs loaded: 12  ·  live scoring: on  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 0.0% | 50.0% | n/a |
| Pass rate 95% CI (Wilson) | 0–39% | 19–81% | — |
| Passes / scored runs | 0/6 | 3/6 | Fisher p = 0.182 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | Amazon Bedrock ×6 | Amazon Bedrock ×6 | — |
| Cost source | billed by OpenRouter (6/6) | billed by OpenRouter (6/6) | — |
| Time (mean latency, s) | 33.61 | 133.70 | +297.8% 🔴 |
| Cost (total USD) | $0.6166 | $0.5686 | -7.8% 🟢 |
| Cost / run (USD) | $0.1028 | $0.0948 | -7.8% 🟢 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.18, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 394,974 | 544,545 | +37.9% 🔴 |
| output tokens | 44,321 | 226,797 | +411.7% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 439,295 | 771,342 | +75.6% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 0 | 257,114 | n/a |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0000 | $0.1895 | n/a |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 0/3 ❌ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r1b_jhipster_boot3.20261013T052330Z.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r1b_jhipster_boot3.20261013T052330Z.r1.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r1b_jhipster_boot3.20261013T052330Z.r2.json` | failed checks: edits_applied, javax_free, build, unit_tests, integration_tests, e2e (1 edit(s) did not apply) |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r2_gwt_to_angular.20261013T052330Z.json` | failed checks: parity (parity 2 passed, 2 failed) |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r2_gwt_to_angular.20261013T052330Z.r1.json` | failed checks: parity (parity 7 passed, 1 failed) |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r2_gwt_to_angular.20261013T052330Z.r2.json` | failed checks: parity (parity 2 passed, 2 failed) |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r1b_jhipster_boot3.20261013T052330Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r1b_jhipster_boot3.20261013T052330Z.r1.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (3 edit(s) did not apply) |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r1b_jhipster_boot3.20261013T052330Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Haiku 4.5 | 1.0 | 5.0 | 0.1 | 1.25 |
| Claude Haiku 5.5 | 0.1 | 0.5 | 0.005 | 0.125 |
