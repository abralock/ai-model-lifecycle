# Agentic migration

In Gate 1, *migration* means what it means on a real project: the AI changes the
code, builds it, runs the tests, reads what fails and fixes it, until the project
delivers what was asked. `agentic.py` measures exactly that. Single-shot runs
(`runner.py`), where the model writes every change in one reply without building
or testing anything, are kept as a quick screening test only.

Why: on the real JHipster project (r1b) every model scored 0% single-shot, while
Sonnet 5.5 working in Claude Code with `/goal` delivered a passing migration in
29 minutes (build, 52 unit, 140 integration and 54 Cypress tests).

## How an attempt runs

1. **Workspace.** The case's starting project is copied into a fresh folder
   (`.agentic-work/`, deleted afterwards). Only task inputs go in: answer keys
   (`golden_postgres.sql`) and the hidden acceptance tests never do.
2. **Sandbox.** The agent runs in a throwaway Docker container
   (`docker/agent/Dockerfile`) with Java 17 + Maven, Java 8 (r2's original App
   Engine backend), Node 20 + Chromium and PostgreSQL 17. The workspace is the
   only mount it can write; dependency caches are named volumes. Model-run
   commands never touch the host.
3. **Goal.** The prompt is `/goal <condition>` (each case's `goal` in
   `agentic.py`); the task text is the case's `prompt.md` with its reply-format
   section replaced by workspace instructions. Claude Code keeps working until
   its goal check finds the condition met or `--time-limit` (default 3600 s)
   stops the container.
4. **Settings.** No sub-agents (`--disallowedTools Agent`), no MCP servers, no
   user settings; effort from `--effort` or `models.yaml defaults.effort`.
5. **Login.** The container logs in with `CLAUDE_CODE_OAUTH_TOKEN`
   (`claude setup-token`, the claude.ai subscription). It is passed to Docker by
   name from the environment, so it never appears on a command line; no API key
   ever reaches the sandbox.
6. **Scoring.** The files the agent delivered (each case's `deliverables`) become
   a FILE/DELETE answer and the case's scorer checks it exactly as it checks a
   single-shot answer. The agent's own test edits are not part of it: acceptance
   runs our hidden tests.

## Two agents: Claude Code and opencode

Claude models run in **Claude Code** on the claude.ai subscription. Open-weight
models on OpenCode Go (`api: opencode-go` in `models.yaml`: GLM-5.3, GLM-5.3
Flash, DeepSeek V4 Pro, Kimi K3, …) run in **opencode**, pinned to v2.2.5 in the
same image, so both agents get the identical toolchain. `agentic.py` picks the
agent from the model's route; workspace, goal, time limit, harvest and scoring
are shared.

| | Claude Code | opencode |
|---|---|---|
| Login | `CLAUDE_CODE_OAUTH_TOKEN` (subscription) | `OPENCODE_GO_API_KEY`, passed as `OPENCODE_API_KEY` (Go subscription) |
| Goal | `/goal <condition>` on stdin | the same, read by opencode v2's `/goal` |
| Task text | `--append-system-prompt-file` | `instructions` in the per-attempt `/gate1/opencode.json` |
| No sub-agents | `--disallowedTools Agent` | permission `subagent: deny` |
| Isolation | no MCP, no user settings | only the `opencode-go` provider (`provider.use` policy), no MCP, plugins, LSP, formatter, snapshots or project config |
| Thinking level | `--effort` (low … max) | `reasoning_effort` in the build agent's request body (low, medium, high; Go models have no effort variants) |
| Cost | Claude Code's estimate at API list prices | Go list price of the tokens used (`pricing.py`; quota, not a bill) |
| Model time | reported (`duration_api_ms`) | derived: the model steps' wall time minus tool time inside them |

Each agent gets only its own credential, passed by name; any credential
value an agent prints is replaced with `[REDACTED]` before the stream is
saved. An opencode provider error (auth, quota, rate limit, routing, outage)
is an infra error and stops the batch; an error the model causes (e.g.
context overflow) ends a scored attempt and is kept as `agent_error`.
`--max-spend-usd` stops a batch once its estimated spend reaches the cap; for
Go, keep Extra Usage off so a spent quota blocks requests instead of billing.

An opencode row differs from a Claude row in both the model and the agent
(system prompt, tools, goal check), and the leaderboard says so ("· opencode").

## What each task gets

| Task | Workspace | Tools it can use to test | Delivered (scored) |
|---|---|---|---|
| r1 Spring Boot 2 → 3 | the module (pom.xml, src) | Maven, Java 17 | pom.xml, src/** |
| r1b JHipster → Boot 3 | the whole app at the pinned commit, node_modules installed | ./mvnw, Cypress (Chromium) | pom.xml, src/main/java, src/main/resources |
| r2 GWT → Angular | the Angular workspace, `gwt/`, `e2e/` | `ng build`, `sh backend/run.sh` (the original app + REST API on :8888, your build at /ng/) | src/** (the scorer restores the fixed files) |
| r3 Oracle → Postgres | Oracle procedures, seed.sql, the Oracle result sets (`expected/`) | psql | postgres/** |
| r4 Schema + load + index | schema.sql, target_query.sql | psql, EXPLAIN | solution.sql |
| r5 ETL + dashboard | etl_spec.md, dashboard_schema.sql, R4's schema + seeder | psql, python3 | etl.sql |

## Results

Records and a `REPORT.md` go to `runs/<pair>/agentic/<run>/` (one JSON per attempt
plus the agent's full event stream, `.stream.jsonl`). `leaderboard.py` ranks
agentic results first: pass rate per task, mean time, TTFS, Pass@T (agentic
budgets), tool / model time, mean cost, cost per pass and turns
(docs/METRICS_PLAN.md §8). Pass/fail is re-scored through the score cache, so a scorer fix
reaches earlier attempts.

## Limits

* Agentic attempts take tens of minutes each and use the subscription's usage
  limit (Claude) or the Go quota (opencode); run one task with `--case` before a
  full sweep.
* Not yet observed: opencode's `/goal` re-prompting an agent that stopped before
  the goal was met (the first smoke test finished on its first stop).
* Binary deliverables (such as images) travel base64-encoded as `### BINARY:` blocks.
* A delivered file that itself contains a Markdown fence line cannot travel
  through the FILE-block answer intact (code, SQL and config files never do).
