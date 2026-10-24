# Gate 1 Scorecard — sonnet-5.5-cc-vs-deepseek-v4-pro · real suite

> Generated: 2026-10-24T05:16:32+00:00  
> Current: **Claude Sonnet 5.5 (CC)** (`claude-sonnet-5-5`)  
> Target: **DeepSeek V4 Pro** (`deepseek-v4-pro`)  
> Run: 20261024T041958Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: null, {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 50.0% | 0.0% | -100.0% 🔴 |
| Pass rate 95% CI (Wilson) | 19–81% | 0–39% | — |
| Passes / scored runs | 3/6 | 0/6 | Fisher p = 0.182 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×6 | opencode-go ×6 | — |
| Cost source | Claude Code estimate at API prices (6/6) | price table (pricing.py) | — |
| Time (mean latency, s) | 260.77 | 195.14 | -25.2% 🟢 |
| Cost (total USD) | $3.3353 | $0.5077 | -84.8% 🟢 |
| Cost / run (USD) | $0.5559 | $0.0846 | -84.8% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.18, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 547,945 | 311,454 | -43.2% 🟢 |
| output tokens | 256,242 | 150,305 | -41.3% 🟢 |
| · of which thinking | 199,047 | 117,762 | -40.8% 🟢 |
| cache-read tokens | 363,818 | 207,360 | -43.0% 🟢 |
| cache-write tokens | 184,115 | 0 | -100.0% 🟢 |
| **total token spend** | 804,187 | 461,759 | -42.6% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 268,062 | 0 | -100.0% 🟢 |
| Cache hit-rate % | 66.4% | 100.0% | +50.6% 🟢 |
| Cost / successful task (USD) | $1.1118 | $0.0000 | -100.0% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 3/3 ✅ | 0/3 ❌ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261024T041958Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261024T041958Z.r1.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261024T041958Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| DeepSeek V4 Pro | `deepseek-v4-pro.r1b_jhipster_boot3.20261024T041958Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| DeepSeek V4 Pro | `deepseek-v4-pro.r1b_jhipster_boot3.20261024T041958Z.r1.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (1 edit(s) did not apply) |
| DeepSeek V4 Pro | `deepseek-v4-pro.r1b_jhipster_boot3.20261024T041958Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| DeepSeek V4 Pro | `deepseek-v4-pro.r2_gwt_to_angular.20261024T041958Z.json` | failed checks: build, parity |
| DeepSeek V4 Pro | `deepseek-v4-pro.r2_gwt_to_angular.20261024T041958Z.r1.json` | failed checks: build, parity |
| DeepSeek V4 Pro | `deepseek-v4-pro.r2_gwt_to_angular.20261024T041958Z.r2.json` | failed checks: build, parity |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| DeepSeek V4 Pro | 0.66 | 1.98 | 0.022 | 0.0 |
