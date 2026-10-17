# Gate 1 Scorecard — opus-4.8-vs-5.5-cc · real suite

> Generated: 2026-10-17T02:18:51+00:00  
> Current: **Claude Opus 4.8 (CC)** (`claude-opus-4-8`)  
> Target: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`)  
> Run: 20261017T003122Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 50.0% | 33.3% | -33.3% 🔴 |
| Pass rate 95% CI (Wilson) | 19–81% | 10–70% | — |
| Passes / scored runs | 3/6 | 2/6 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×6 | claude-code ×6 | — |
| Cost source | Claude Code estimate at API prices (6/6) | Claude Code estimate at API prices (6/6) | — |
| Time (mean latency, s) | 630.71 | 363.79 | -42.3% 🟢 |
| Cost (total USD) | $12.5483 | $6.9755 | -44.4% 🟢 |
| Cost / run (USD) | $2.0914 | $1.1626 | -44.4% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 656,446 | 547,922 | -16.5% 🟢 |
| output tokens | 239,355 | 271,500 | +13.4% 🔴 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 0 | 363,818 | n/a |
| cache-write tokens | 656,432 | 184,092 | -72.0% 🟢 |
| **total token spend** | 895,801 | 819,422 | -8.5% 🟢 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 298,600 | 409,711 | +37.2% 🔴 |
| Cache hit-rate % | 0.0% | 66.4% | n/a |
| Cost / successful task (USD) | $4.1828 | $3.4878 | -16.6% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 3/3 ✅ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Opus 4.8 (CC) | `claude-opus-4-8.r1b_jhipster_boot3.20261017T003122Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 4.8 (CC) | `claude-opus-4-8.r1b_jhipster_boot3.20261017T003122Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 4.8 (CC) | `claude-opus-4-8.r1b_jhipster_boot3.20261017T003122Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261017T003122Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261017T003122Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r1b_jhipster_boot3.20261017T003122Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Opus 5.5 (CC) | `claude-opus-5-5.r2_gwt_to_angular.20261017T003122Z.json` | failed checks: parity (parity 0 passed, 3 failed) |

## Overall score (current = 100 baseline)

- Quality component: 66.7  (w=0.5)
- Cost component:    150.0  (w=0.3, clamped to 50–150)
- Time component:    150.0  (w=0.2, clamped to 50–150)
- **Overall: 108.3**  → target < baseline ⚠️ (lower pass rate than current: cheaper or faster does not make up for it)
