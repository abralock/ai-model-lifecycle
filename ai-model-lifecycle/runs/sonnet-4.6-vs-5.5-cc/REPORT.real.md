# Gate 1 Scorecard — sonnet-4.6-vs-5.5-cc · real suite

> Generated: 2026-10-17T06:35:19+00:00  
> Current: **Claude Sonnet 4.6 (CC)** (`claude-sonnet-4-6`)  
> Target: **Claude Sonnet 5.5 (CC)** (`claude-sonnet-5-5`)  
> Run: 20261017T043407Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 16.7% | 50.0% | +200.0% 🟢 |
| Pass rate 95% CI (Wilson) | 3–56% | 19–81% | — |
| Passes / scored runs | 1/6 | 3/6 | Fisher p = 0.545 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×6 | claude-code ×6 | — |
| Cost source | Claude Code estimate at API prices (6/6) | Claude Code estimate at API prices (6/6) | — |
| Time (mean latency, s) | 807.29 | 347.94 | -56.9% 🟢 |
| Cost (total USD) | $8.4082 | $4.3630 | -48.1% 🟢 |
| Cost / run (USD) | $1.4014 | $0.7272 | -48.1% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.55, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 397,775 | 784,502 | +97.2% 🔴 |
| output tokens | 401,443 | 348,863 | -13.1% 🟢 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 0 | 580,423 | n/a |
| cache-write tokens | 397,757 | 204,063 | -48.7% 🟢 |
| **total token spend** | 799,218 | 1,133,365 | +41.8% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 799,218 | 377,788 | -52.7% 🟢 |
| Cache hit-rate % | 0.0% | 74.0% | n/a |
| Cost / successful task (USD) | $8.4082 | $1.4543 | -82.7% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 1/3 ⚠️ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 4.6 (CC) | `claude-sonnet-4-6.r1b_jhipster_boot3.20261017T043407Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 4.6 (CC) | `claude-sonnet-4-6.r1b_jhipster_boot3.20261017T043407Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 4.6 (CC) | `claude-sonnet-4-6.r1b_jhipster_boot3.20261017T043407Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 4.6 (CC) | `claude-sonnet-4-6.r2_gwt_to_angular.20261017T043407Z.json` | failed checks: build, parity |
| Claude Sonnet 4.6 (CC) | `claude-sonnet-4-6.r2_gwt_to_angular.20261017T043407Z.r2.json` | failed checks: parity (parity 0 passed, 3 failed) |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261017T043407Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261017T043407Z.r1.json` | failed checks: boot3, java17, javax_free, build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261017T043407Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |

## Overall score (current = 100 baseline)

- Quality component: 300.0  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 225.0**  → target ≥ baseline ✅
