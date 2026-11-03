# Handoff: the agents are told the internet rule; re-run r1b (2026-11-03)

Written by Claude Code on the Kasm machine for Claude Code on the owner's home
PC (the one that runs the agentic batches). Read it top to bottom before
running anything. It follows on from `docs/HANDOFF_R1B_RERUN.md` (2026-11-02).

## Where things are

| What | Where |
|---|---|
| Owner's fork (push here) | https://github.com/abralock/ai-model-lifecycle |
| Branch with the changes | `fix/agentic-prompt-rules` (from `main` at `66aad94`, PR #55) |
| Code | the repo's git root is `ai-model-lifecycle/`; the project is one level down, in `ai-model-lifecycle/ai-model-lifecycle/` (run every command below from there) |
| Results deck (claude.ai Slides artifact) | https://claude.ai/artifact/NDs6WhZJx789q2iVzfDrVU — "Gate 1 Agentic Results" (private; slides 5, 6, 12, 13, 18 and backup 35 are the relevant ones) |

## Why (what the owner's manager asked for)

On 2026-11-02 the sandbox was locked to an allowlist (model APIs, Maven, npm,
Node, Cypress). GLM-5.3's r1b re-run then had GitHub refused, so it downloaded
`generator-jhipster` 8.0.0 from **npm** (which builds need, so it is allowed)
and read the templates JHipster's Boot 3 app is generated from: the answer's
blueprint. It is excluded (`runs/EXCLUDED.json`). The agents had never been
**told** answer sources were off-limits. The manager asked to say so in the
prompt. "Air-gapped" would be untrue (Maven and npm must work), so the text
says exactly what the sandbox reaches and what is off-limits.

## What the branch changes (done and tested on Kasm)

All in `agentic.py`, plus `tests/test_agentic.py` and `docs/AGENTIC.md`:

1. **`SYSTEM_NOTE`** (every task, both agents) gains:
   > Internet access: the sandbox reaches only the model API and the package
   > registries a build needs (Maven Central, npm); every other site is
   > blocked. Use the registries only to install the project's dependencies.
   > Do not look up, download or copy a published solution, a newer version of
   > this project, or the generator or templates it was made from, from any
   > source, npm included. The result must be your own migration of the code
   > in /work.
2. **r1b's `task_note`** gains: "Off-limits: jhipster-sample-app in any
   version other than the one here, and generator-jhipster (its templates
   describe the answer)." Other tasks do not get the JHipster names.
3. **opencode's web tools off**: `OPENCODE_DENIED_ACTIONS = ("subagent",
   "webfetch", "websearch")` are denied in the per-attempt config, the
   counterpart of Claude Code's `--disallowedTools Agent WebFetch WebSearch`.
   (In GLM's re-run `webfetch` was refused by the proxy and `websearch`
   returned "Web search cancelled", but websearch may run through opencode's
   own servers, which are allowed.)
4. **Cypress bug fixed**: `_setup_r1b` replaced the whole `src/test` with the
   migrated suite, which holds only `java/` and `resources/`, so the 54
   Cypress specs in `src/test/javascript` were deleted from the workspace on
   2026-11-02 (both re-runs restored them with `git checkout`; scoring was
   not affected, the scorer runs Cypress from its own cache). Now only
   `java/` and `resources/` are replaced.

Verified on Kasm: `pytest` 400 passed, 18 skipped (Postgres not running
there; none touch this change). **Not verified:** that opencode v2.2.5
accepts `webfetch` / `websearch` as permission actions (the image is not on
the Kasm machine). Step 4 checks it.

## Steps on the home PC

Follow the repo's rules (the `gate1-eval` skill): never print `.env`, confirm
with the owner before anything that spends, no commits/pushes without review.

### 1. Get the branch

```bash
cd <your clone>/ai-model-lifecycle            # the git root
git fetch origin                              # or the fork remote
git checkout fix/agentic-prompt-rules         # or `git checkout main && git pull` once merged
cd ai-model-lifecycle                         # the project
```

### 2. Images, caches, keys

No Dockerfile changed, so the images from 2026-11-02 are fine. If either is
missing: `docker build -t gate1-agent:latest docker/agent` and
`docker build -t gate1-egress:latest docker/egress` (on x86, `JAVA_HOME` in
`docker/agent/Dockerfile` must end `-amd64`, not `-arm64`). `.env` needs
`CLAUDE_CODE_OAUTH_TOKEN` (Claude re-runs) and `OPENCODE_GO_API_KEY` (GLM);
keep Go's Extra Usage off.

### 3. Tests: must pass with nothing skipped

```bash
docker compose -f docker/docker-compose.yml up -d    # Postgres for the SQL tests
python -m cases.sources --check
bash cases/r1b_jhipster_boot3/setup_e2e.sh           # no-op if the cache exists
pytest -q                                            # 0 failed, 0 skipped
```

### 4. Check opencode accepts the new permissions (free, no model call)

```bash
mkdir -p /tmp/oc-check
python -c "import agentic, json; print(json.dumps(agentic.opencode_config('glm-5.3', 'medium'), indent=2))" > /tmp/oc-check/opencode.json
docker run --rm --entrypoint sh -v /tmp/oc-check:/gate1:ro \
  -e OPENCODE_CONFIG=/gate1/opencode.json -e OPENCODE_DISABLE_PROJECT_CONFIG=1 \
  gate1-agent:latest -c 'opencode debug config; echo ===; opencode debug agents'
```

Expect: no config error, and the resolved permissions show `webfetch` and
`websearch` (and `subagent`) as `deny`. If opencode rejects the names or
resolves them differently, find the right action names (`opencode debug
agents`, https://opencode.ai/v2/docs/), fix `OPENCODE_DENIED_ACTIONS` and its
test, and do not run GLM until this passes.

### 5. Smoke test the new prompt (cheap; ask the owner)

```bash
python agentic.py --pair opus-5.5-cc-vs-glm-5.3 --role target \
    --case r4_schema_load_optimize --effort medium --time-limit 1200
```

Expect: `network: allowlist`, a pass, and in the stream log
(`runs/opus-5.5-cc-vs-glm-5.3/agentic/<run>/*.stream.jsonl`) no `webfetch` or
`websearch` tool call that ran (a denied one is fine). This adds one r4
attempt to GLM-5.3's row; if unwanted, add its record to `runs/EXCLUDED.json`
with the reason "smoke test (prompt-rules check)".

### 6. The re-runs (ask the owner first: they spend)

**Required: GLM-5.3 on r1b** (OpenCode Go; the last one cost about $12 at Go
list price). Same settings as before: role `target` of
`opus-5.5-cc-vs-glm-5.3`, medium, 3600 s, one attempt.

```bash
python agentic.py --pair opus-5.5-cc-vs-glm-5.3 --role target \
    --case r1b_jhipster_boot3 --effort medium --repeats 1 --time-limit 3600 \
    --max-spend-usd 15
```

**Optional: all 9 Claude rows on r1b**, so every r1b row has the same prompt
and setup (and comparable times: before 2026-11-02 the agents also migrated
the tests themselves). None of the Claude rows ever used the answer (except
Haiku high's first attempt, already excluded), so their pass/fail stands
either way. 9 attempts of up to 60 min on the Claude subscription; the
originals took 16–41 min each.

| Row | Pair | Role | Effort | Current r1b run (to supersede) |
|---|---|---|---|---|
| Sonnet 5.5 low | `sonnet-5.5-cc-vs-deepseek-v4-pro` | current | low | 20261101T005111Z |
| Sonnet 5.5 medium | `sonnet-5.5-cc-vs-deepseek-v4-pro` | current | medium | 20261031T130029Z |
| Sonnet 5.5 high | `sonnet-5.5-cc-vs-deepseek-v4-pro` | current | high | 20261031T161435Z |
| Opus 5.5 low | `opus-5.5-cc-vs-kimi-k3` | current | low | 20261101T024937Z |
| Opus 5.5 medium | `opus-5.5-cc-vs-kimi-k3` | current | medium | 20261031T145008Z |
| Opus 5.5 high | `opus-5.5-cc-vs-kimi-k3` | current | high | 20261031T190847Z |
| Haiku 5.5 low | `haiku-5.5-cc-vs-glm-5.3-flash` | current | low | 20261101T013831Z |
| Haiku 5.5 medium | `haiku-5.5-cc-vs-glm-5.3-flash` | current | medium | 20261031T135411Z |
| Haiku 5.5 high | `haiku-5.5-cc-vs-glm-5.3-flash` | current | high | 20261102T111955Z |

```bash
# one per row, e.g. Sonnet low:
python agentic.py --pair sonnet-5.5-cc-vs-deepseek-v4-pro --role current \
    --case r1b_jhipster_boot3 --effort low --repeats 1 --time-limit 3600
```

A usage-limit stop (exit code 3 / "stopping: …limit") is not a result: wait
for the limit to reset and run the same command again.

### 7. Check each result before reporting it

* The record (`runs/<pair>/agentic/<run>/*.r1b_jhipster_boot3.*.json`):
  `passed`, `reason`, `checks`, `network` = `allowlist`, `blocked_hosts`.
* The stream log: search for `github`, `jhipster-sample-app`, `v8.0.0`,
  `generator-jhipster`, `npm pack`, `npm view`, `npm install -g`. A fetch of
  the generator or the published app means the attempt used the answer
  despite being told: add it to `runs/EXCLUDED.json` with the evidence, as
  for the 2026-11-02 GLM re-run, and tell the owner (it is a finding).
* Cypress: the specs should now be there from the start (no `git checkout
  ... src/test/javascript` in the log).
* A fail: find the cause in the stream log and the scorer's `details` before
  reporting it.

### 8. Leaderboard: decide how old r1b attempts count

`leaderboard.py` **pools** every non-excluded attempt per model and level, so
a re-run is averaged with the old attempt (r1b would show 2/2 and a mean
time). Ask the owner which they want:

* **Pool** (default, no change): more attempts per row, but mixed setups.
* **Supersede**: add each replaced record from the table above to
  `runs/EXCLUDED.json` with the reason "superseded by the <run> re-run with
  the stated internet rule (2026-11-03)". They stay visible as flagged rows.

Then `python leaderboard.py` and check `runs/LEADERBOARD.md`.

### 9. Commit the results

A new branch from the updated main, with the new `runs/*/agentic/<run>/`
folders, `runs/EXCLUDED.json` if changed, and `runs/LEADERBOARD.md`; push to
the fork and open a PR, as usual. Do not commit `.env`.

## Then update the deck

Deck: https://claude.ai/artifact/NDs6WhZJx789q2iVzfDrVU (edit with the
Artifact tool: read `project/slides/<id>.html`, change, publish to the same
URL). Slides to touch once results are in:

| Slide | id | Change |
|---:|---|---|
| 1 | `cover` | counts and the GLM sentence |
| 7, 8, 9 | `ranking`, `real-projects`, `thinking-level` | new r1b times/costs if the Claude rows were re-run |
| 12 | `pass-rule` | the table: GLM's new attempt; note the agents are now told the rule |
| 13 | `sandbox-reach` | "opencode's web search is still on" and open gap 2 are now fixed |
| 14 | `caveats` | the "Fixed · open internet" box: the rule is now stated |
| 18 | `glm-real` | the r1b card: the new result |
| 19 | `recommendation` | next steps |
| backup | `backup-ranking`, `backup-r1b`, `backup-r1b-2`, `backup-runs` | copy the new LEADERBOARD.md values |
