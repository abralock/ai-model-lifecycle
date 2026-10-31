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
2. **Sandbox.** Claude Code runs in a throwaway Docker container
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
plus its full Claude Code stream, `.stream.jsonl`). `leaderboard.py` ranks
agentic results first: pass rate per task, mean time, TTFS, Pass@T (agentic
budgets), tool / model time, mean cost, cost per pass and turns
(docs/METRICS_PLAN.md §8). Pass/fail is re-scored through the score cache, so a scorer fix
reaches earlier attempts.

## Limits

* Claude Code models only for now; open-weight models need their own agent
  (e.g. OpenCode) to take the same test.
* Agentic attempts take tens of minutes each and use the subscription's usage
  limit; run one task with `--case` before a full sweep.
* Binary deliverables (such as images) travel base64-encoded as `### BINARY:` blocks.
* A delivered file that itself contains a Markdown fence line cannot travel
  through the FILE-block answer intact (code, SQL and config files never do).
