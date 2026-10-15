# Gate 1 Scorecard — qwen3.8-flash-vs-glm-5.3-flash · real suite

> Generated: 2026-10-15T14:16:54+00:00  
> Current: **Qwen3.8 Flash** (`qwen3.8-flash`)  
> Target: **GLM-5.3 Flash** (`glm-5.3-flash`)  
> Run: 20261015T123041Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 32,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 0.0% | 16.7% | n/a |
| Pass rate 95% CI (Wilson) | 0–39% | 3–56% | — |
| Passes / scored runs | 0/6 | 1/6 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | opencode-go ×6 | opencode-go ×6 | — |
| Cost source | price table (pricing.py) | price table (pricing.py) | — |
| Time (mean latency, s) | 424.64 | 289.00 | -31.9% 🟢 |
| Cost (total USD) | $0.1403 | $0.0898 | -36.0% 🟢 |
| Cost / run (USD) | $0.0234 | $0.0150 | -36.0% 🟢 |

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 313,527 | 283,563 | -9.6% 🟢 |
| output tokens | 192,000 | 86,165 | -55.1% 🟢 |
| · of which thinking | 185,389 | 56,461 | -69.5% 🟢 |
| cache-read tokens | 188,160 | 141,056 | -25.0% 🟢 |
| cache-write tokens | 0 | 0 | n/a |
| **total token spend** | 505,527 | 369,728 | -26.9% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 0 | 369,728 | n/a |
| Cache hit-rate % | 100.0% | 100.0% | +0.0% 🟢 |
| Cost / successful task (USD) | $0.0000 | $0.0898 | n/a |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 0/3 ❌ | 1/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Qwen3.8 Flash | `qwen3.8-flash.r1b_jhipster_boot3.20261015T123041Z.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r1b_jhipster_boot3.20261015T123041Z.r1.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r1b_jhipster_boot3.20261015T123041Z.r2.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r2_gwt_to_angular.20261015T123041Z.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r2_gwt_to_angular.20261015T123041Z.r1.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r2_gwt_to_angular.20261015T123041Z.r2.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| GLM-5.3 Flash | `glm-5.3-flash.r1b_jhipster_boot3.20261015T123041Z.json` | failed checks: edits_applied, javax_free, build, unit_tests, integration_tests, e2e (1 edit(s) did not apply) |
| GLM-5.3 Flash | `glm-5.3-flash.r1b_jhipster_boot3.20261015T123041Z.r1.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| GLM-5.3 Flash | `glm-5.3-flash.r1b_jhipster_boot3.20261015T123041Z.r2.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| GLM-5.3 Flash | `glm-5.3-flash.r2_gwt_to_angular.20261015T123041Z.json` | failed checks: parity (parity 7 passed, 1 failed) |
| GLM-5.3 Flash | `glm-5.3-flash.r2_gwt_to_angular.20261015T123041Z.r1.json` | failed checks: parity (parity 4 passed, 2 failed) |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Qwen3.8 Flash | 0.15 | 0.47 | 0.016 | 0.2 |
| GLM-5.3 Flash | 0.15 | 0.5 | 0.03 | 0.0 |
