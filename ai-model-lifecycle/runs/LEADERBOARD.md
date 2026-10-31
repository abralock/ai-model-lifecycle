# Gate 1 leaderboard

> Generated: 2026-10-31T15:56:10+00:00 · live scoring: on (score cache)  
> Routes: Claude Code, OpenCode Go (OpenRouter left out; `--routes all` includes it)  
> Results: from run 20261031T114732Z on · agentic runs only (single-shot screening is in each pair's REPORT.md; `--all-results` shows it here)

# Agentic migration (primary result)

The model works on a copy of the project in a sandbox with Claude Code, the way a developer would: it changes code, builds, runs the tests and fixes what fails, until its goal is met or the time limit is hit (agentic.py). What it delivered is then checked by the same acceptance test as single-shot, including hidden tests it never saw. Infra errors (sessions that never ran) are excluded.

## Ranking

Models that tried every task rank first. Time is the agent's wall-clock time per attempt; cost is Claude Code's estimate at API list prices.

| # | Model | Thinking level | Sanity passed | Real passed | Overall pass rate | Tasks tried |
|---:|---|---|---:|---:|---:|---:|
| 1 | Claude Haiku 5.5 (CC) | medium | 12/12 | 2/2 | 100% (14/14) | 6/6 |
| 2 | Claude Opus 5.5 (CC) | medium | 12/12 | 2/2 | 100% (14/14) | 6/6 |
| 3 | Claude Sonnet 5.5 (CC) | medium | 13/13 | 2/2 | 100% (15/15) | 6/6 |

### r1_springboot2to3 — Spring Boot 2 → 3 (small app)

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | medium | 3/3 | 100% | 0.8 | 0.8 | 100% | 100% | 100% | 1.30 | $0.07 | $0.07 | 5 | 20261031T120615Z |
| 2 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 1.1 | 1.1 | 100% | 100% | 100% | 0.22 | $0.25 | $0.25 | 8 | 20261031T123749Z |
| 3 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 2.9 | 2.9 | 0% | 100% | 100% | 1.55 | $0.02 | $0.02 | 16 | 20261031T121809Z |

### r3_oracle_to_postgres — Oracle → PostgreSQL procedures

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | medium | 3/3 | 100% | 0.6 | 0.6 | 100% | 100% | 100% | 0.01 | $0.08 | $0.08 | 4 | 20261031T120615Z |
| 2 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 1.0 | 1.0 | 100% | 100% | 100% | 0.02 | $0.22 | $0.22 | 4 | 20261031T123749Z |
| 3 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 1.0 | 1.0 | 100% | 100% | 100% | 0.01 | $0.01 | $0.01 | 11 | 20261031T121809Z |

### r4_schema_load_optimize — Schema load + query optimization

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | medium | 4/4 | 100% | 0.5 | 0.5 | 100% | 100% | 100% | 0.16 | $0.06 | $0.06 | 4 | 20261031T114732Z, 20261031T120615Z |
| 2 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 1.1 | 1.1 | 100% | 100% | 100% | 0.15 | $0.01 | $0.01 | 11 | 20261031T121809Z |
| 3 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 1.2 | 1.2 | 100% | 100% | 100% | 0.14 | $0.25 | $0.25 | 6 | 20261031T123749Z |

### r5_etl_dashboard — ETL job + dashboard schema

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@120s | Pass@300s | Pass@600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Haiku 5.5 (CC) | medium | 3/3 | 100% | 1.3 | 1.3 | 100% | 100% | 100% | 0.08 | $0.02 | $0.02 | 9 | 20261031T121809Z |
| 2 | Claude Sonnet 5.5 (CC) | medium | 3/3 | 100% | 1.8 | 1.8 | 67% | 100% | 100% | 1.03 | $0.10 | $0.10 | 7 | 20261031T120615Z |
| 3 | Claude Opus 5.5 (CC) | medium | 3/3 | 100% | 4.0 | 4.0 | 0% | 67% | 100% | 1.20 | $0.47 | $0.47 | 12 | 20261031T123749Z |

### r1b_jhipster_boot3 — JHipster app → Spring Boot 3 / Java 17

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@900s | Pass@1800s | Pass@3600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Opus 5.5 (CC) | medium | 1/1 | 100% | 17.2 | 17.2 | 0% | 100% | 100% | 2.09 | $3.29 | $3.29 | 75 | 20261031T145008Z |
| 2 | Claude Sonnet 5.5 (CC) | medium | 1/1 | 100% | 25.8 | 25.8 | 0% | 100% | 100% | 3.98 | $1.28 | $1.28 | 70 | 20261031T130029Z |
| 3 | Claude Haiku 5.5 (CC) | medium | 1/1 | 100% | 28.6 | 28.6 | 0% | 100% | 100% | 1.42 | $1.38 | $1.38 | 131 | 20261031T135411Z |

### r2_gwt_to_angular — GWT → Angular port

| # | Model | Thinking level | Passed | Pass rate | Mean time (min) | TTFS (min) | Pass@900s | Pass@1800s | Pass@3600s | Tool / model time | Mean cost | Cost / pass | Mean turns | Runs |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | medium | 1/1 | 100% | 7.9 | 7.9 | 100% | 100% | 100% | 0.53 | $1.01 | $1.01 | 54 | 20261031T133909Z |
| 2 | Claude Opus 5.5 (CC) | medium | 1/1 | 100% | 9.3 | 9.3 | 100% | 100% | 100% | 0.32 | $2.65 | $2.65 | 41 | 20261031T153844Z |
| 3 | Claude Haiku 5.5 (CC) | medium | 1/1 | 100% | 23.9 | 23.9 | 0% | 100% | 100% | 0.73 | $1.91 | $1.91 | 154 | 20261031T135411Z |

TTFS is the mean wall time of passing attempts; Pass@T the share of attempts that passed within T seconds (agentic budgets: models.yaml `agentic_time_budgets_s`). Tool / model time divides the time tools ran (builds, tests, servers; parallel calls merged) by the time the model spent in API requests, summed over attempts that measured both; above 1 means the attempt was mostly waiting on builds and tests (docs/METRICS_PLAN.md §8).

