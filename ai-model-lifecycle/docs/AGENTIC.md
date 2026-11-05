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
   commands never touch the host. The sandbox has **no internet of its own**:
   see [Sandbox network](#sandbox-network).
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

## Sandbox network

The sandbox reaches only what a migration needs: the model APIs and the
package registries. Agent containers join `gate1-sandbox`, an internal Docker
network with no route to the internet; the only way out is `gate1-egress`, a
small proxy (tinyproxy, `docker/egress/`) that forwards to the hosts in
`docker/egress/allowlist.txt` and refuses everything else:

| Allowed | Why |
|---|---|
| `api.anthropic.com`, `statsig.anthropic.com` | Claude Code |
| `opencode.ai`, `models.opencode.ai`, `models.dev` | opencode on OpenCode Go (API, model catalog) |
| `repo.maven.apache.org`, `repo1.maven.org` | Maven dependencies and plugins |
| `registry.npmjs.org`, `nodejs.org` | npm packages; the Node that JHipster's build installs |
| `download.cypress.io`, `cdn.cypress.io` | the Cypress binary |

GitHub and every other code host or website are refused. Both agents also run
without their web tools: Claude Code with `--disallowedTools Agent WebFetch
WebSearch`, opencode with the `webfetch` and `websearch` permissions denied
(`OPENCODE_DENIED_ACTIONS`). opencode's `webfetch` runs inside the sandbox, so
the proxy refused it anyway; its `websearch` may run through opencode's own
servers, which are allowed, so it had to be switched off.

**The agents are told, too.** Every agent's system text (`SYSTEM_NOTE`) says
what the sandbox reaches, that the registries are for dependencies only, and
that a published solution, a newer version of the project, or the generator or
templates it was made from are off-limits from any source, npm included. r1b's
task note names `jhipster-sample-app` (other versions) and `generator-jhipster`.
Before this the rule was only enforced, never stated (see Residual risk).

* **Why.** Until 2026-11-01 the sandbox was open. On r1b two agents
  (GLM-5.3 and Haiku 5.5 at high) downloaded JHipster's own published Boot 3
  version of the app, i.e. the answer; GLM-5.3 copied files and build-plugin
  versions from it. Those r1b results do not count.
* **Checked before every batch.** `agentic.py` starts the network and proxy
  if missing, then probes from a sandbox container: Maven Central must answer
  through the proxy, GitHub must be refused, and nothing may get out without
  the proxy. A failed probe stops the batch before anything is spent.
* **Recorded per attempt.** Each record carries `network`, `egress_hosts`
  (hosts the proxy let through) and `blocked_hosts` (hosts it refused); a
  refused host is printed as the batch runs.
* **Clients.** curl, git, npm, Node and both agents read the `*_PROXY`
  variables; the entrypoint writes Maven's `~/.m2/settings.xml` (Maven reads
  no proxy variables). `localhost` stays direct, so builds and tests reach
  their own servers.
* **Residual risk.** npm hosts `generator-jhipster`, whose templates describe
  a JHipster 8 app; `egress_hosts` shows whether an attempt used the npm
  registry at all (r1b and r2 ship with node_modules installed). GLM-5.3's
  r1b re-run of 2026-11-02 read those templates when GitHub was refused, so
  the agents are now told (above); the proxy cannot tell a dependency from a
  template, so this rule is stated and checked in the logs, not enforced.
* **Debugging only:** `--network open` puts the sandbox on Docker's default
  bridge (the old behavior). Never use it for a scored run; records say
  `"network": "open"`.

One-time setup: `docker build -t gate1-egress:latest docker/egress` (and
rebuild `gate1-agent` for `chromium-driver`, which agents used to download).

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
| No sub-agents, no web tools | `--disallowedTools Agent WebFetch WebSearch` | permissions `subagent`, `webfetch`, `websearch`: deny |
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
| r1b JHipster → Boot 3 | the whole app at the pinned commit, node_modules installed, with `src/test/java` and `src/test/resources` replaced by the already-migrated suite its prompt promises (the one the scorer runs; since 2026-11-02, before that the original Boot 2 tests); the Cypress suite in `src/test/javascript` stays (on 2026-11-02 itself it was deleted by mistake, and both re-runs restored it from git) | ./mvnw, Cypress (Chromium) | pom.xml, src/main/java, src/main/resources |
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

### Separate tracks (`--track`)

An experiment that must not mix with the main board runs as a track:

```bash
python agentic.py --pair sonnet-5.5-cc-vs-deepseek-v4-pro --role current --effort low \
    --case r1b_jhipster_boot3 --time-limit 600 --track r1b-10min --tell-time-limit
python leaderboard.py --track r1b-10min      # writes runs/LEADERBOARD_r1b-10min.md
```

* Each record carries `track`; `runs/LEADERBOARD.md` never counts a track's
  attempts, and a track's board counts only its own.
* `--tell-time-limit` adds to the agent's system text: "Time limit: you have
  N minutes. The session is then stopped, and whatever is in /work at that
  moment is scored as it stands." Without it the prompt never mentions the
  limit (the main board's setting).
* The track board ranks by pass rate, then by how far an attempt got: the
  share of the scorer's acceptance checks passed (r1b: edits applied, Boot 3,
  Java 17, no javax, build, unit, integration, E2E), then hidden tests passed,
  then time and cost. It lists the checks that failed, whether each attempt
  was stopped at the limit, and mean input and output tokens.
* First track, `r1b-10min` (2026-11-05): r1b with a 10-minute limit the agent
  is told about, at the peers' request (are faster models better when time is
  short?).

### Tokens and cost of a session stopped at the time limit

Claude Code reports cost, API time and total output tokens only in the result
event it writes when a session ends; a session the time limit stops has none.
So, for a stopped Claude Code session:

* **Turns and input tokens** come from the stream: one id per model reply,
  and each reply's input, cache-read and cache-write tokens, which match the
  result event exactly (checked on the 60-minute r1b runs).
* **Output tokens** come from Claude Code's own session record, copied out of
  the container just before it is stopped (`ClaudeCodeBackend.save_session`,
  kept as `<record>.session.jsonl`, secrets redacted). The stream logs each
  reply's output count before the reply is finished (a 90-second test: 164 in
  the stream against 14,675 in the record), so it is never used. The sandbox
  therefore runs Claude Code without `--no-session-persistence`; the
  container is removed after each attempt, so nothing outlives it.
* **Cost and API time** stay unknown (n/a). A session that wrote a result
  event and then resumed before being stopped is treated the same way, so a
  partial running total is never reported as the session's.

opencode reports tokens and cost per step, so its stopped sessions are complete.

## Limits

* Agentic attempts take tens of minutes each and use the subscription's usage
  limit (Claude) or the Go quota (opencode); run one task with `--case` before a
  full sweep.
* Not yet observed: opencode's `/goal` re-prompting an agent that stopped before
  the goal was met (the first smoke test finished on its first stop).
* Binary deliverables (such as images) travel base64-encoded as `### BINARY:` blocks.
* A delivered file that itself contains a Markdown fence line cannot travel
  through the FILE-block answer intact (code, SQL and config files never do).
