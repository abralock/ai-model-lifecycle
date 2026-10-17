# How the Gate 1 score is calculated

Every `REPORT.md` ends with an **overall score** and a **verdict**, e.g.
`Overall: 123.5 → target ≥ baseline ✅`. This page explains where that number comes
from. The code is `overall_score()` and `component()` in `report.py`.

## In one line

The **current model always scores 100**. The new (target) model's score says how
it compares: **above 100 is better overall, below 100 is worse.**

```
Overall = 0.5 × Quality + 0.3 × Cost + 0.2 × Time
```

## The three parts

Each part compares the target with the current model, scaled so that "the same" is 100.

| Part | Weight | Calculation | Higher means |
|---|---|---|---|
| **Quality** | 50% | target pass rate ÷ current pass rate × 100 | the new model solves more tasks |
| **Cost** | 30% | current cost per task ÷ target cost per task × 100 | the new model is **cheaper** |
| **Time** | 20% | current time per task ÷ target time per task × 100 | the new model is **faster** |

- Cost and time are flipped (current ÷ target) because lower is better: a target
  at half the cost scores 200 on cost, before the cap below.
- **Inputs** come from the same run: pass rate = passes ÷ scored runs (12 per model
  with 4 tasks × 3 repeats); cost per task = total billed cost ÷ scored runs; time per
  task = mean response time. Runs whose API call failed ("infra errors") are left out
  of all three. What "response time" covers (one request per assignment, thinking
  included, grading and retries excluded): [docs/LATENCY.md](docs/LATENCY.md).

## The cap: cost and time count between 50 and 150

Without a cap, a model 4× cheaper would score 400 on cost and outweigh being worse
at the actual tasks. So the **cost and time parts are each limited to 50–150**.
Together they can move the overall score by at most **±25 points** (30% × 50 + 20% × 50).
Quality is not capped: it is what matters most.

## The verdict

| Verdict | Rule |
|---|---|
| `target ≥ baseline ✅` | overall ≥ 100 **and** the target's pass rate is **not lower** than the current model's |
| `target < baseline ⚠️` | anything else |

A model that passes fewer tasks never gets ✅, however cheap or fast it is. If either
model passes nothing, no overall score is given.

## Worked example: Sonnet 5 → Sonnet 5.5 = 123.5

From `runs/sonnet-5-vs-5.5/REPORT.md` (run `20261009T150204Z`):

| Part | Sonnet 5 (current) | Sonnet 5.5 (target) | Calculation | Value | × weight | Points |
|---|---|---|---|---|---|---|
| Quality | 8/12 = 66.7% | 12/12 = 100% | 100 ÷ 66.7 × 100 | **150.0** | × 0.5 | 75.0 |
| Cost | $0.0457 / task | $0.0510 / task | 0.0457 ÷ 0.0510 × 100 | **89.5** (12% dearer) | × 0.3 | 26.9 |
| Time | 28.97 s / task | 26.80 s / task | 28.97 ÷ 26.80 × 100 | **108.1** (7% faster) | × 0.2 | 21.6 |
| | | | | | **Overall** | **123.5** |

Sonnet 5.5 costs a little more, but 4 more passes and slightly faster answers
outweigh that: 123.5, and its pass rate is not lower, so ✅.

## All four pairs (runs of 2026-10-09)

| Upgrade | Quality (× 0.5) | Cost (× 0.3) | Time (× 0.2) | Overall | Verdict |
|---|---|---|---|---|---|
| Sonnet 5 → 5.5 | 12/12 vs 8/12 → **150.0** | **89.5** | **108.1** | 75.0 + 26.9 + 21.6 = **123.5** | ✅ |
| Sonnet 4.6 → 5.5 | 12/12 vs 9/12 → **133.3** | **93.7** | **89.6** | 66.7 + 28.1 + 17.9 = **112.7** | ✅ |
| Haiku 4.5 → 5.5 | 10/12 vs 9/12 → **111.1** | 4.1× cheaper, **capped at 150** | 2× slower → **52.8** | 55.6 + 45.0 + 10.6 = **111.1** | ✅ |
| Opus 4.8 → 5.5 | 12/12 vs 12/12 → **100.0** | **80.8** | 2.4× slower, **capped at 50** | 50.0 + 24.2 + 10.0 = **84.2** | ⚠️ |

- **Opus:** same quality, slower and dearer, so it can only land below 100.
- **Haiku:** the cap stops the big cost saving from hiding the speed loss; what
  lifts it above 100 is one extra pass.

## Reading it sensibly

- **Quality dominates on purpose.** One extra pass out of 12 moves quality by
  about 8–11%, which is 4–6 overall points.
- **12 runs per model is a small sample.** The same Haiku pair scored 111.1 on one
  run and 100.0 on the next (10/12 vs 8/12 passes). Read the score next to the pass
  counts and **Fisher p** in the report (below 0.05 means the quality difference is
  unlikely to be luck), and check failures with `verify_failures.py`.
- **The weights are a choice.** 50 / 30 / 20 comes from `GATE1_BUILD_PLAN.md`. To
  change them, edit `W_QUALITY, W_COST, W_TIME` in `report.py`; the cap is
  `COMPONENT_MIN, COMPONENT_MAX`.
- **Not checked by the score:** the plan's extra exit criteria (for example a 100%
  pass floor on certain tasks) are not enforced by `report.py`. Read the per-task
  table in the report for those.
