# Gate 1 Scorecard — opus-5.5-cc-vs-glm-5.3 · real suite

> Generated: 2026-10-23T01:46:51+00:00  
> Current: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Target: **GLM-5.3** (`glm-5.3`)  
> Run: 20261023T003736Z  ·  runs loaded: 12  ·  live scoring: on  
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
| Time (mean latency, s) | 390.50 | 212.90 | -45.5% 🟢 |
| Cost (total USD) | $7.4975 | $0.8269 | -89.0% 🟢 |
| Cost / run (USD) | $1.2496 | $0.1378 | -89.0% 🟢 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.18, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 547,919 | 283,563 | -48.2% 🟢 |
| output tokens | 297,600 | 88,763 | -70.2% 🟢 |
| · of which thinking | 171,350 | 51,751 | -69.8% 🟢 |
| cache-read tokens | 363,818 | 151,275 | -58.4% 🟢 |
| cache-write tokens | 184,089 | 0 | -100.0% 🟢 |
| **total token spend** | 845,519 | 372,326 | -56.0% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 281,840 | 0 | -100.0% 🟢 |
| Cache hit-rate % | 66.4% | 100.0% | +50.6% 🟢 |
| Cost / successful task (USD) | $2.4992 | $0.0000 | -100.0% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 3/3 ✅ | 0/3 ❌ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261023T003736Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261023T003736Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261023T003736Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| GLM-5.3 | `glm-5.3.r1b_jhipster_boot3.20261023T003736Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| GLM-5.3 | `glm-5.3.r1b_jhipster_boot3.20261023T003736Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| GLM-5.3 | `glm-5.3.r1b_jhipster_boot3.20261023T003736Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| GLM-5.3 | `glm-5.3.r2_gwt_to_angular.20261023T003736Z.json` | failed checks: build, parity |
| GLM-5.3 | `glm-5.3.r2_gwt_to_angular.20261023T003736Z.r1.json` | failed checks: parity (parity 7 passed, 1 failed) |
| GLM-5.3 | `glm-5.3.r2_gwt_to_angular.20261023T003736Z.r2.json` | failed checks: build, parity |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| GLM-5.3 | 1.4 | 4.4 | 0.26 | 0.0 |
