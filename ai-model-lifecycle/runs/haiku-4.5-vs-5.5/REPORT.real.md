# Gate 1 Scorecard — haiku-4.5-vs-5.5 · real suite

> Generated: 2026-10-13T13:41:23+00:00  
> Current: **Claude Haiku 4.5** (`anthropic/claude-haiku-4.5`)  
> Target: **Claude Haiku 5.5** (`anthropic/claude-haiku-5.5`)  
> Run: 20261013T130717Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 64,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 0.0% | 33.3% | n/a |
| Pass rate 95% CI (Wilson) | 0–39% | 10–70% | — |
| Passes / scored runs | 0/6 | 2/6 | Fisher p = 0.455 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | Amazon Bedrock ×6 | Amazon Bedrock ×6 | — |
| Cost source | billed by OpenRouter (6/6) | billed by OpenRouter (6/6) | — |
| Time (mean latency, s) | 62.97 | 140.08 | +122.5% 🔴 |
| Cost (total USD) | $0.7648 | $0.5816 | -24.0% 🟢 |
| Cost / run (USD) | $0.1275 | $0.0969 | -24.0% 🟢 |

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.45, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 395,154 | 544,545 | +37.8% 🔴 |
| output tokens | 73,938 | 235,522 | +218.5% 🔴 |
| · of which thinking | 22,045 | 153,992 | +598.5% 🔴 |
| cache-read tokens | 0 | 0 | n/a |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 469,092 | 780,067 | +66.3% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 0 | 390,034 | n/a |
| Cache hit-rate % | 0.0% | 0.0% | n/a |
| Cost / successful task (USD) | $0.0000 | $0.2908 | n/a |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 0/3 ❌ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r1b_jhipster_boot3.20261013T130717Z.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r1b_jhipster_boot3.20261013T130717Z.r1.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (1 edit(s) did not apply) |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r1b_jhipster_boot3.20261013T130717Z.r2.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (1 edit(s) did not apply) |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r2_gwt_to_angular.20261013T130717Z.json` | failed checks: parity (parity 6 passed, 1 failed) |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r2_gwt_to_angular.20261013T130717Z.r1.json` | failed checks: parity (parity 5 passed, 2 failed) |
| Claude Haiku 4.5 | `anthropic__claude-haiku-4.5.r2_gwt_to_angular.20261013T130717Z.r2.json` | failed checks: build, parity |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r1b_jhipster_boot3.20261013T130717Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r1b_jhipster_boot3.20261013T130717Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r1b_jhipster_boot3.20261013T130717Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 | `anthropic__claude-haiku-5.5.r2_gwt_to_angular.20261013T130717Z.json` | failed checks: parity (parity 7 passed, 1 failed) |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Claude Haiku 4.5 | 1.0 | 5.0 | 0.1 | 1.25 |
| Claude Haiku 5.5 | 0.1 | 0.5 | 0.005 | 0.125 |
