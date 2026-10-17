# Gate 1 Scorecard — haiku-4.5-vs-5.5-cc · real suite

> Generated: 2026-10-17T07:43:49+00:00  
> Current: **Claude Haiku 4.5 (CC)** (`claude-haiku-4-5`)  
> Target: **Claude Haiku 5.5 (CC)** (`claude-haiku-5-5`)  
> Run: 20261017T070151Z  ·  runs loaded: 12  ·  live scoring: on  
> Output limit (max_tokens): current 128,000 · target 128,000  
> Thinking budget sent: {"effort": "medium"} (models.yaml `reasoning`)  

## Summary — Current vs Target

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Quality (pass rate) | 0.0% | 50.0% | n/a |
| Pass rate 95% CI (Wilson) | 0–39% | 19–81% | — |
| Passes / scored runs | 0/6 | 3/6 | Fisher p = 0.182 |
| Infra errors (excluded) | 0 | 0 | — |
| Provider (runs) | claude-code ×6 | claude-code ×6 | — |
| Cost source | Claude Code estimate at API prices (6/6) | Claude Code estimate at API prices (6/6) | — |
| Time (mean latency, s) | 125.62 | 197.96 | +57.6% 🔴 |
| Cost (total USD) | $1.3961 | $0.6881 | -50.7% 🟢 |
| Cost / run (USD) | $0.2327 | $0.1147 | -50.7% 🟢 |

> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The subscription does not bill per call, so this is not a bill, and it is not comparable with OpenRouter billed cost.

> ⚠️ The quality difference is **not statistically significant** (Fisher p = 0.18, n = 6 vs 6). Add cases or repeats before treating it as a real difference.

## Raw token counts

| Bucket | Current | Target | Δ |
|---|---:|---:|---:|
| input tokens | 397,940 | 547,937 | +37.7% 🔴 |
| output tokens | 120,052 | 326,028 | +171.6% 🔴 |
| · of which thinking | 68,145 | 258,592 | +279.5% 🔴 |
| cache-read tokens | 0 | 363,818 | n/a |
| cache-write tokens | 397,880 | 184,107 | -53.7% 🟢 |
| **total token spend** | 517,992 | 873,965 | +68.7% 🔴 |

## Normalized views

| Metric | Current | Target | Δ |
|---|---:|---:|---:|
| Tokens / successful task | 0 | 291,322 | n/a |
| Cache hit-rate % | 0.0% | 66.4% | n/a |
| Cost / successful task (USD) | $0.0000 | $0.2294 | n/a |

## Per-case quality (passes / runs)

| Case | Current | Target |
|---|---|---|
| r1b_jhipster_boot3 | 0/3 ❌ | 0/3 ❌ |
| r2_gwt_to_angular | 0/3 ❌ | 3/3 ✅ |

## Failing runs

| Model | Run file | Reason |
|---|---|---|
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r1b_jhipster_boot3.20261017T070151Z.json` | failed checks: edits_applied, build, unit_tests, integration_tests, e2e (1 edit(s) did not apply) |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r1b_jhipster_boot3.20261017T070151Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r1b_jhipster_boot3.20261017T070151Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r2_gwt_to_angular.20261017T070151Z.json` | failed checks: build, parity |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r2_gwt_to_angular.20261017T070151Z.r1.json` | failed checks: build, parity |
| Claude Haiku 4.5 (CC) | `claude-haiku-4-5.r2_gwt_to_angular.20261017T070151Z.r2.json` | failed checks: parity (parity 0 passed, 3 failed) |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r1b_jhipster_boot3.20261017T070151Z.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r1b_jhipster_boot3.20261017T070151Z.r1.json` | failed checks: build, unit_tests, integration_tests, e2e |
| Claude Haiku 5.5 (CC) | `claude-haiku-5-5.r1b_jhipster_boot3.20261017T070151Z.r2.json` | failed checks: build, unit_tests, integration_tests, e2e |
