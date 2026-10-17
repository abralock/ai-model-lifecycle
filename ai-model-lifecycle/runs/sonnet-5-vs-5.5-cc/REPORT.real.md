# Gate 1 Scorecard — sonnet-5-vs-5.5-cc · real suite

> Generated: 2026-10-17T04:52:20+00:00  
> Current: **Claude Sonnet 5 (CC)** (`claude-sonnet-5`)  
> Target: **Claude Sonnet 5.5 (CC)** (`claude-sonnet-5-5`)  
> Run: 20261017T034727Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 33.3% | 33.3% | +0.0% 🟢 |
| Pass rate 95% CI (Wilson) | 10–70% | 10–70% | — |
| Passes / scored runs | 2/6 | 2/6 | Fisher p = 1.000 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×6 | claude-code ×6 | — |
| Cost source | Claude Code estimate at API prices (6/6) | Claude Code estimate at API prices (6/6) | — |
| Time (mean latency, s) | 198.91 | 267.62 | +34.5% 🔴 |
| Cost (total USD) | $3.8152 | $3.4948 | -8.4% 🟢 |
| Cost / run (USD) | $0.6359 | $0.5825 | -8.4% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 1.00, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 548,299 | 547,946 | -0.1% 🟢 |
| output tokens | 162,198 | 272,191 | +67.8% 🔴 |
| · of which thinking | 0 | 0 | n/a |
| cache-read tokens | 0 | 363,818 | n/a |
| cache-write tokens | 548,287 | 184,116 | -66.4% 🟢 |
| **total token spend** | 710,497 | 820,137 | +15.4% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 355,248 | 410,068 | +15.4% 🔴 |
| Cache hit-rate % | 0.0% | 66.4% | n/a |
| Cost / successful task (USD) | $1.9076 | $1.7474 | -8.4% 🟢 |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 2/3 ⚠️ | 2/3 ⚠️ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Sonnet 5 (CC) | `claude-sonnet-5.r1b_jhipster_boot3.20261017T034727Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5 (CC) | `claude-sonnet-5.r1b_jhipster_boot3.20261017T034727Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5 (CC) | `claude-sonnet-5.r1b_jhipster_boot3.20261017T034727Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5 (CC) | `claude-sonnet-5.r2_gwt_to_angular.20261017T034727Z.json` | failed checks: build, parity |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261017T034727Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261017T034727Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r1b_jhipster_boot3.20261017T034727Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Sonnet 5.5 (CC) | `claude-sonnet-5-5.r2_gwt_to_angular.20261017T034727Z.json` | failed checks: build, parity |

## Overall score (current = 100 baseline)

- Quality component: 100.0  (w=0.5)
- Cost component:    109.2  (w=0.3, clamped to 50–150)
- Time component:    74.3  (w=0.2, clamped to 50–150)
- **Overall: 97.6**  → target < baseline ⚠️
