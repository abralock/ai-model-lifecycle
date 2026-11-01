# Gate 1 leaderboard

> Generated: 2026-11-01T13:17:52+00:00 · live scoring: on (score cache)  
> Routes: Claude Code, OpenCode Go (OpenRouter left out; `--routes all` includes it)  
> Results: from run 20261031T114732Z on · agentic runs only (single-shot screening is in each pair's REPORT.md; `--all-results` shows it here)

# Agentic migration (primary result)

The model works on a copy of the project in a sandbox with a coding agent, the way a developer would: it changes code, builds, runs the tests and fixes what fails, until its goal is met or the time limit is hit (agentic.py). What it delivered is then checked by the same acceptance test as single-shot, including hidden tests it never saw. Infra errors (sessions that never ran) are excluded.

Claude models run in Claude Code; open-weight models run in opencode (rows marked "· opencode"), so an opencode row differs from a Claude row in both the model and the agent.

## Ranking

Models that tried every task rank first, then by pass rate; equal pass rates are ranked by time, then cost. Time is the agent's wall-clock time. Cost is Claude Code's estimate at API list prices, or for opencode rows the OpenCode Go list price of the tokens used (quota, not a bill); the ranking adds up each task's mean attempt, i.e. one pass through the tasks tried.

| # | Model | Thinking level | Sanity passed | Real passed | Overall pass rate | Tasks tried | Time, all tasks (min) | Cost, all tasks |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Claude Sonnet 5.5 (CC) | low | 12/12 | 2/2 | 100% (14/14) | 6/6 | 26.3 | $2.03 |
| 2 | Claude Opus 5.5 (CC) | low | 12/12 | 2/2 | 100% (14/14) | 6/6 | 31.2 | $3.94 |
| 3 | Claude Opus 5.5 (CC) | medium | 12/12 | 2/2 | 100% (14/14) | 6/6 | 33.9 | $7.13 |
| 4 | Claude Sonnet 5.5 (CC) | medium | 13/13 | 2/2 | 100% (15/15) | 6/6 | 37.4 | $2.59 |
| 5 | Claude Sonnet 5.5 (CC) | high | 12/12 | 2/2 | 100% (14/14) | 6/6 | 42.5 | $2.89 |
| 6 | Claude Haiku 5.5 (CC) | medium | 12/12 | 2/2 | 100% (14/14) | 6/6 | 58.8 | $3.35 |
| 7 | Claude Haiku 5.5 (CC) | low | 12/12 | 2/2 | 100% (14/14) | 6/6 | 64.7 | $2.57 |
| 8 | Claude Haiku 5.5 (CC) | high | 12/12 | 2/2 | 100% (14/14) | 6/6 | 72.5 | $4.34 |
| 9 | Claude Opus 5.5 (CC) | high | 12/12 | 2/2 | 100% (14/14) | 6/6 | 76.4 | $14.64 |
| 10 | GLM-5.3 · opencode | medium | 13/13 | 1/2 | 93% (14/15) | 6/6 | 113.8 | $24.07 |

### r1_springboot2to3 — Spring Boot 2 → 3 (small app)

| # | Model | Thinking level | Passed | Pass rate | Unit tests | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | low | 3/3 | 100% | 100% (12/12) | 0.4 | 0.4 | 100% | 100% | 100% | 0.16 | $0.07 | $0.07 | 6 | 20261101T003616Z |
| 2 | Claude Sonnet 5.5 (CC) | high | 3/3 | 100% | 100% (12/12) | 0.5 | 0.5 | 100% | 100% | 100% | 0.17 | $0.08 | $0.08 | 5 | 20261031T160419Z |
| 3 | Claude Opus 5.5 (CC) | low | 3/3 | 100% | 100% (12/12) | 0.7 | 0.7 | 100% | 100% | 100% | 0.20 | $0.17 | $0.17 | 7 | 20261101T024018Z |
| 4 | Claude Sonnet 5.5 (CC) | medium | 3/3 | 100% | 100% (12/12) | 0.8 | 0.8 | 100% | 100% | 100% | 1.30 | $0.07 | $0.07 | 5 | 20261031T120615Z |
| 5 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 100% (12/12) | 1.1 | 1.1 | 100% | 100% | 100% | 0.22 | $0.25 | $0.25 | 8 | 20261031T123749Z |
| 6 | Claude Opus 5.5 (CC) | high | 3/3 | 100% | 100% (12/12) | 1.6 | 1.6 | 67% | 100% | 100% | 0.15 | $0.36 | $0.36 | 11 | 20261031T183901Z |
| 7 | GLM-5.3 · opencode | medium | 3/3 | 100% | 100% (12/12) | 2.3 | 2.3 | 67% | 100% | 100% | 0.29 | $0.14 | $0.14 | 14 | 20261101T044458Z |
| 8 | Claude Haiku 5.5 (CC) | low | 3/3 | 100% | 100% (12/12) | 2.9 | 2.9 | 0% | 100% | 100% | 2.13 | $0.02 | $0.02 | 16 | 20261101T011617Z |
| 9 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 100% (12/12) | 2.9 | 2.9 | 0% | 100% | 100% | 1.55 | $0.02 | $0.02 | 16 | 20261031T121809Z |
| 10 | Claude Haiku 5.5 (CC) | high | 3/3 | 100% | 100% (12/12) | 5.1 | 5.1 | 0% | 33% | 100% | 1.62 | $0.03 | $0.03 | 24 | 20261031T165728Z |

### r3_oracle_to_postgres — Oracle → PostgreSQL procedures

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Opus 5.5 (CC) | low | 3/3 | 100% | 0.6 | 0.6 | 100% | 100% | 100% | 0.01 | $0.14 | $0.14 | 4 | 20261101T024018Z |
| 2 | Claude Sonnet 5.5 (CC) | medium | 3/3 | 100% | 0.6 | 0.6 | 100% | 100% | 100% | 0.01 | $0.08 | $0.08 | 4 | 20261031T120615Z |
| 3 | Claude Sonnet 5.5 (CC) | low | 3/3 | 100% | 0.7 | 0.7 | 100% | 100% | 100% | 0.01 | $0.10 | $0.10 | 5 | 20261101T003616Z |
| 4 | Claude Haiku 5.5 (CC) | low | 3/3 | 100% | 0.8 | 0.8 | 100% | 100% | 100% | 0.02 | $0.01 | $0.01 | 11 | 20261101T011617Z |
| 5 | Claude Sonnet 5.5 (CC) | high | 3/3 | 100% | 0.8 | 0.8 | 100% | 100% | 100% | 0.01 | $0.11 | $0.11 | 5 | 20261031T160419Z |
| 6 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 1.0 | 1.0 | 100% | 100% | 100% | 0.02 | $0.22 | $0.22 | 4 | 20261031T123749Z |
| 7 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 1.0 | 1.0 | 100% | 100% | 100% | 0.01 | $0.01 | $0.01 | 11 | 20261031T121809Z |
| 8 | Claude Opus 5.5 (CC) | high | 3/3 | 100% | 1.3 | 1.3 | 100% | 100% | 100% | 0.01 | $0.28 | $0.28 | 6 | 20261031T183901Z |
| 9 | Claude Haiku 5.5 (CC) | high | 3/3 | 100% | 1.8 | 1.8 | 67% | 100% | 100% | 0.01 | $0.02 | $0.02 | 14 | 20261031T165728Z |
| 10 | GLM-5.3 · opencode | medium | 3/3 | 100% | 8.9 | 8.9 | 0% | 0% | 67% | 0.08 | $0.64 | $0.64 | 29 | 20261101T044458Z |

### r4_schema_load_optimize — Schema load + query optimization

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | medium | 4/4 | 100% | 0.5 | 0.5 | 100% | 100% | 100% | 0.16 | $0.06 | $0.06 | 4 | 20261031T114732Z, 20261031T120615Z |
| 2 | Claude Sonnet 5.5 (CC) | low | 3/3 | 100% | 0.5 | 0.5 | 100% | 100% | 100% | 0.28 | $0.06 | $0.06 | 5 | 20261101T003616Z |
| 3 | Claude Opus 5.5 (CC) | low | 3/3 | 100% | 0.6 | 0.6 | 100% | 100% | 100% | 0.09 | $0.14 | $0.14 | 3 | 20261101T024018Z |
| 4 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 1.1 | 1.1 | 100% | 100% | 100% | 0.15 | $0.01 | $0.01 | 11 | 20261031T121809Z |
| 5 | Claude Sonnet 5.5 (CC) | high | 3/3 | 100% | 1.1 | 1.1 | 100% | 100% | 100% | 0.22 | $0.11 | $0.11 | 7 | 20261031T160419Z |
| 6 | Claude Haiku 5.5 (CC) | low | 3/3 | 100% | 1.1 | 1.1 | 100% | 100% | 100% | 0.24 | $0.01 | $0.01 | 13 | 20261101T011617Z |
| 7 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 1.2 | 1.2 | 100% | 100% | 100% | 0.14 | $0.25 | $0.25 | 6 | 20261031T123749Z |
| 8 | Claude Opus 5.5 (CC) | high | 3/3 | 100% | 1.5 | 1.5 | 100% | 100% | 100% | 0.12 | $0.31 | $0.31 | 7 | 20261031T183901Z |
| 9 | Claude Haiku 5.5 (CC) | high | 3/3 | 100% | 2.1 | 2.1 | 33% | 100% | 100% | 0.10 | $0.02 | $0.02 | 16 | 20261031T165728Z |
| 10 | GLM-5.3 · opencode | medium | 4/4 | 100% | 9.0 | 9.0 | 0% | 0% | 50% | 0.11 | $0.62 | $0.62 | 22 | 20261101T043154Z, 20261101T044458Z |

### r5_etl_dashboard — ETL job + dashboard schema

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | high | 3/3 | 100% | 0.8 | 0.8 | 100% | 100% | 100% | 0.03 | $0.09 | $0.09 | 4 | 20261031T160419Z |
| 2 | Claude Opus 5.5 (CC) | low | 3/3 | 100% | 0.9 | 0.9 | 100% | 100% | 100% | 0.24 | $0.17 | $0.17 | 5 | 20261101T024018Z |
| 3 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 1.3 | 1.3 | 100% | 100% | 100% | 0.08 | $0.02 | $0.02 | 9 | 20261031T121809Z |
| 4 | Claude Sonnet 5.5 (CC) | medium | 3/3 | 100% | 1.8 | 1.8 | 67% | 100% | 100% | 1.03 | $0.10 | $0.10 | 7 | 20261031T120615Z |
| 5 | Claude Haiku 5.5 (CC) | low | 3/3 | 100% | 2.4 | 2.4 | 33% | 100% | 100% | 1.49 | $0.01 | $0.01 | 11 | 20261101T011617Z |
| 6 | Claude Sonnet 5.5 (CC) | low | 3/3 | 100% | 3.0 | 3.0 | 67% | 67% | 100% | 2.54 | $0.13 | $0.13 | 9 | 20261101T003616Z |
| 7 | Claude Haiku 5.5 (CC) | high | 3/3 | 100% | 3.5 | 3.5 | 0% | 67% | 100% | 0.93 | $0.02 | $0.02 | 13 | 20261031T165728Z |
| 8 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 4.0 | 4.0 | 0% | 67% | 100% | 1.20 | $0.47 | $0.47 | 12 | 20261031T123749Z |
| 9 | Claude Opus 5.5 (CC) | high | 3/3 | 100% | 5.4 | 5.4 | 0% | 67% | 100% | 0.94 | $0.62 | $0.62 | 13 | 20261031T183901Z |
| 10 | GLM-5.3 · opencode | medium | 3/3 | 100% | 9.3 | 9.3 | 0% | 33% | 33% | 0.40 | $0.58 | $0.58 | 26 | 20261101T044458Z |

### r1b_jhipster_boot3 — JHipster app → Spring Boot 3 / Java 17

| # | Model | Thinking level | Passed | Pass rate | Unit tests | Integration tests | E2E tests | Mean time (min) | TTFS (min) | Pass@900s | Pass@1800s | Pass@3600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | low | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 16.1 | 16.1 | 0% | 100% | 100% | 3.17 | $0.99 | $0.99 | 64 | 20261101T005111Z |
| 2 | Claude Opus 5.5 (CC) | medium | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 17.2 | 17.2 | 0% | 100% | 100% | 2.09 | $3.29 | $3.29 | 75 | 20261031T145008Z |
| 3 | Claude Opus 5.5 (CC) | low | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 17.8 | 17.8 | 0% | 100% | 100% | 3.13 | $1.71 | $1.71 | 57 | 20261101T024937Z |
| 4 | Claude Sonnet 5.5 (CC) | medium | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 25.8 | 25.8 | 0% | 100% | 100% | 3.98 | $1.28 | $1.28 | 70 | 20261031T130029Z |
| 5 | Claude Sonnet 5.5 (CC) | high | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 27.8 | 27.8 | 0% | 100% | 100% | 3.73 | $1.39 | $1.39 | 76 | 20261031T161435Z |
| 6 | Claude Haiku 5.5 (CC) | medium | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 28.6 | 28.6 | 0% | 100% | 100% | 1.42 | $1.38 | $1.38 | 131 | 20261031T135411Z |
| 7 | Claude Opus 5.5 (CC) | high | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 31.3 | 31.3 | 0% | 0% | 100% | 1.29 | $5.23 | $5.23 | 98 | 20261031T190847Z |
| 8 | Claude Haiku 5.5 (CC) | low | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 33.2 | 33.2 | 0% | 0% | 100% | 2.45 | $1.25 | $1.25 | 127 | 20261101T013831Z |
| 9 | Claude Haiku 5.5 (CC) | high | 1/1 | 100% | 100% (52/52) | 100% (140/140) | 100% (54/54) | 40.7 | 40.7 | 0% | 0% | 100% | 0.46 | $2.62 | $2.62 | 168 | 20261031T173531Z |
| 10 | GLM-5.3 · opencode | medium | 0/1 | 0% | 100% (52/52) | not run | not run | 48.8 | n/a | 0% | 0% | 0% | 1.08 | $12.26 | n/a | 245 | 20261101T061953Z |

### r2_gwt_to_angular — GWT → Angular port

| # | Model | Thinking level | Passed | Pass rate | E2E tests | Mean time (min) | TTFS (min) | Pass@900s | Pass@1800s | Pass@3600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | low | 1/1 | 100% | 100% (8/8) | 5.5 | 5.5 | 100% | 100% | 100% | 0.63 | $0.68 | $0.68 | 38 | 20261101T005111Z |
| 2 | Claude Sonnet 5.5 (CC) | medium | 1/1 | 100% | 100% (8/8) | 7.9 | 7.9 | 100% | 100% | 100% | 0.53 | $1.01 | $1.01 | 54 | 20261031T133909Z |
| 3 | Claude Opus 5.5 (CC) | medium | 1/1 | 100% | 100% (8/8) | 9.3 | 9.3 | 100% | 100% | 100% | 0.32 | $2.65 | $2.65 | 41 | 20261031T153844Z |
| 4 | Claude Opus 5.5 (CC) | low | 1/1 | 100% | 100% (8/8) | 10.6 | 10.6 | 100% | 100% | 100% | 1.28 | $1.60 | $1.60 | 36 | 20261101T024937Z |
| 5 | Claude Sonnet 5.5 (CC) | high | 1/1 | 100% | 100% (8/8) | 11.5 | 11.5 | 100% | 100% | 100% | 1.35 | $1.10 | $1.10 | 52 | 20261031T161435Z |
| 6 | Claude Haiku 5.5 (CC) | high | 1/1 | 100% | 100% (8/8) | 19.3 | 19.3 | 0% | 100% | 100% | 0.64 | $1.62 | $1.62 | 106 | 20261031T173531Z |
| 7 | Claude Haiku 5.5 (CC) | medium | 1/1 | 100% | 100% (8/8) | 23.9 | 23.9 | 0% | 100% | 100% | 0.73 | $1.91 | $1.91 | 154 | 20261031T135411Z |
| 8 | Claude Haiku 5.5 (CC) | low | 1/1 | 100% | 100% (8/8) | 24.3 | 24.3 | 0% | 100% | 100% | 1.28 | $1.26 | $1.26 | 126 | 20261101T033634Z |
| 9 | Claude Opus 5.5 (CC) | high | 1/1 | 100% | 100% (8/8) | 35.4 | 35.4 | 0% | 0% | 100% | 0.79 | $7.83 | $7.83 | 124 | 20261031T190847Z |
| 10 | GLM-5.3 · opencode | medium | 1/1 | 100% | 100% (8/8) | 35.6 | 35.6 | 0% | 0% | 100% | 1.23 | $9.83 | $9.83 | 218 | 20261101T071035Z |

Unit, integration and E2E tests show how far an attempt got, even when it failed: the share of the hidden suite's tests that passed, summed over the attempts whose suite ran ("not run": the build stopped before that suite, e.g. a failed build check). E2E is the browser suite (Cypress for r1b, the Playwright parity suite for r2). Pass rate stays the official result: an attempt passes only if every check passes.

TTFS is the mean wall time of passing attempts; Pass@T the share of attempts that passed within T seconds (agentic budgets: models.yaml `agentic_time_budgets_s`). Tool / model time divides the time tools ran (builds, tests, servers; parallel calls merged) by the time the model spent in API requests (opencode reports none: there it is the model steps' wall time minus the tool time inside them), summed over attempts that measured both; above 1 means the attempt was mostly waiting on builds and tests (docs/METRICS_PLAN.md §8).

