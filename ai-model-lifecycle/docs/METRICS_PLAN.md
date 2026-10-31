# Gate 1 Metrics Improvement Plan

> Status: Implemented (single-shot, 2026-10-30); extended to agentic runs (§8, 2026-10-31)  
> Date: 2026-10-30, amended 2026-10-31

## Purpose

Add three complementary measurements to the Gate 1 model-evaluation scorecard:

1. Time to First Success (TTFS)
2. Success rate within a time budget, `Pass@T`
3. Execution Time / Thinking Time ratio

The implementation must preserve Gate 1's existing single-shot benchmark, deterministic scoring, cost accounting, and weighted overall score.

**Amendment 2026-10-31.** Gate 1 now measures migration the way it is done on a real project: the model changes code, builds, tests and fixes until the project delivers (`agentic.py`, docs/AGENTIC.md). Agentic results are the primary leaderboard; single-shot is kept as a quick screening test. Sections 1–7 below define the metrics for single-shot runs and still apply to them unchanged. Section 8 defines the same three metrics for agentic attempts.

**Scope exclusion:** OpenRouter is excluded for now. Do not make OpenRouter calls or change its transport, billing, instrumentation, or route-specific behavior as part of this work. The initial implementation and smoke testing target supported non-OpenRouter routes only.

## 1. Metric definitions

For scored attempt `i`:

- `L_i = latency_s`: complete-response latency for that attempt.
- `P_i`: the deterministic scorer's pass/fail result.
- Infrastructure errors remain excluded from all three metrics.
- Grading time and harness retry time remain outside model latency.

### 1.1 Time to First Success

Gate 1 remains single-shot, so each attempt has one opportunity to succeed. For a passing attempt:

```text
TTFS_i = L_i
```

Report mean TTFS over passing attempts:

```text
Mean TTFS = sum(L_i for passing attempts) / number of passes
```

Rules:

- Failed attempts do not contribute to the TTFS average.
- Show coverage as passes / scored runs.
- Render `n/a` when a model has no passes.
- Do not introduce a retry-until-pass or generate-test-fix loop *into single-shot runs*. (Agentic runs are that loop by design, measured separately: §8.)

TTFS does not add a separate timeout. The existing call `timeout_s` still prevents an attempt from running indefinitely, and the existing transport-retry policy still applies. If all transport attempts time out or fail, the record remains an infrastructure error: it has no TTFS and is excluded from Pass@T. A `Pass@T` budget is only a reporting threshold; it does not cancel a call at `T`.

### 1.2 Success rate within a time budget: Pass@T

For a time budget `T` in seconds:

```text
Pass@T = number of scored attempts where P_i and L_i <= T
         ---------------------------------------------------
                    number of scored attempts
```

Rules:

- The time boundary is inclusive: `latency_s <= T`.
- A passing attempt slower than `T` does not count in the numerator.
- Model failures and slow passes remain in the denominator.
- Infrastructure errors are excluded from both numerator and denominator.
- Pass/fail must come from the live scorer when live scoring is enabled, not merely the runner's `ok` flag.

Default budgets:

| Suite | Default budgets |
|---|---|
| Sanity | 30, 60, 120 seconds |
| Real | 300, 900, 1800 seconds |

Budgets must be configurable in `models.yaml` and overridable from the report CLI.

### 1.3 Execution Time / Thinking Time ratio

Definitions:

- **Thinking time:** client-observed streamed reasoning phases.
- **Execution time:** client-observed streamed visible-answer phases only.

Execution time must not be calculated as `latency_s - thinking_time_s`, because that difference also contains startup, network, CLI, and other overhead.

Aggregate the ratio over the same measured calls:

```text
Execution / Thinking ratio = sum(execution_time_s)
                             -----------------------
                             sum(thinking_time_s)
```

Rules:

- Use paired calls where both timing fields are available.
- Render `n/a` when measurements are missing or total thinking time is zero.
- Never interpret a missing measurement as zero.
- Do not infer phase durations from reasoning-token counts.

### 1.4 Relationship to the overall score

Initially, TTFS, Pass@T, and Execution / Thinking ratio are descriptive metrics. They must not alter:

- The existing Quality, Cost, or Time components.
- The current = 100 normalization.
- The weighted overall score or verdict.

## 2. Complete phase-timing instrumentation

**Files:** `runner.py`, `common.py`, `models.yaml`

Build on the existing opt-in `thinking_time_s` work rather than replacing it.

Implementation steps:

1. Extend `_ThinkingTimer` into a phase timer that accumulates reasoning and visible-answer intervals with `time.monotonic()`.
2. Support interleaved reasoning and answer events.
3. Ignore empty and keepalive chunks.
4. Close any active phase at end-of-stream.
5. Add optional `execution_time_s` to `CallResult` and `RunResult`, alongside `thinking_time_s`.
6. Preserve existing `latency_s`, retry, billing, output-extraction, and scorer behavior.
7. Keep phase capture behind the existing `thinking_time` opt-in so a normal evaluation does not silently change transport.
8. Add `Config.time_budgets_s`, validating that values are positive, finite, sorted, and unique.

Configuration:

```yaml
defaults:
  time_budgets_s: [30, 60, 120]

suites:
  real:
    time_budgets_s: [300, 900, 1800]
```

Initial route support:

| Route | Phase timing |
|---|---|
| OpenCode Go chat / messages | Supported through existing streaming instrumentation |
| Claude Code | Supported through opt-in stream-json instrumentation |
| OpenCode Go Responses API | `n/a`; retain non-streaming behavior |

OpenRouter is outside this iteration. Do not switch Go Responses or any other currently non-streaming route to streaming in this change. Any later expansion must first prove equivalent output and complete usage/cost capture.

## 3. Aggregate and render metrics

**Files:** `report.py`, `common.py`

Extend `ModelAgg` with:

- Passing-latency totals for mean TTFS.
- Per-attempt `(latency, passed)` outcomes for configurable Pass@T calculations.
- Paired execution/thinking totals and measurement coverage.

Populate success-dependent metrics only after the scorer has determined `passed`.

Add summary rows for:

- `TTFS (mean successful-attempt latency, s)`
- One row per configured `Pass@T`
- `Execution / thinking time ratio`, including measured-run coverage

Keep the existing mean-latency row and all existing score calculations unchanged.

Add a repeatable report option:

```bash
python report.py --pair <pair> --time-budget 30 --time-budget 60 --time-budget 120
```

When no CLI override is supplied, use the active suite's configured budgets.

Historical run files already contain enough information for TTFS and Pass@T, so report regeneration can add those metrics without new model calls. Their Execution / Thinking ratio remains `n/a` unless phase timing was recorded.

Under `--no-score`, document that TTFS and Pass@T inherit the runner completion flag and therefore do not represent verified task correctness.

## 4. Export metrics to MLflow

**Files:** `mlflow_export.py`, `MLFLOW.md`

Add model-level metrics, automatically mirrored as `current_*` and `target_*` on the parent run:

- `mean_ttfs_s`
- `pass_at_30s`, `pass_at_60s`, and other configured budget names
- `execution_thinking_time_ratio`
- Timing-coverage counts

Add per-call `execution_time_s` alongside `thinking_time_s`, and include both fields in the `calls.json` artifact.

Rules:

- Omit unavailable numeric MLflow metrics rather than logging zero.
- Keep `runs/` as the source of truth.
- Preserve export idempotency. Already-exported MLflow runs do not change automatically; new or explicitly re-exported runs contain the new fields.

## 5. Tests

### `tests/test_harness.py`

Cover:

- TTFS includes passing attempts only.
- Zero-pass models render `n/a` rather than a misleading zero.
- Pass@T uses the all-scored-attempts denominator.
- Infrastructure errors are excluded.
- The `latency_s == T` boundary passes.
- Live scorer results, not merely `ok`, drive TTFS and Pass@T.
- Execution / Thinking uses a ratio of sums over paired measurements.
- Missing timing and zero-thinking cases return `n/a`.
- Existing overall-score values remain unchanged.
- Suite-specific and CLI budget selection works.

### `tests/test_go_gateway.py`

Cover:

- Reasoning, visible-answer, interleaved, and empty chunks.
- Phase-timer calculations and persisted fields.
- Timing capture remains opt-in.
- Responses API behavior remains unchanged when phase timing is unsupported.
- No OpenRouter-specific instrumentation or test coverage is added in this iteration.

### `tests/test_claude_code_gateway.py`

Cover:

- Opt-in stream-json and partial-message flags.
- Claude stream-event classification.
- Equivalence of the final result with the existing JSON route.
- Error and timeout handling.
- Persistence of execution and thinking durations.

### `tests/test_mlflow_export.py`

Cover:

- Parent, model, and per-call metrics.
- `current_*` / `target_*` names.
- Budget-specific metric names.
- `calls.json` phase-timing fields.
- Missing measurements are omitted rather than exported as zero.

## 6. Documentation updates during implementation

- `docs/LATENCY.md`: metric formulas, scopes, defaults, coverage, and route limitations.
- `README.md`: configuration and report CLI examples.
- `MLFLOW.md`: new metric and artifact fields.
- `SCORING.md`: clarify that the new metrics do not currently affect the weighted score.

## 7. Verification and acceptance criteria

Verification sequence:

1. Start the required Docker services and run `pytest -q`; all tests must pass with nothing skipped.
2. Regenerate one historical non-OpenRouter report and verify TTFS and Pass@T values, `n/a` phase ratios, and an unchanged overall score.
3. After confirming model-run cost, execute one cheap instrumented smoke test on a supported non-OpenRouter streaming route.
4. Inspect the saved run JSON and generated report for correct timing fields and coverage.

Acceptance criteria:

- No retry-until-pass or grading behavior was introduced.
- Existing latency, quality, cost, and overall-score results are unchanged for the same records.
- Pass@T denominators include every scored attempt and exclude only infrastructure errors.
- Missing measurements never become zero.
- TTFS is `n/a` without a pass.
- Execution / Thinking ratio is `n/a` without valid paired measurements and nonzero thinking time.
- Historical reports remain reproducible.
- New Markdown and MLflow outputs use the same metric definitions and values.

## 8. Agentic attempts (amendment 2026-10-31)

An agentic attempt (`agentic.py`) is one Claude Code session in a sandbox that
works on the project until its `/goal` is met or the time limit stops it; what
it delivered is then scored by the same deterministic scorer, hidden tests
included. One attempt is one opportunity to succeed, so the single-shot
definitions carry over with these changes.

For agentic attempt `i`:

- `W_i = latency_s`: the session's wall-clock time, sandbox start to stop.
  Scoring time stays outside it.
- `P_i`: the scorer's verdict on what the attempt delivered (live scoring
  through the score cache, so a scorer fix reaches earlier attempts).
- A session that never ran, or that Claude Code ended with an error (login,
  usage limit, API), is an infrastructure error and is excluded from every
  metric. A session stopped by the time limit is a scored attempt.

### 8.1 TTFS

```text
Mean TTFS = sum(W_i for passing attempts) / number of passes
```

`n/a` without a pass; shown with coverage as passes / attempts.

### 8.2 Pass@T

```text
Pass@T = number of attempts where P_i and W_i <= T
         ------------------------------------------
                 number of scored attempts
```

Inclusive boundary; failures and slow passes stay in the denominator. Agentic
attempts build and test for minutes, so they have their own budgets,
configurable in `models.yaml` as `agentic_time_budgets_s`:

| Suite | Agentic budgets |
|---|---|
| Sanity | 120, 300, 600 seconds |
| Real | 900, 1800, 3600 seconds |

A budget is a reporting threshold; the attempt's hard stop is `--time-limit`.

### 8.3 Tool time / model time ratio

In an agentic session most of the time goes to running builds and tests rather
than to producing text, so the stream-phase execution / thinking ratio of §1.3
is replaced by:

- **Model time:** `duration_api_ms`, the session's time in API requests
  (thinking and writing), as Claude Code reports it.
- **Tool time:** for each tool call, from the `tool_use` message to its
  `tool_result`, by the events' own timestamps in the session stream, with
  overlapping (parallel) calls merged so no second counts twice.

```text
Tool / model time = sum(tool_time_s) / sum(model_time_s)
```

over attempts that measured both. Never derived from `latency_s` (which also
holds sandbox start-up and harness overhead); `n/a` when unmeasured or model
time is zero; a missing measurement is never zero. Above 1 means the attempt
spent more time waiting on builds and tests than on the model. The model's
reported thinking time (`thinking_duration_ms`) is recorded per attempt as
`thinking_time_s` for reference.

### 8.4 Where they appear

`runs/LEADERBOARD.md`, agentic section, per task: Passed, Pass rate, Mean time,
TTFS, one Pass@T column per budget, Tool / model time, Mean cost, Cost / pass,
Mean turns. Like §1.4, these are descriptive and do not change any score.
Records written before §8 were backfilled from their saved session streams.

