# Passdown: r1b in 10 minutes, two runs on their own boards (2026-11-05/06)

Written by Claude Code on the owner's home PC (the one that runs the agentic
batches), for whoever picks this up next: the owner, a peer, or another Claude
Code session. Read it top to bottom before re-running anything.

## Where things are

| What | Where |
|---|---|
| Pull request | https://github.com/locky-bot2/ai-model-lifecycle/pull/59 (branch `feature/r1b-10min-board` on the fork `abralock/ai-model-lifecycle`, from `main` at `827ec39`) |
| Run 1 board | `runs/LEADERBOARD_r1b-10min.md` (10 attempts: 9 Claude rows + GLM-5.3) |
| Run 2 board | `runs/LEADERBOARD_r1b-10min-run2.md` (9 attempts: the 9 Claude rows again) |
| Main board | `runs/LEADERBOARD.md`, **unchanged**: never counts a track's attempts |
| Records | `runs/<pair>/agentic/20261105T1*/`: per attempt a record `.json`, the agent's `.stream.jsonl` and, for run 2's stopped Claude sessions, Claude Code's `.session.jsonl` |
| Deck | https://claude.ai/artifact/NDs6WhZJx789q2iVzfDrVU ("Gate 1 Agentic Results", private): slide 36 finding, 37 table with tokens, 38–41 raw data of both boards, 19 next steps updated |
| How it works | `docs/AGENTIC.md`, sections "Separate tracks" and "Tokens and cost of a session stopped at the time limit" |
| Related, still open | PR #58, `docs/R1B_NEXT_PLAN.md`: a harder, less memorizable successor to r1b (the manager's "r1b seems easy") |

## Why

Every model passes r1b in the 60-minute run, so pass/fail no longer separates
them. Peers suggested the same real task with a 10-minute limit. The owner
asked for the result as a **separate leaderboard**, never mixed with the main
board, and then for a second run as **another separate board**, not pooled
with the first. Peers also asked for **token spend** in the result table.

## What was built (PR #59)

* `agentic.py --track NAME`: each record carries `track`. The main board skips
  every attempt with a track; `leaderboard.py --track NAME` counts only that
  track's attempts and writes `runs/LEADERBOARD_<NAME>.md`.
* `agentic.py --tell-time-limit`: adds to the agent's system text "Time limit:
  you have N minutes. The session is then stopped, and whatever is in /work at
  that moment is scored as it stands." The main board's prompt never mentions
  the limit.
* The track board ranks by pass rate, then share of the scorer's 8 acceptance
  checks passed, then hidden tests passed, then time and cost, and shows
  checks failed, unit/integration/E2E, stopped at limit, cost, input tokens,
  output tokens, turns and the run id.
* Token spend for sessions the time limit stops (Claude Code writes cost, API
  time and output totals only in its final result event, which a stopped
  session never writes):
  * turns and input/cache tokens: from each model reply in the stream (exact,
    checked against the 60-minute runs);
  * output tokens: from Claude Code's own session record, copied out of the
    still-running container just before the stop. The stream's per-reply
    output counts are logged before the reply finishes (a 90-second test: 164
    in the stream against 14,675 in the record) and are never used. For this
    the sandbox no longer passes `--no-session-persistence` (the container is
    removed after each attempt anyway);
  * cost and API time: n/a.
* The score cache now also keeps each answer's checks (scorer fingerprint
  unchanged: nothing was re-scored on the main board).

## Results

r1b (JHipster app to Spring Boot 3 / Java 17), 10-minute limit the agents were
told about, locked sandbox, one attempt per model and thinking level per run.

| Row | Run 1 | Run 2 |
|---|---|---|
| Opus 5.5 low | pass | 7/8, E2E failed |
| Opus 5.5 medium | 7/8, E2E | 7/8, E2E |
| Opus 5.5 high | 7/8, E2E | pass, finished itself at 7.6 min ($1.14 API price) |
| Sonnet 5.5 low | 7/8, E2E | 7/8, E2E |
| Sonnet 5.5 medium | pass | 7/8, E2E |
| Sonnet 5.5 high | 7/8, E2E | pass |
| Haiku 5.5 low / medium / high | 7/8, E2E ×3 | 7/8, E2E ×3 |
| GLM-5.3 (opencode) | 4/8, build fails, $1.59 Go credit | not run |

* **Every Claude attempt finishes the Java migration in 10 minutes**: Boot 3,
  Java 17, no javax, the build, all 52 unit and 140 integration tests.
* **Who passes is close to chance**: 2 of 9 Claude rows passed in each run, 4
  different rows, none passed both. Not a ranking; it does not change the
  deck's recommendation (low thinking for Sonnet and Opus).
* **All 14 Claude E2E failures are genuine**, each checked in the scorer's
  details: 7 times the app refused to start on a setting JHipster 8 no longer
  binds (`jhipster.logging.logstash.queue-size`; the tests don't load it, the
  real app does); 4 times it set up its database but never opened its web port
  in 4 minutes (the health check got connection refused, not an error
  status); 3 times it started but answered 401 for `/` (security config locks
  anonymous users out of the UI).
* **Tokens (run 2)**: Opus low used the fewest (754k input, 8.7k output);
  Haiku 3–4× that (2.3–3.2M input, 24–35k output). Input is mostly cache
  reads. Run 1 has input tokens only (it predates the session-record fix).
* **Clean**: no command in any of the 19 attempts touched GitHub,
  `jhipster-sample-app`, `generator-jhipster`, v8.0.0 or npm package lookups.
  Refused hosts were Chrome's own background requests and opencode's startup
  request to github.com.
* Spend: GLM-5.3 $1.59 of Go credit; Claude rows on the subscription (about
  2½ hours of attempts per run).

## How to re-run or extend

From the project folder (`ai-model-lifecycle/ai-model-lifecycle`), Docker
Desktop running (the r1 scorer tests and every r1b score need it):

```bash
# one row of a new run, on its own board (pick a new track name per run)
python agentic.py --pair sonnet-5.5-cc-vs-deepseek-v4-pro --role current --effort low \
    --case r1b_jhipster_boot3 --repeats 1 --time-limit 600 \
    --track r1b-10min-run3 --tell-time-limit
python leaderboard.py --track r1b-10min-run3     # runs/LEADERBOARD_r1b-10min-run3.md
```

Pairs and roles for the 9 Claude rows: `sonnet-5.5-cc-vs-deepseek-v4-pro`,
`opus-5.5-cc-vs-kimi-k3`, `haiku-5.5-cc-vs-glm-5.3-flash`, all role `current`,
effort `low`/`medium`/`high`. GLM-5.3: `--pair opus-5.5-cc-vs-glm-5.3 --role
target --effort medium --max-spend-usd 5` (Go credit; ask the owner first).

## Gotchas

* **Run attempts one at a time.** With a hard 10-minute clock, a second batch
  or a re-score running beside it slows the agent and changes the result.
* **Scoring a failing r1b attempt takes about 5–8 minutes**: the scorer waits
  the full 240 s for an app that already crashed. A full re-score of 9–10
  attempts is 45–60 minutes.
* **Output tokens need the session record.** It exists only for attempts run
  with the PR #59 code (from 2026-11-05 22:47 on). Older stopped sessions
  cannot be recovered: their output and cost stay n/a.
* **Claude cost for a stopped session is n/a by design**; don't estimate it
  from `pricing.py`: its table disagrees with Claude Code's own figures by up
  to 5× on the 5.5 models (an open issue, not fixed here).
* Haiku low's run-1 cost ($0.06) is what Claude Code reported when its session
  paused just before the stop; it looks low for 2.7M input tokens.
* Run 2 was first written with `track: r1b-10min` and moved to
  `r1b-10min-run2` afterwards (records with run id ≥ `20261105T144700Z`), at
  the owner's request to keep the runs on separate boards.
* `.claude/settings.local.json` at the repo root (git-ignored) holds allow
  rules added on 2026-11-05 so the overnight commit, push and deck publish
  would not stop for approval. Remove it if no longer wanted.

## Open items

1. Review and merge PR #59 (and PR #58, the r1b successor plan).
2. Decide whether the 10-minute track is worth more runs: with 1 attempt per
   row, pass/fail at 10 minutes is close to chance. Three or more runs per row
   would show whether any row passes reliably.
3. The successor task (PR #58): a disguised or private app, so the result is
   not memorization.
4. Share the deck from its Share menu when it should reach the peers.
