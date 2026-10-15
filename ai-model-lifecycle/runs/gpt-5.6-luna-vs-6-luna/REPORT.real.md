# Gate 1 Scorecard — gpt-5.6-luna-vs-6-luna · real suite

> Generated: 2026-10-15T05:38:35+00:00  
> Current: **GPT-5.6 Luna** (`gpt-5.6-luna`)  
> Target: **GPT-6 Luna** (`gpt-6-luna`)  
> Run: 20261015T051257Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 0.0% | 0.0% | n/a |
| Pass rate 95% CI (Wilson) | 0–39% | 0–39% | — |
| Passes / scored runs | 0/6 | 0/6 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | opencode-go-responses ×6 | opencode-go-responses ×6 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 33.37 | 68.41 | +105.0% 🔴 |
| Cost (total USD) | $0.0922 | $0.0488 | -47.1% 🟢 |
| Cost / run (USD) | $0.0154 | $0.0081 | -47.1% 🟢 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 289,833 | 289,833 | +0.0% 🟢 |
| output tokens | 25,323 | 35,751 | +41.2% 🔴 |
| · of which thinking | 2,001 | 7,971 | +298.4% 🔴 |
| cache-read tokens | 193,210 | 193,210 | +0.0% 🟢 |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 315,156 | 325,584 | +3.3% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 0 | 0 | n/a |
| Cache hit-rate % | 100.0% | 100.0% | +0.0% 🟢 |
| Cost / successful task (USD) | $0.0000 | $0.0000 | n/a |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 0/3 ❌ | 0/3 ❌ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| GPT-5.6 Luna | `gpt-5.6-luna.r1b_jhipster_boot3.20261015T051257Z.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (2 edit(s) did not apply) |
| GPT-5.6 Luna | `gpt-5.6-luna.r1b_jhipster_boot3.20261015T051257Z.r1.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (3 edit(s) did not apply) |
| GPT-5.6 Luna | `gpt-5.6-luna.r1b_jhipster_boot3.20261015T051257Z.r2.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (3 edit(s) did not apply) |
| GPT-5.6 Luna | `gpt-5.6-luna.r2_gwt_to_angular.20261015T051257Z.json` | failed checks: parity (parity 0 passed, 3 failed) |
| GPT-5.6 Luna | `gpt-5.6-luna.r2_gwt_to_angular.20261015T051257Z.r1.json` | failed checks: parity (parity 7 passed, 1 failed) |
| GPT-5.6 Luna | `gpt-5.6-luna.r2_gwt_to_angular.20261015T051257Z.r2.json` | failed checks: parity (parity 0 passed, 3 failed) |
| GPT-6 Luna | `gpt-6-luna.r1b_jhipster_boot3.20261015T051257Z.json` | failed checks: edits_applied, javax_free, build, unit_tests, integration_tests, e2e (1 edit(s) did not apply) |
| GPT-6 Luna | `gpt-6-luna.r1b_jhipster_boot3.20261015T051257Z.r1.json` | failed checks: edits_applied, javax_free, build, unit_tests, integration_tests, e2e (2 edit(s) did not apply) |
| GPT-6 Luna | `gpt-6-luna.r1b_jhipster_boot3.20261015T051257Z.r2.json` | failed checks: edits_applied, javax_free, build, unit_tests, integration_tests, e2e (3 edit(s) did not apply) |
| GPT-6 Luna | `gpt-6-luna.r2_gwt_to_angular.20261015T051257Z.json` | failed checks: parity (parity 7 passed, 1 failed) |
| GPT-6 Luna | `gpt-6-luna.r2_gwt_to_angular.20261015T051257Z.r1.json` | failed checks: parity (parity 7 passed, 1 failed) |
| GPT-6 Luna | `gpt-6-luna.r2_gwt_to_angular.20261015T051257Z.r2.json` | failed checks: build, parity |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| GPT-5.6 Luna | 0.2 | 1.2 | 0.02 | 0.25 |
| GPT-6 Luna | 0.1 | 0.5 | 0.01 | 0.125 |
