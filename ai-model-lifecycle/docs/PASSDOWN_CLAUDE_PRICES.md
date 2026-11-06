# Passdown: Claude 5.5 prices, and costs for sessions stopped at the limit (2026-11-06)

Written by Claude Code on the owner's work machine (no Docker score cache, no
GitHub login), for whoever picks this up next: the owner, a peer, or another
Claude Code session. Read it top to bottom before re-running anything.

## Where things are

| What | Where |
|---|---|
| Branch | `fix/claude-api-prices` on the fork `abralock/ai-model-lifecycle`, from `main` at `2b1ea8b` (PR #59 merged): `8f1d093` the change, then this passdown |
| Pull request | not opened yet: https://github.com/abralock/ai-model-lifecycle/pull/new/fix/claude-api-prices, base `locky-bot2/ai-model-lifecycle` `main` (description drafted in the session; summary below) |
| Prices | `pricing.py`: the Claude 5.5 rows and `usage_cost_usd()` |
| Stopped-session cost | `agentic.py`: `session_cost_usd()`, record field `cost_from_prices_usd` |
| Track boards | `leaderboard.py` `render_track`: cost column, marked `≈` when priced |
| Tests | `tests/test_pricing.py` (new), `tests/test_claude_code_gateway.py` (one test rewritten) |
| Deck | https://claude.ai/artifact/NDs6WhZJx789q2iVzfDrVU ("Gate 1 Agentic Results", private): **new slide 38**, the run-2 ranking with GLM-5.3, checks passed as a percentage and estimated costs; **new slide 39**, what the 8 checks mean (8/8, 7/8, 4/8); backup slides moved to 40–43 |
| Stand-alone slide | https://claude.ai/artifact/LnCE7R29CRVndumtNd38cR (private): the same ranking as one page, before the cost column was added; delete if unneeded |
| Previous passdown | `docs/PASSDOWN_R1B_10MIN.md` (PR #59) |

## Why

The owner asked for one slide ranking the 9 Claude rows of the r1b 10-minute
rerun (run 2) together with GLM-5.3 (run 1), then asked why Claude's cost was
n/a. Claude Code reports cost only in its final result event, which a session
stopped at the limit never writes. Pricing those sessions from their tokens
was blocked by an open item from PR #59: `pricing.py` disagreed with Claude
Code's own figures by up to 5× on the 5.5 models. This branch fixes the table
and uses it.

## What was wrong in `pricing.py`

Found by pricing the `modelUsage` of every finished Claude Code session under
`runs/` (218 model entries) and comparing with its `costUSD`:

| | Was | Now |
|---|---|---|
| Cache writes | priced as 5-minute writes (1.25× input) | Claude Code writes the main model's cache for **1 hour** (2× input): Opus $8, Sonnet $4, Haiku $0.20 per 1M; side calls still use 5-minute writes |
| Haiku 5.5, prompt over 100K tokens | flat $0.10 / $0.50 | **5× every rate** for that request; most requests in Haiku's 60-minute sessions are over 100K, hence the 4–5× gap |
| Haiku 5.5 cache read | $0.005 | $0.01 |
| Claude Code ids (`claude-opus-5-5`, …) | no row, so the $3/$15 fallback | same rows as `anthropic/claude-*-5.5` |

Final rates (USD per 1M: input, output, cache read, 5-min write, 1-h write):
Opus 5.5 4 / 20 / 0.20 / 5 / 8 · Sonnet 5.5 2 / 10 / 0.10 / 2.50 / 4 ·
Haiku 5.5 0.10 / 0.50 / 0.01 / 0.125 / 0.20, ×5 over 100K.

Result: **exact for all 43 finished Opus 5.5 and 43 Sonnet 5.5 sessions**.
Haiku, priced per request, is within about 5–16% of Claude Code's figure
(was 4–5× low); the rest is likely Claude Code's own background Haiku calls,
which the stream does not show, and the 5× long-context factor on cache
buckets is an assumption that fits but is not separately confirmed.

Note: the `claude-api` skill's cached table gave Sonnet 5.5 cache reads as
$0.20; Claude Code's figures only fit $0.10. Trust the session data.

## What was built (commit `8f1d093`)

* `pricing.Price` gains `cache_write_1h`, `long_context_over` and
  `long_context_factor`. `pricing.usage_cost_usd(model, usage)` prices one API
  request from its `usage` (5-min/1-h split from `usage.cache_creation`; no
  split means 5-min). The long-context tier is per request, so it must be
  summed per request, never applied to a session's totals.
* `agentic.session_cost_usd(lines)`: each reply in Claude Code's session
  record (one id per reply, largest output count kept), priced and summed.
  None for an empty record or an unknown model. Leaves out Claude Code's
  background calls (about 1% of Opus high's cost).
* New record field `cost_from_prices_usd`, set only when the session was
  stopped and a session record exists. `cost_estimate_usd` stays Claude
  Code's own figure; nothing overwrites it.
* Track boards (`leaderboard.py --track`) show the priced cost as `≈ $x.xx`
  and the note explains it. Ranking is unchanged (it still sorts on reported
  cost only). **The main board is unchanged.**
* Backfilled `cost_from_prices_usd` into the 8 stopped run-2 records
  (`20261105T144700Z` … `20261105T163050Z`, one line each). Run 1 attempts
  have no session record, so they stay n/a.
* `-cc` pair reports (`report.py`) now show a price reference with these real
  prices, since the ids have rows; before, it was hidden to avoid showing the
  $3/$15 fallback. `test_price_reference_hidden_when_unused_and_unpriced` was
  rewritten as `test_price_reference_shows_real_claude_code_prices`. Its
  single cache-write column shows the 5-minute rate only.

## Results: r1b 10-minute run 2, estimated cost at API list price

The Claude runs used the subscription; these are API-price equivalents.

| Row | Cost |
|---|---|
| Opus 5.5 high (finished at 7.6 min) | $1.14, Claude Code's own |
| Opus medium / low | ≈ $0.78 / $0.59 |
| Sonnet high / low / medium | ≈ $0.64 / $0.54 / $0.40 |
| Haiku high / low / medium | ≈ $0.07 / $0.06 / $0.05 (no request over 100K) |
| GLM-5.3 (run 1, opencode) | $1.59 Go credit |

Haiku uses the most tokens but costs about a tenth of Sonnet or Opus.

## How to finish or re-run

From the project folder (`ai-model-lifecycle/ai-model-lifecycle`), on the
home PC (it has the score cache and Docker):

```bash
git fetch fork && git checkout fix/claude-api-prices
python -m pytest -q tests/                        # full suite, see Tests below
python leaderboard.py --track r1b-10min-run2      # board shows ≈ costs
python leaderboard.py --track r1b-10min           # run 1: unchanged except the note
```

Then commit the two board files to the branch (or after merge), and copy the
new cost column onto deck slide 43 (run 2 raw data, 2 of 2), which still shows
n/a. Slide 38 already has the costs.

To price another stopped session by hand:

```python
import agentic
agentic.session_cost_usd(open("<record>.session.jsonl").readlines())
```

## Tests

* `tests/test_pricing.py`: 7 tests, including Opus high's $1.128846 to the
  cent and a sweep over every finished Opus and Sonnet session under `runs/`.
* Related suites (pricing, gateway, provider and cost, leaderboard, mlflow
  export): 113 passed, 1 skipped.
* Full suite on this machine (Python 3.10 venv), **before** the gateway test
  was rewritten: 402 passed, 1 failed (that test), 18 skipped. Not re-run
  since. **Re-run the full suite on the home PC before merging.**

## Gotchas

* **Regenerating a board re-scores every attempt unless the score cache has
  it.** The cache, `.mlflow_score_cache.json`, is git-ignored and lives only
  on the home PC. On another machine `leaderboard.py --track` takes about an
  hour of Docker scoring for r1b (it was stopped after 10 minutes here).
* **Price per request, not per session**, for Haiku: the 100K tier applies to
  a request's prompt. `modelUsage` totals cannot be priced exactly for Haiku.
* **Stream output counts are not usable** (logged before the reply ends);
  `session_cost_usd` reads the session record, which has the final counts.
* `pricing.py`'s older Claude rows (4.x, Sonnet 5) still use the 5% / 125%
  convention, not checked figures.
* This machine has no `gh` and no GitHub login: pushes and PRs are done by the
  owner (`! git push …` in the Claude Code prompt works).

## Open items

1. Open the PR (description drafted in the session), review, merge.
2. Re-run the full test suite on the home PC.
3. Regenerate both 10-minute boards and update deck slide 43.
4. Decide whether `-cc` pair reports should show the price reference (now
   shown, with real prices) or keep it hidden for Claude Code pairs.
5. Optional: the main board and run 1 could also use priced costs for any
   stopped Claude session; run 1 cannot (no session records).
6. Still open from PR #59: more 10-minute runs per row (one attempt per row
   is close to chance), and PR #58 (a harder, less memorizable r1b successor).
7. Share the deck from its Share menu when it should reach the peers.
