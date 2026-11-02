# Handoff: re-run r1b for Haiku 5.5 high and GLM-5.3 (2026-11-02)

Written by Claude Code on the Kasm machine for Claude Code on the owner's main
PC (the one that made the earlier agentic runs). Everything needed to do the
re-runs is here; read it top to bottom before running anything.

## Where things are

| What | Where |
|---|---|
| Upstream repo (PRs merge here) | https://github.com/locky-bot2/ai-model-lifecycle, branch `main` |
| Owner's fork (push here) | https://github.com/abralock/ai-model-lifecycle |
| Branch with the fixes | `fix/agentic-sandbox-network-r1b-tests` on the fork (commits `9893ef9` and the one adding this file) |
| Pull request | open it from the fork if it is not open yet: https://github.com/locky-bot2/ai-model-lifecycle/compare/main...abralock:ai-model-lifecycle:fix/agentic-sandbox-network-r1b-tests |
| Code | the repo's git root is `ai-model-lifecycle/`; the project is one level down, in `ai-model-lifecycle/ai-model-lifecycle/` (run every command below from there) |
| Results deck (claude.ai Slides artifact) | https://claude.ai/artifact/NDs6WhZJx789q2iVzfDrVU — "Gate 1 Agentic Results", 32 slides |

## What happened (why these two re-runs)

1. **The agent sandbox had open internet access.** A scan of all 144 agentic
   session logs (`runs/*/agentic/*/*.stream.jsonl`) found two r1b sessions that
   downloaded JHipster's own published Boot 3 version of the app
   (`github.com/jhipster/jhipster-sample-app`, v8.0.0), which is the answer:
   * **GLM-5.3** (opencode, medium), run `20261101T061953Z`: cloned it, diffed it
     file by file and copied ten main-code files, `logback-spring.xml`, many
     test files and plugin versions from it. Its Modernizer 2.7.0 came from that
     pom; our hidden tests call `Optional.get()` 16 times, which 2.7.0 rejects,
     so the scored build stopped before the integration tests (fail).
   * **Haiku 5.5 high** (Claude Code), run `20261031T173531Z`: downloaded the
     v8.0.0 `pom.xml`, three config files and the whole v8.0.0 `src/test` and
     compared against them (pass).
   * Every other session only downloaded libraries (Maven Central), browser
     drivers, or files already in its workspace. Those results stand.
2. **The r1b prompt promised migrated tests that were not there.** The prompt
   says `src/test` is "already migrated to Boot 3", but the workspace held the
   original Boot 2 tests, so all ten r1b agents migrated them to check their
   work. No pass/fail changed (the scorer always swaps in its own suite), but
   it added some time to every r1b run.

## What the branch changes (already done, tested)

* `docker/egress/` (new): an allowlist proxy (tinyproxy). Agent containers
  join the internal network `gate1-sandbox`, whose only way out is the proxy
  `gate1-egress`. Allowed: `api.anthropic.com`, `statsig.anthropic.com`,
  `opencode.ai`, `models.opencode.ai`, `models.dev`, `repo.maven.apache.org`,
  `repo1.maven.org`, `registry.npmjs.org`, `nodejs.org`, `download.cypress.io`,
  `cdn.cypress.io`. Everything else (GitHub included) is refused.
* `agentic.py`: before a batch it starts the network and proxy if missing and
  probes them (Maven allowed, GitHub refused, no direct route); a leak stops
  the batch. Each record gets `network`, `egress_hosts`, `blocked_hosts`.
  Claude Code runs with `--disallowedTools Agent WebFetch WebSearch`.
  `--network open` restores the old behavior (debugging only, never scored).
* `docker/agent/entrypoint.sh`: writes Maven's `~/.m2/settings.xml` with the
  proxy (Maven ignores `*_PROXY`). `docker/agent/Dockerfile`: adds
  `chromium-driver`.
* r1b workspace: `src/test` is now the migrated suite the prompt promises
  (`scorers/fixtures/r1b_hidden_tests`, the one the scorer runs).
* `leaderboard.py` + `runs/EXCLUDED.json`: the two tainted attempts are kept
  as records but not counted; LEADERBOARD.md lists them with the reason.
* `.env.example`: lists `CLAUDE_CODE_OAUTH_TOKEN`.
* Docs: `docs/AGENTIC.md` "Sandbox network".

Verified on the Kasm machine: `pytest` 383 passed, 18 skipped (Postgres not
running there); live Docker checks: Maven Central allowed, GitHub refused
through the proxy and directly; Maven, Claude Code 2.1.316 and opencode 2.2.5
reach their servers through the proxy (fake credentials, 401 replies). **Not
yet verified: a real agent session in the rebuilt `gate1-agent` image.**

## Steps on this PC

Follow the repo's rules (the `gate1-eval` skill): never print `.env`, confirm
with the owner before anything that spends, no commits/pushes without review.

### 1. Get the branch

```bash
cd <your clone>/ai-model-lifecycle            # the git root
git remote add fork https://github.com/abralock/ai-model-lifecycle.git 2>/dev/null
git fetch fork
git checkout -b fix/agentic-sandbox-network-r1b-tests fork/fix/agentic-sandbox-network-r1b-tests
# (or `git checkout main && git pull` once the PR is merged)
cd ai-model-lifecycle                         # the project
```

### 2. Keys in `.env` (gitignored; do not print it)

* `CLAUDE_CODE_OAUTH_TOKEN`: from `claude setup-token` (claude.ai subscription,
  not an API key). Needed for the Haiku re-run.
* `OPENCODE_GO_API_KEY`: opencode.ai/console, Go subscription. Needed for GLM.
  Keep Go's Extra Usage off so a spent quota blocks instead of billing.

### 3. Rebuild both images

```bash
docker build -t gate1-agent:latest docker/agent      # adds chromium-driver
docker build -t gate1-egress:latest docker/egress    # new: the allowlist proxy
```

`docker/agent/Dockerfile` sets `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64`,
fine on an ARM machine (the earlier runs). On x86 it must be `-amd64`.

### 4. Caches and tests

```bash
python -m cases.sources --check                     # pinned project sources
bash cases/r1b_jhipster_boot3/setup_e2e.sh           # no-op if the cache exists
docker compose -f docker/docker-compose.yml up -d    # Postgres for the SQL tests
pytest -q                                            # must pass, nothing skipped
GATE1_SLOW_TESTS=1 pytest -q tests/test_r1b_reference_slow.py   # r1b scorer end to end
```

### 5. Smoke test the locked sandbox (cheap: one small task)

```bash
python agentic.py --pair haiku-5.5-cc-vs-glm-5.3-flash --role current \
    --case r4_schema_load_optimize --effort low --time-limit 1200
```

Expect: the batch prints `network: allowlist`, the attempt passes. In its
record (`runs/haiku-5.5-cc-vs-glm-5.3-flash/agentic/<run>/*.json`):
`"network": "allowlist"`, `egress_hosts` contains `api.anthropic.com`,
`blocked_hosts` is empty or only harmless hosts. If the probe fails, or the
session cannot reach a service it needs, read the proxy log
(`docker logs gate1-egress`) and fix the allowlist before going on. This
attempt is a smoke test; it adds one r4 attempt to Haiku low's row, as
earlier smoke tests did for Sonnet medium and GLM-5.3. If that is unwanted,
add its record to `runs/EXCLUDED.json` with the reason "smoke test".

### 6. The two re-runs (same settings as the originals; ask the owner first)

Originals: Haiku 5.5, role `current` of `haiku-5.5-cc-vs-glm-5.3-flash`,
effort `high`, 3600 s; GLM-5.3, role `target` of `opus-5.5-cc-vs-glm-5.3`,
effort `medium`, 3600 s. One attempt each, as for every r1b row.

```bash
# Haiku 5.5 high (Claude subscription; the original took 40.7 min)
python agentic.py --pair haiku-5.5-cc-vs-glm-5.3-flash --role current \
    --case r1b_jhipster_boot3 --effort high --repeats 1 --time-limit 3600

# GLM-5.3 medium (OpenCode Go; the original cost $12.26 at Go list price)
python agentic.py --pair opus-5.5-cc-vs-glm-5.3 --role target \
    --case r1b_jhipster_boot3 --effort medium --repeats 1 --time-limit 3600 \
    --max-spend-usd 15
```

### 7. Check each result

* Record: `passed`, `reason`, `checks`, and `blocked_hosts`. A refused GitHub
  host means the agent tried to fetch the answer again and was stopped; note
  it. `egress_hosts` with `registry.npmjs.org`: look at the stream log for
  `generator-jhipster` (it ships JHipster 8 templates; the one known gap).
* Search the stream log for `github`, `jhipster-sample-app`, `v8.0.0`.
* A fail: find the cause in the stream log and the scorer's `details` before
  reporting it (as on the deck's GLM slide).

### 8. Leaderboard

```bash
python leaderboard.py
```

`runs/LEADERBOARD.md` should list the two excluded attempts at the top of the
agentic section, and the Haiku high and GLM-5.3 rows should now count only the
new r1b attempt (Runs column: the new run id).

### 9. Commit the results

New branch from the updated main (or this branch), the new
`runs/*/agentic/<run>/` folders and `runs/LEADERBOARD.md`; push to the fork
and open a PR into `locky-bot2/ai-model-lifecycle` `main`, as usual. Do not
commit `.env`.

## Then update the deck

Deck: https://claude.ai/artifact/NDs6WhZJx789q2iVzfDrVU (a claude.ai Slides
artifact; edit it with the Artifact tool: read `project/slides/<id>.html`,
change, publish to the same URL). The two rows carry a † "r1b result under
review … re-run pending" today. Replace them with the new results:

| Slide | id | Change |
|---:|---|---|
| 1 | `cover` | the "141 of 142 … two r1b results under review" stat and notes |
| 7 | `ranking` | Haiku high and GLM rows (time, cost, pass); drop the †; footer |
| 8 | `real-projects` | Haiku high r1b time/turns/cost; footer |
| 9 | `thinking-level` | Haiku high bars if its total changes; footer |
| 11, 12 | `trust`, `caveats` | item 9 / "Fixed · open internet": say the re-runs are done |
| 16 | `glm-real` | the r1b card and notes: the new result |
| 17 | `recommendation` | the "Next: re-run r1b" item becomes "Done" |
| 18, 23, 28, 29, 32 | `r1b-example`, `backup-ranking`, `backup-r1b`, `backup-r1b-2`, `backup-runs` | copy the new LEADERBOARD.md values; drop the † |

Note on every changed slide that the two re-runs used the new setup (no
internet, migrated tests in the workspace), so their r1b times are not
strictly comparable with the other rows' (those agents also spent time
migrating the tests). Pass/fail is comparable.
