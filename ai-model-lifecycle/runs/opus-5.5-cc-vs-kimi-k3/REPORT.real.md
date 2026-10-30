# Gate 1 Scorecard — opus-5.5-cc-vs-kimi-k3 · real suite

> Generated: 2026-10-27T14:26:57+00:00  
> Current: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Target: **Kimi K3** (`kimi-k3`)  
> Run: 20261027T122733Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: null, {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 50.0% | 16.7% | -66.7% 🔴 |
| Pass rate 95% CI (Wilson) | 19–81% | 3–56% | — |
| Passes / scored runs | 3/6 | 1/6 | Fisher p = 0.545 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×6 | opencode-go ×6 | — |
| Cost source | Claude Code estimate at API prices (6/6) | price table (pricing.py) | — |
| Time (mean latency, s) | 398.91 | 706.44 | +77.1% 🔴 |
| Cost (total USD) | $7.5818 | $9.5226 | +25.6% 🔴 |
| Cost / run (USD) | $1.2636 | $1.5871 | +25.6% 🔴 |

> Cross-gateway pair (by design): current runs via **claude-code**, target via **opencode-go**. Quality is like-for-like (same tasks, same scorers). Time and Cost compare each model **on its own route** — two services with different cost bases — not two models on shared infrastructure.

> Cost uses the `pricing.py` table for runs without an OpenRouter billed cost (runs made before billed cost was recorded). Table prices may be out of date.

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.55, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 547,784 | 292,764 | -46.6% 🟢 |
| output tokens | 301,867 | 572,383 | +89.6% 🔴 |
| · of which thinking | 188,205 | 553,630 | +194.2% 🔴 |
| cache-read tokens | 363,818 | 195,172 | -46.4% 🟢 |
| cache-write tokens | 183,954 | 0 | -100.0% 🟢 |
| **total token spend** | 849,651 | 865,147 | +1.8% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 283,217 | 865,147 | +205.5% 🔴 |
| Cache hit-rate % | 66.4% | 100.0% | +50.6% 🟢 |
| Cost / successful task (USD) | $2.5273 | $9.5226 | +276.8% 🔴 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 3/3 ✅ | 1/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261027T122733Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261027T122733Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261027T122733Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Kimi K3 | `kimi-k3.r1b_jhipster_boot3.20261027T122733Z.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Kimi K3 | `kimi-k3.r1b_jhipster_boot3.20261027T122733Z.r1.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Kimi K3 | `kimi-k3.r1b_jhipster_boot3.20261027T122733Z.r2.json` | no `### FILE:` or `### EDIT:` blocks found in model output |
| Kimi K3 | `kimi-k3.r2_gwt_to_angular.20261027T122733Z.json` | failed checks: build, parity |
| Kimi K3 | `kimi-k3.r2_gwt_to_angular.20261027T122733Z.r1.json` | failed checks: build, parity |

### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)

| Model | input | output | cache-read | cache-write |
|---|---:|---:|---:|---:|
| Kimi K3 | 3.0 | 15.0 | 0.3 | 0.0 |

## Overall score (current = 100 baseline)

- Quality component: 33.3  (w=0.5)
- Cost component:    79.6  (w=0.3, clamped to 50–150)
- Time component:    56.5  (w=0.2, clamped to 50–150)
- **Overall: 51.8**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
