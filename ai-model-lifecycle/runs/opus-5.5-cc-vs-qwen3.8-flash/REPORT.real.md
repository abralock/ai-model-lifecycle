# Gate 1 Scorecard — opus-5.5-cc-vs-qwen3.8-flash · real suite

> Generated: 2026-10-23T13:44:20+00:00  
> Current: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Target: **Qwen3.8 Flash** (`qwen3.8-flash`)  
> Run: 20261023T095118Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 32,000  
> Thinking budget sent: null, {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 50.0% | 0.0% | -100.0% 🔴 |
| Pass rate 95% CI (Wilson) | 19–81% | 0–49% | — |
| Passes / scored runs | 3/6 | 0/4 | Fisher p = 0.200 |
| Infra errors (excluded) | 0 | 2 | — |
| Provider (runs) | claude-code ×6 | opencode-go ×4 | — |
| Cost source | Claude Code estimate at API prices (6/6) | price table (pricing.py) | — |
| Time (mean latency, s) | 445.83 | 494.80 | +11.0% 🔴 |
| Cost (total USD) | $7.2972 | $0.0896 | -98.8% 🟢 |
| Cost / run (USD) | $1.2162 | $0.0224 | -98.2% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.20, n = 6 vs 4). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 656,405 | 187,335 | -71.5% 🟢 |
| output tokens | 286,498 | 128,000 | -55.3% 🟢 |
| · of which thinking | 188,356 | 123,104 | -34.6% 🟢 |
| cache-read tokens | 472,300 | 82,432 | -82.5% 🟢 |
| cache-write tokens | 184,091 | 0 | -100.0% 🟢 |
| **total token spend** | 942,903 | 315,335 | -66.6% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 314,301 | 0 | -100.0% 🟢 |
| Cache hit-rate % | 72.0% | 100.0% | +39.0% 🟢 |
| Cost / successful task (USD) | $2.4324 | $0.0000 | -100.0% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/1 ❌ |
| r2_gwt_to_angular | 3/3 ✅ | 0/3 ❌ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261023T095118Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261023T095118Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261023T095118Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Qwen3.8 Flash | `qwen3.8-flash.r1b_jhipster_boot3.20261023T095118Z.json` | INFRA ERROR: Timeout: litellm.Timeout: AnthropicException - litellm.Timeout: Connection timed out after 1800.0 seconds. |
| Qwen3.8 Flash | `qwen3.8-flash.r1b_jhipster_boot3.20261023T095118Z.r1.json` | INFRA ERROR: Timeout: litellm.Timeout: AnthropicException - litellm.Timeout: Connection timed out after 1800.0 seconds. |
| Qwen3.8 Flash | `qwen3.8-flash.r1b_jhipster_boot3.20261023T095118Z.r2.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r2_gwt_to_angular.20261023T095118Z.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r2_gwt_to_angular.20261023T095118Z.r1.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Qwen3.8 Flash | `qwen3.8-flash.r2_gwt_to_angular.20261023T095118Z.r2.json` | no `### FILE:` or `### EDIT:` blocks found in model output |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Qwen3.8 Flash | 0.15 | 0.47 | 0.016 | 0.2 |
