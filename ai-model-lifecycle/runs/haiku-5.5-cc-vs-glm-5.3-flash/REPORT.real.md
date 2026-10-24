# Gate 1 Scorecard — haiku-5.5-cc-vs-glm-5.3-flash · real suite

> Generated: 2026-10-24T08:30:15+00:00  
> Current: **Claude Haiku 5.5 (CC)** (`claude-haiku-5-5`)  
> Target: **GLM-5.3 Flash** (`glm-5.3-flash`)  
> Run: 20261024T063522Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: null, {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 16.7% | 0.0% | -100.0% 🔴 |
| Pass rate 95% CI (Wilson) | 3–56% | 0–39% | — |
| Passes / scored runs | 1/6 | 0/6 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×6 | opencode-go ×6 | — |
| Cost source | Claude Code estimate at API prices (6/6) | price table (pricing.py) | — |
| Time (mean latency, s) | 161.90 | 762.90 | +371.2% 🔴 |
| Cost (total USD) | $0.6400 | $0.0977 | -84.7% 🟢 |
| Cost / run (USD) | $0.1067 | $0.0163 | -84.7% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 547,936 | 283,563 | -48.2% 🟢 |
| output tokens | 276,741 | 108,319 | -60.9% 🟢 |
| · of which thinking | 191,761 | 25,783 | -86.6% 🟢 |
| cache-read tokens | 363,818 | 34,048 | -90.6% 🟢 |
| cache-write tokens | 184,106 | 0 | -100.0% 🟢 |
| **total token spend** | 824,677 | 391,882 | -52.5% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 824,677 | 0 | -100.0% 🟢 |
| Cache hit-rate % | 66.4% | 100.0% | +50.6% 🟢 |
| Cost / successful task (USD) | $0.6400 | $0.0000 | -100.0% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 1/3 ⚠️ | 0/3 ❌ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r1b_jhipster_boot3.20261024T063522Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r1b_jhipster_boot3.20261024T063522Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r1b_jhipster_boot3.20261024T063522Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r2_gwt_to_angular.20261024T063522Z.r1.json` | failed checks: build, parity |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r2_gwt_to_angular.20261024T063522Z.r2.json` | failed checks: parity (parity 3 passed, 1 failed) |
| GLM-5.3 Flash | `glm-5.3-flash.r1b_jhipster_boot3.20261024T063522Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| GLM-5.3 Flash | `glm-5.3-flash.r1b_jhipster_boot3.20261024T063522Z.r1.json` | failed checks: javax_free, build, unit_tests, integration_tests, e2e |
| GLM-5.3 Flash | `glm-5.3-flash.r1b_jhipster_boot3.20261024T063522Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| GLM-5.3 Flash | `glm-5.3-flash.r2_gwt_to_angular.20261024T063522Z.json` | failed checks: parity (parity 7 passed, 1 failed) |
| GLM-5.3 Flash | `glm-5.3-flash.r2_gwt_to_angular.20261024T063522Z.r1.json` | failed checks: parity (parity 7 passed, 1 failed) |
| GLM-5.3 Flash | `glm-5.3-flash.r2_gwt_to_angular.20261024T063522Z.r2.json` | failed checks: parity (parity 7 passed, 1 failed) |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| GLM-5.3 Flash | 0.15 | 0.5 | 0.03 | 0.0 |
