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
