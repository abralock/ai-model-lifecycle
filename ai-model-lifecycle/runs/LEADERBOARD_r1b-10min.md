# Separate board: r1b-10min

> Generated: 2026-11-06T11:35:31+00:00. A separate track (agentic.py `--track r1b-10min`): these attempts are never counted in `runs/LEADERBOARD.md`, and the main board's attempts are never counted here.

Time limit: 10 min (stated in the prompt). When the limit is hit the session is stopped and what is in the workspace is scored as it stands, with the same scorer and hidden tests as the main board.

Ranked by pass rate, then by how far the attempt got: the share of the scorer's acceptance checks that passed, then hidden tests passed, then time and cost.

## r1b_jhipster_boot3 — JHipster app → Spring Boot 3 / Java 17

| # | Model | Thinking level | Passed | Checks passed | Checks failed | Unit tests | Integration tests | E2E tests | Mean time (min) | Stopped at limit | Mean cost | Input tokens | Output tokens | Mean turns | Runs |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Opus 5.5 (CC) | low | 1/1 | 100% (8/8) | none | 100% (52/52) | 100% (140/140) | 100% (54/54) | 10.0 | 1/1 | n/a | 900k | n/a | 27 | 20261105T121013Z |
| 2 | Claude Sonnet 5.5 (CC) | medium | 1/1 | 100% (8/8) | none | 100% (52/52) | 100% (140/140) | 100% (54/54) | 10.0 | 1/1 | n/a | 2.3M | n/a | 42 | 20261105T114202Z |
| 3 | Claude Opus 5.5 (CC) | medium | 0/1 | 88% (7/8) | e2e | 100% (52/52) | 100% (140/140) | not run | 10.0 | 1/1 | n/a | 1.1M | n/a | 26 | 20261105T122300Z |
| 4 | Claude Haiku 5.5 (CC) | low | 0/1 | 88% (7/8) | e2e | 100% (52/52) | 100% (140/140) | not run | 10.0 | 1/1 | $0.06 | 2.7M | 20k | 50 | 20261105T125359Z |
| 5 | Claude Sonnet 5.5 (CC) | high | 0/1 | 88% (7/8) | e2e | 100% (52/52) | 100% (140/140) | not run | 10.0 | 1/1 | n/a | 2.2M | n/a | 33 | 20261105T115445Z |
| 6 | Claude Haiku 5.5 (CC) | medium | 0/1 | 88% (7/8) | e2e | 100% (52/52) | 100% (140/140) | not run | 10.0 | 1/1 | n/a | 1.8M | n/a | 40 | 20261105T130930Z |
| 7 | Claude Haiku 5.5 (CC) | high | 0/1 | 88% (7/8) | e2e | 100% (52/52) | 100% (140/140) | not run | 10.0 | 1/1 | n/a | 2.1M | n/a | 39 | 20261105T132459Z |
| 8 | Claude Sonnet 5.5 (CC) | low | 0/1 | 88% (7/8) | e2e | 100% (52/52) | 100% (140/140) | not run | 10.0 | 1/1 | n/a | 1.1M | n/a | 28 | 20261105T112623Z |
| 9 | Claude Opus 5.5 (CC) | high | 0/1 | 88% (7/8) | e2e | 100% (52/52) | 100% (140/140) | not run | 10.0 | 1/1 | n/a | 923k | n/a | 27 | 20261105T123829Z |
| 10 | GLM-5.3 · opencode | medium | 0/1 | 50% (4/8) | build, unit_tests, integration_tests, e2e | not run | not run | not run | 10.0 | 1/1 | $1.59 | 3.6M | 56k | 48 | 20261105T134031Z |

Checks passed: the scorer's acceptance checks (for r1b: edits applied, Spring Boot 3, Java 17, no javax imports, build, unit tests, integration tests, E2E), summed over attempts; a pass needs all of them. Hidden test columns as on the main board ("not run": the build stopped before that suite). Cost: Claude Code reports cost only when its session ends, so a Claude attempt stopped at the limit is priced from its session record instead (≈: every request at Anthropic API list prices, pricing.py; these reproduce Claude Code's own figure for finished sessions; attempts without a record: n/a); opencode reports it per step. Tokens are means per attempt: input counts fresh input plus cache reads and cache writes (an agent re-reads its context every turn, so it is mostly cache reads); output includes thinking. For a Claude attempt stopped at the limit, input tokens come from each model reply and output tokens from Claude Code's session record, copied out before the stop (attempts from 2026-11-05 22:47 on; earlier ones have no record, so output is n/a). Turns for a stopped Claude attempt are its model replies.
