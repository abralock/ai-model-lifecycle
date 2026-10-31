# Gate 1: how "latency" is measured

**Short answer:** yes. In Gate 1, latency is the time a model takes to complete one
assignment: from sending the task to receiving the model's complete solution. Each
assignment is a single request, so request time and assignment time are the same thing.

## What one assignment is

Each task is one prompt that contains everything the model needs: the instructions and
the source code to change. The model answers with the whole solution in one reply,
either as full files or as search/replace edits. There is no back-and-forth, no tool
use and no second attempt.

| Suite | Task | What the model has to do | Prompt size |
|---|---|---|---|
| Sanity | r1 | Migrate a small Spring Boot 2 app to Spring Boot 3 | ~7k tokens |
| Sanity | r3 | Convert Oracle stored procedures to PostgreSQL | ~3k tokens |
| Sanity | r4 | Write a schema load script and optimize a query | ~2.5k tokens |
| Sanity | r5 | Build an ETL job and a dashboard schema | ~4k tokens |
| Real | r1b | Upgrade a real JHipster app to Spring Boot 3 / Java 17 | ~108k tokens |
| Real | r2 | Migrate a real GWT app to Angular | ~74k tokens |

## What the latency number includes

`latency_s` in each run file is wall-clock time, measured around the call:

- **Included:** all of the model's work on the answer, hidden thinking ("reasoning")
  as well as the visible answer. On the Claude Code route it also includes anything
  Claude Code does inside one call, such as an internal retry.
- **Not included:**
  - *Grading.* Compiling the answer and running the tests happens afterwards and isn't timed.
  - *Our own retries.* If a request fails (for example a rate limit) and the harness
    retries it, only the successful attempt is timed. The attempt count is recorded
    separately.
  - *Time to first token.* We measure time to the complete answer only.

The scorecard's **Time (mean latency, s)** row is the average of `latency_s` over all
of a model's scored runs in one pair: 4 tasks × 3 repeats = 12 runs on the sanity
suite, 2 tasks × 3 repeats = 6 runs on the real suite.

## Optional thinking-stream time

Set `thinking_time: true` under `defaults:` in `models.yaml` for **future runs** to
record `thinking_time_s` alongside total latency. OpenCode Go chat/messages streams
are timestamped at reasoning/content transitions. Claude Code uses opt-in
`stream-json` with partial messages and timestamps its thinking/text events.

A thinking phase starts at the first reasoning event and ends at the next visible
answer event (or at end-of-stream when no answer is produced). Multiple phases are
summed. This is **client-observed reasoning-stream time**, including network and
gateway waits between events; it is not provider-reported compute time. Existing run
JSON cannot be backfilled with it.

The effective effort is recorded in `reasoning_requested` and exported to MLflow as
`reasoning_effort`. Use the same supported effort level on both models when making a
level-adjusted comparison; a model-specific `params.reasoning_effort` on Go and the
suite's `reasoning: {effort: ...}` on Claude Code otherwise remain different settings.

## What it does not measure

This is a **single-shot** benchmark: how long a model takes to write the whole solution
in one reply. It does **not** measure an *agent* doing the assignment, editing files,
compiling, reading the errors and fixing them over many steps until the tests pass. If
"time to complete the assignment" means that agentic workflow, we don't measure it today.

## Results: Claude models via Claude Code (October 2026)

Runs made through the Claude Code CLI on a personal claude.ai subscription. All times
are seconds per assignment.

### Mean time per assignment (the scorecard's "Time" row)

| Pair | Suite | Current model | Target model | Change |
|---|---|---|---|---|
| Haiku 4.5 → Haiku 5.5 | Sanity | 65.9 s | 26.2 s | −60% |
| Opus 4.8 → Opus 5.5 | Sanity | 35.0 s | 48.6 s | +39% |
| Sonnet 5 → Sonnet 5.5 | Sanity | 37.3 s | 21.0 s | −44% |
| Sonnet 4.6 → Sonnet 5.5 | Sanity | 124.4 s | 85.3 s | −31% |
| Opus 4.8 → Opus 5.5 | Real | 630.7 s | 363.8 s | −42% |
| Sonnet 5 → Sonnet 5.5 | Real | 198.9 s | 267.6 s | +35% |
| Sonnet 4.6 → Sonnet 5.5 | Real | 807.3 s | 347.9 s | −57% |

### Real suite: time per assignment, median (min–max of 3 runs)

| Model | r1b JHipster → Boot 3 | r2 GWT → Angular |
|---|---|---|
| Opus 4.8 | 667 s (614–1,738) | 270 s (215–281) |
| Opus 5.5 | 561 s (467–657) | 149 s (148–201) |
| Sonnet 5 | 256 s (170–293) | 153 s (143–179) |
| Sonnet 5.5 (Sonnet 5 pair) | 516 s (313–548) | 76 s (66–86) |
| Sonnet 5.5 (Sonnet 4.6 pair) | 672 s (382–787) | 87 s (67–92) |
| Sonnet 4.6 | 896 s (611–912) | 759 s (599–1,067) |

### Sanity suite: time per assignment, median of 3 runs

| Model | r1 | r3 | r4 | r5 |
|---|---|---|---|---|
| Haiku 4.5 | 43 s | 77 s | 73 s | 80 s |
| Haiku 5.5 | 33 s | 23 s | 23 s | 23 s |
| Opus 4.8 | 51 s | 21 s | 40 s | 24 s |
| Opus 5.5 | 51 s | 33 s | 60 s | 46 s |
| Sonnet 5 | 37 s | 14 s | 43 s | 44 s |
| Sonnet 5.5 (Sonnet 5 pair) | 28 s | 17 s | 22 s | 16 s |
| Sonnet 4.6 | 71 s | 60 s | 99 s | 89 s |
| Sonnet 5.5 (Sonnet 4.6 pair) | 125 s | 18 s | 23 s | 16 s |

## How to read these numbers

- **Time mostly follows how much the model writes, thinking included.** Each output
  token takes time, and hidden thinking counts. For example, on r2 Sonnet 4.6 produced
  a median of ~64k output tokens (mostly thinking) for a ~24k-character answer and took
  ~13 minutes. Sonnet 5.5 produced ~13–14k tokens and took ~1.5 minutes.
- **Use the median, not the single worst run.** A few runs are outliers because of
  something other than the model's work:
  - Opus 4.8 r1b, 1,738 s, and Sonnet 5.5 r1 in the 4.6 pair, 324 s: Claude Code
    sent the prompt twice inside one call (twice the usual input tokens), probably an
    internal retry.
  - Sonnet 4.6 r3 (629 s) and Sonnet 5.5 r5 (396 s) in the 4.6 pair: one-off slow
    calls; the other two repeats took 18–60 s.
  - The API was slower overall during the Sonnet 4.6 run. Sonnet 5.5's r1 median is
    125 s there against 28 s in the Sonnet 5 pair, for the same model and task.
- **The mean includes failed answers.** An answer that fails the tests still took time
  to produce, so it counts. Only API failures (infra errors) are left out.
- **Not comparable across routes.** These come from the Claude Code CLI. Runs through
  OpenRouter use a different request and different infrastructure, so compare
  current vs target within one route only.

## Coming next

From now on, Claude Code runs also record `duration_api_ms` (time spent in the model
API alone) and `num_turns` (how many requests Claude Code made for the answer).
Comparing `duration_api_ms` with `latency_s` will separate model time from CLI
overhead and internal retries, and make outliers like the doubled requests easy to
spot.

## Descriptive timing metrics (docs/METRICS_PLAN.md)

Three scorecard rows describe timing without touching the weighted overall score,
the Quality/Cost/Time components, or the verdict:

- **TTFS (mean successful-attempt latency, s)** — Gate 1 is single-shot, so each
  attempt has one opportunity to succeed and `TTFS_i = latency_s` of a passing
  attempt. The row shows the mean over passing attempts with coverage
  `(passes/scored runs)`, and `n/a` without a pass. There is no retry-until-pass
  loop and no extra timeout.
- **Pass@T** — the share of *scored* attempts that passed with `latency_s <= T`
  (inclusive boundary). Failures and slow passes stay in the denominator; infra
  errors are excluded from both sides. Budgets are reporting thresholds only —
  they never cancel a call. Defaults come from `time_budgets_s` in `models.yaml`
  (sanity: 30/60/120 s, real suite: 300/900/1800 s) and can be overridden per
  report with repeatable `--time-budget` flags.
- **Execution / thinking time ratio** — `sum(execution_time_s) / sum(thinking_time_s)`
  over the calls where *both* stream phases were measured, with coverage
  `(measured/scored runs)`. Execution time is the streamed visible-answer phase,
  measured directly — never `latency_s - thinking_time_s`, which also contains
  startup, network and CLI overhead. `n/a` without paired measurements or with
  zero total thinking; a missing measurement is never treated as zero, and phase
  durations are never inferred from reasoning-token counts.

Historical run files already contain latency and pass/fail, so regenerating a
report adds TTFS and Pass@T to old runs without new model calls; their phase
ratio stays `n/a` unless the run was made with `thinking_time: true`. Under
`--no-score`, TTFS and Pass@T reflect the runner completion flag, not verified
task correctness, and the report says so.

## Thinking-effort sweeps (low / medium / high / xhigh / max)

Run one pair at several thinking-effort levels and compare them side by side:

```bash
# models.yaml defaults: thinking_time: true   (to measure thinking/answer phases)
python runner.py --pair opus-5.5-cc-vs-kimi-k3 --role current --effort low,medium,high,xhigh,max --repeats 3
python report.py --pair opus-5.5-cc-vs-kimi-k3 --by-effort      # -> REPORT.effort.md
```

- `--effort` runs the pair once per level, **each level in its own run id**, and
  records `effort_override` on every call. Claude Code receives `--effort <level>`
  and takes all five levels (`claude --help`, CLI 2.1.314). OpenCode Go's chat route
  receives `reasoning_effort: <level>` (replacing the model's own `params` for that
  run only — `models.yaml` is not changed) and takes low / medium / high only: its
  OpenAI-style `reasoning_effort` stops at `high`, so `xhigh` and `max` are refused
  there rather than sent.
- OpenRouter pairs are refused (out of scope, docs/METRICS_PLAN.md), and so are Go's
  responses and messages routes, which have no verified effort control — a sweep
  whose levels silently do nothing would be worse than no sweep. Whether a Go model
  honors `reasoning_effort` shows in its thinking tokens per level.
- `--role current|target` runs one side only (useful when one gateway is out of
  quota). One-sided runs are partial, so they never become the main scorecard.
- Effort runs never become `REPORT.md` either: the scorecard skips them, and
  `--list-runs` labels them `effort sweep: <level> (<roles>)`.
- `report.py --by-effort` writes `REPORT.effort.md` (or `REPORT.<suite>.effort.md`):
  one row per model × level, from the latest run of each, plus the main scorecard's
  run as a **default** baseline — pass rate, mean latency, thinking and answer time,
  their ratio, thinking tokens per call, TTFS, Pass@T and cost per run — then
  thinking time by task. Descriptive only: it feeds no score or verdict.
- Inside an instrumented stream, a phase that never happened is a measured **0 s**
  (a model that answers without thinking, common at low effort, thought for 0 s);
  `n/a` means the call was not instrumented at all.
