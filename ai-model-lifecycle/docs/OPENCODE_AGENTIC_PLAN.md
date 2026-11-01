# Plan: open-weight models in the agentic harness via opencode

Status: **implemented 2026-11-01** (see docs/AGENTIC.md, "Two agents"). The
GLM-5.3 smoke test passed r4. Not yet observed: `/goal` re-prompting an agent
that stops early. Differences from this plan, found by probing opencode v2.2.5:
Go models have no low/medium/high variants, so the thinking level is sent as
`reasoning_effort` in the build agent's request body; the config is written in
v2's native form (`policies`, `permissions`, `agents`, `snapshots`, `plugins`,
`update`). Drafted 2026-11-01.

## Goal

Run the open-weight models already configured in `models.yaml` (GLM-5.3,
GLM-5.3 Flash, DeepSeek V4 Pro, Kimi K3) on the same agentic Gate 1 tasks as
the Claude 5.5 models, scored by the same hidden tests, on the same
leaderboard. Claude models keep running through Claude Code; open-weight
models run through **opencode**, the open-source coding-agent CLI.

## Decisions

| Topic | Decision |
|---|---|
| Route | **opencode → OpenCode Go** (`api: opencode-go`, key `OPENCODE_GO_API_KEY`), the route `models.yaml` already uses. No OpenRouter. |
| Plan | Go Plus. |
| Billing guard | Extra Usage stays **off** except while a run is going; the credit balance is the hard spend cap. |
| Claude via API key | Never. No Anthropic API credits are used. |
| Agent-only control (Claude Haiku through opencode) | **Skipped for now**; revisit if the open-weight results look surprising. |
| opencode version | Pin **v2.2.5** (has a native `/goal`). Fall back to a harness loop if `/goal` does not work in headless `opencode run`. |

## Quota and spend (as of 2026-11-01)

Go Plus console: 5-hour window 0% used, **weekly 100% used** (resets in about
22 h), **monthly 98% used** (resets in about 13 days), Extra Usage off,
credit $0.00. The remaining monthly quota is enough for a smoke test at most.
A full run needs either the monthly reset or purchased credits.

Estimated cost of one full run (sanity × 3 + real × 1) at Go list prices,
from the Claude runs' token profiles:

| Model | Typical | Heavy (many turns, poor caching) |
|---|---:|---:|
| DeepSeek V4 Pro | ~$0.60 | ~$3 |
| GLM-5.3 Flash | ~$2 | ~$2 |
| GLM-5.3 | ~$5 | up to ~$18 |
| Kimi K3 | ~$7.50 | up to ~$28 |

Nearly all of it is the real tasks (r1b, r2). Prompt-cache hit rate through
opencode is the biggest unknown and is measured in the smoke test.
**To verify before buying:** the rate extra-usage credits are charged at.

Spend controls:
1. A fixed credit purchase (suggested start: $20). Balance $0 means requests are blocked, not billed.
2. Extra Usage on only during a run.
3. opencode config `enabled_providers: ["opencode-go"]`, so a typo cannot fall through to opencode's pay-as-you-go Zen provider.
4. Harness `--max-spend-usd`: stop the batch when the estimated spend passes the cap.
5. Optional per-attempt kill when one attempt's estimate passes a cap (recorded as `stopped_by: cost_cap`, scored like a time limit).

## Design

### Two backends, one harness (`agentic.py`)

Shared, unchanged: cases and setups, task prompt, workspace snapshot and
answer, time limit via `docker kill`, scoring, records, `REPORT.md`, the run loop.

Per backend: command, container env, control files, stream parser, error and
limit detection, preflight.

- `ClaudeCodeBackend` delegates to today's functions, which keep their names and behavior. The Claude path stays byte-for-byte identical.
- `OpencodeBackend` gets new functions: `write_opencode_control`, `opencode_command`, `_opencode_env`, `summarize_opencode`, `_OPENCODE_LIMIT_RE`, `preflight_opencode`.
- `backend_for(cfg, model)` routes `claude-code` models to Claude Code, `opencode-go` models to opencode, and refuses anything else.
- `AgenticResult` gains `agent`, `agent_version`, `goal_mode`, `cost_reported_usd`, `reasoning_tokens`, `model_time_source`, `stopped_by`. Old records default to `agent: claude-code`.
- Effort: `low`, `medium` and `high` for opencode, via model variants; `xhigh` and `max` are refused.

### Docker image

One image, so both agents get the identical toolchain (Java 17/8, Maven,
Node 20, Chromium, Postgres 17).

- Add a pinned opencode layer from the GitHub release tarball, with a SHA256 check, after the Claude Code layer.
- Record both agent versions as image labels.
- Build as `gate1-agent:oc-2.2.5` and retag only after review.

### Auth and isolation

- The container gets `OPENCODE_API_KEY` from `OPENCODE_GO_API_KEY`, passed **by name** only.
- The opencode path strips `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_*` and `OPENROUTER_*`. The Claude path strips `OPENCODE_*`.
- Per-attempt `/gate1/opencode.json` (read-only mount, no secrets):
  - `enabled_providers: ["opencode-go"]`
  - the goal task as instructions from `/gate1/system.md`
  - no MCP servers or plugins; LSP, formatter, snapshot and share off
  - all permissions allowed, **subagents denied** (as `--disallowedTools Agent` for Claude)
- Env flags disable project config, Claude-Code compatibility, external skills and autoupdate.
- **New, both backends:** redact any secret env value from the saved stream logs before writing them. An agent running `env` must not leak a key into `runs/`.
- Add `OPENCODE_API_KEY=` and `OPENCODE_GO_API_KEY=` to the pre-commit secret scan.

### Goal and persistence parity

- **Native (preferred):** the prompt file holds `/goal <goal>`, the same as Claude's. opencode v2's goal reviewer judges after each idle point (at most 50 rounds, stops after 3 with no progress).
- **Loop (fallback):** if headless `opencode run` ignores `/goal`, a small driver re-prompts with `--continue` until the agent answers `GOAL MET`, stalls 3 times, or hits the time limit. The agent judges itself, which is weaker; it is recorded as `goal_mode: loop` and footnoted.

### Stream parsing (opencode `--format json`)

| Field | Source |
|---|---|
| turns | count of `step_finish` events |
| tool calls | count of `tool_use` events |
| tokens (input, output, reasoning, cache) | sum of `step_finish.part.tokens` (per-step deltas) |
| cost | `pricing.py` at Go list price; opencode's own sum kept as `cost_reported_usd` |
| tool time | merged `tool_use` start–end spans (shared helper with `stream_timing`) |
| model time | derived from step spans minus tool spans (`model_time_source: derived`) |
| thinking time | `reasoning` part spans, else none |
| final message | last `text` event |

**Error classification**
- **Infra error (not scored):** auth, quota, rate limit, network and 5xx errors, and runs where the agent never got to work.
- **Scored failure:** errors the model causes, such as context overflow or the goal pausing for lack of progress.
- **Batch stop:** limit and quota errors also stop the batch via `_OPENCODE_LIMIT_RE`.

### Model config (`models.yaml`, `common.py`)

- Existing cross pairs already hold the open models as `--role target`. No new pairs are needed.
- Add an `agentic.opencode` block: version, goal mode, effort variants and `max_spend_usd`.
- `ModelRef` gains optional `agent` and `agentic_effort`.
- GLM is thinking-only: smoke-test it at medium, and fall back to low per model if steps run out of output budget.

### Leaderboard

- Rows pool by model, thinking level and agent. Open-weight rows read e.g. "GLM-5.3 · opencode". Claude rows are unchanged.
- Footnotes:
  - Go cost is quota at list price, not a bill.
  - opencode model time is derived.
  - **Model and agent change together**, so an opencode row differs from a Claude row in both.

## Files to change

| # | Task | Files | Size |
|---|---|---|---|
| 1 | `agent`, `agentic_effort` on `ModelRef`; `Config.agentic` | `common.py` | S |
| 2 | `agentic.opencode` block | `models.yaml` | S |
| 3 | Backend abstraction; `_docker_prefix`, `_merge_spans`; new result fields; log redaction | `agentic.py` | M |
| 4 | `OpencodeBackend` (control files, command, env, parser, limits, preflight) | `agentic.py` | M–L |
| 5 | `--agent`, `--max-spend-usd`; batch spend stop | `agentic.py` | S–M |
| 6 | Pinned opencode layer, checksum, labels; loop script only if needed | `docker/agent/Dockerfile` | S |
| 7 | Pool and label rows by agent; footnotes | `leaderboard.py`, `render_report` in `agentic.py` | S–M |
| 8 | Offline tests (below) | `tests/test_agentic.py`, `tests/test_leaderboard.py`, `tests/fixtures/opencode_stream_*.jsonl` | M |
| 9 | Docs | `docs/AGENTIC.md`, `docs/METRICS_PLAN.md` §8, `README.md` | S |

## Tests (all offline, no model calls)

**Command and env**
- The opencode command passes the key by name, with the config path, `--format json --auto --standalone` and `--model opencode-go/<id>#<effort>`.
- The goal is never in argv.
- Env mapping and stripping is correct for both backends.

**Config**
- `enabled_providers` holds only `opencode-go`.
- Subagents are denied; LSP, formatter and snapshot are off.
- No secret values appear in the file.

**Parsing and classification**
- Step sums, merged tool spans, derived model time, thinking time and the final message.
- Pricing cost vs the reported cost.
- 401/429 → infra error and batch stop; context overflow → scored failure; no steps and exit 1 → "did not run"; time limit → scored.

**Selection and leaderboard**
- The backend is chosen by API.
- `xhigh` is refused for opencode.
- `test_only_claude_code_models_run_agentic` is replaced by these cases.
- Old records pool as claude-code, and one model under two agents makes two rows.

**Regression**
- Every other existing test passes unchanged.

## Rollout

0. Wait for the low-effort Claude sweep to finish, on a new branch from `main`.
1. Implement tasks 1–9; `pytest` passes.
2. Build `gate1-agent:oc-2.2.5`. Container checks with no model spend: version, resolved config, the `opencode-go` model list (confirms IDs and variants).
3. Invalid-key run: capture Go's error shape and check the infra and limit classification.
4. **Needs quota or credits.** Smoke test: DeepSeek V4 Pro, `r4_schema_load_optimize`, 1 attempt, 15-minute limit, off-peak. Inspect the stream by hand:
   - tokens, cost and cache hits
   - `/goal` actually loops
   - harvest and score
   - key redaction
   - no leftover container
5. Sanity suite (×3): DeepSeek V4 Pro, then GLM-5.3 Flash, GLM-5.3, Kimi K3. Compare real spend with the estimates after each.
6. Real suite (×1): one model per 5-hour window, Kimi last.
7. Rebuild the leaderboard and review the opencode rows.

Nothing is committed or pushed without review.

## Risks and open questions

- **`/goal` in headless mode is unverified.** The fallback loop is weaker.
- **opencode moves fast** (v2.2.1 to v2.2.5 in days). The exact version is pinned, real smoke output is kept as test fixtures, and the run warns loudly when no `step_finish` appears.
- **v1 and v2 config schemas differ** (`permission`→`permissions`, `bash`→`shell`, `task`→`subagent`).
- **Tool-calling quality:** GLM and Kimi may produce malformed tool calls. These count as scored failures, not infra errors.
- **r1b context size:** long Maven and Cypress logs. opencode auto-compacts.
- **Background shells:** `opencode run` may exit while a build is still running in the background (loop mode especially).
- **Self-kill:** an agent killing every process ends its own session. This is a scored stop.
- **Quota sharing:** single-shot Go runs and agentic runs draw on the same limits.
- **DeepSeek V4 Pro** needs the region privacy setting on Global, and costs 2× at peak hours.
- **Extra-usage credit rate** is unverified.

## Sources

- opencode CLI, config, permissions, providers and Go docs: https://opencode.ai/docs/ and https://opencode.ai/v2/docs/
- Releases (v2.2.1 goal, v2.2.5 assets): https://github.com/anomalyco/opencode/releases
- npm `opencode-ai` latest 1.19.5 (v1, no `/goal`)
- Source reviewed via context7 `/anomalyco/opencode`: `packages/cli/src/run/`, `packages/core/src/plugin/goal.ts`, `packages/core/src/tool/plugin/shell.ts`, `packages/schema/src/v1/session.ts`
