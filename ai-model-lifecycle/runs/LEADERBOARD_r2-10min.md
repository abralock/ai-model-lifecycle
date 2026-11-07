# Separate board: r2-10min

> Generated: 2026-11-06T13:52:16+00:00. A separate track (agentic.py `--track r2-10min`): these attempts are never counted in `runs/LEADERBOARD.md`, and the main board's attempts are never counted here.

Time limit: 10 min (stated in the prompt). When the limit is hit the session is stopped and what is in the workspace is scored as it stands, with the same scorer and hidden tests as the main board.

Ranked by pass rate, then by how far the attempt got: the share of the scorer's acceptance checks that passed, then hidden tests passed, then time and cost.

## r2_gwt_to_angular — GWT → Angular port

| # | Model | Thinking level | Passed | Checks passed | Checks failed | Integration tests | E2E tests | Mean time (min) | Stopped at limit | Mean cost | Input tokens | Output tokens | Mean turns | Runs |
|---:|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Claude Sonnet 5.5 (CC) | medium | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 5.0 | 0/1 | $0.60 | 1.6M | 17k | 34 | 20261106T122251Z |
| 2 | Claude Haiku 5.5 (CC) | medium | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 5.8 | 0/1 | $0.30 | 4.1M | 44k | 50 | 20261106T131734Z |
| 3 | Claude Opus 5.5 (CC) | low | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 7.3 | 0/1 | $1.47 | 2.0M | 23k | 42 | 20261106T124033Z |
| 4 | Claude Haiku 5.5 (CC) | low | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 7.7 | 0/1 | $0.25 | 4.3M | 51k | 61 | 20261106T130903Z |
| 5 | Claude Opus 5.5 (CC) | high | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 8.0 | 0/1 | $1.51 | 1.9M | 29k | 36 | 20261106T130007Z |
| 6 | Claude Sonnet 5.5 (CC) | low | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 9.2 | 0/1 | $0.83 | 2.6M | 21k | 54 | 20261106T121208Z |
| 7 | GLM-5.3 · opencode | medium | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 10.0 | 1/1 | $1.03 | 1.9M | 53k | 40 | 20261106T133442Z |
| 8 | Claude Opus 5.5 (CC) | medium | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 10.0 | 1/1 | ≈ $1.31 | 1.9M | 25k | 38 | 20261106T124904Z |
| 9 | Claude Haiku 5.5 (CC) | high | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 10.0 | 1/1 | ≈ $0.35 | 5.6M | 71k | 57 | 20261106T132401Z |
| 10 | Claude Sonnet 5.5 (CC) | high | 1/1 | 100% (5/5) | none | 100% (7/7) | 100% (8/8) | 10.0 | 1/1 | ≈ $1.07 | 3.7M | 35k | 54 | 20261106T122830Z |

Checks passed: the scorer's acceptance checks (r2_gwt_to_angular, 5: edits applied, Angular app present, production build, the UI parity suite (Playwright), the UI-vs-REST-API integration suite), summed over attempts; a pass needs all of them. Hidden test columns as on the main board ("not run": the build stopped before that suite). Cost: Claude Code reports cost only when its session ends, so a Claude attempt stopped at the limit is priced from its session record instead (≈: every request at Anthropic API list prices, pricing.py; these reproduce Claude Code's own figure for finished sessions; attempts without a record: n/a); opencode reports it per step. Tokens are means per attempt: input counts fresh input plus cache reads and cache writes (an agent re-reads its context every turn, so it is mostly cache reads); output includes thinking. For a Claude attempt stopped at the limit, input tokens come from each model reply and output tokens from Claude Code's session record, copied out before the stop (attempts from 2026-11-05 22:47 on; earlier ones have no record, so output is n/a). Turns for a stopped Claude attempt are its model replies.
