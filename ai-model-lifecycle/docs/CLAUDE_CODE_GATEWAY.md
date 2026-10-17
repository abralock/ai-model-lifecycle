# Plan: run the Claude pairs through Claude Code (personal subscription)

Status: **built, offline tests only; not run live yet** (2026-10-16, `tests/test_claude_code_gateway.py`) · written 2026-10-15 · owner: Abraham Lock

## Paste this into Claude Code to start

> Read `ai-model-lifecycle/docs/CLAUDE_CODE_GATEWAY.md` and implement it on a new
> branch `claude-code-gateway` off `main`. Write the offline tests first (section 6),
> then the code. Don't run any live model calls and don't commit or push: stop after
> `pytest -q` passes and show me the diff.

## 1. Goal

Add a third kind of gateway, `family: claude-code`, so the four Claude pairs can be
benchmarked with **my own Claude subscription** by calling the Claude Code CLI
(`claude -p`) instead of OpenRouter. It goes next to the two gateways that already exist:
OpenRouter (the default) and OpenCode Go (`family: chat` / `responses`).

Scope and rules:

- **Personal use only.** Runs on my machine, signed in to my own claude.ai account.
  The terms allow that ("an end user signing in to the unmodified Claude Code binary
  with their own Claude subscription"). They do **not** allow sharing the subscription
  or routing teammates' requests through it. See
  https://code.claude.com/docs/en/legal-and-compliance.
- **Never bill an API key by accident.** If `ANTHROPIC_API_KEY` or any other API/cloud
  credential is set, or `claude auth status` doesn't report `authMethod: "claude.ai"`,
  refuse to run (section 4.6).
- **Separate pairs.** Results go in new `*-cc` pairs and are never mixed with the
  OpenRouter scorecards. Claude Code's request differs from ours (its own CLI, no
  temperature control), so the numbers are a different measurement.

## 2. What was checked on 2026-10-15

Claude Code 2.1.300, signed in with `authMethod: "claude.ai"`, no API key in the environment.

All 7 models answered a one-line prompt, and `modelUsage` named the model asked for
(no silent fallback):

| Pair | Current | Target |
|---|---|---|
| Opus 4.8 → 5.5 | `claude-opus-4-8` ✅ | `claude-opus-5-5` ✅ |
| Sonnet 5 → 5.5 | `claude-sonnet-5` ✅ | `claude-sonnet-5-5` ✅ |
| Sonnet 4.6 → 5.5 | `claude-sonnet-4-6` ✅ | `claude-sonnet-5-5` ✅ |
| Haiku 4.5 → 5.5 | `claude-haiku-4-5` ✅ | `claude-haiku-5-5` ✅ |

**Claude Code's own instructions inflate every call unless they're replaced:**

| Flags | Extra input tokens per call ("Reply with exactly: OK") |
|---|---|
| defaults + `--tools ""` | 5,000–10,500, different per model (Sonnet 4.6 ≈ 10.5k, Opus 5.5 ≈ 8.2k) and with uneven cache hits |
| lean flags (section 4.2) | ≈ 630, same for every model |

So the lean flags are required, not optional: without them the cost and time
comparison inside a pair is skewed.

Also verified with the lean flags:
- The prompt can be sent on **stdin**. Real-suite prompts are 50k–110k tokens, too big
  for a command-line argument.
- `--effort low` is accepted.
- `--output-format json` returns one JSON object with: `result` (the answer text),
  `is_error`, `stop_reason` (`end_turn` seen), `api_error_status`, `usage`
  (`input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`,
  `output_tokens`), `modelUsage` (keyed by model id), `total_cost_usd`, `duration_ms`,
  `duration_api_ms`, `num_turns`, `session_id`.

Checked 2026-10-16 (Claude Code 2.1.301, docs only, no model call):
- The output limit is the env var `CLAUDE_CODE_MAX_OUTPUT_TOKENS`
  (https://code.claude.com/docs/en/env-vars). Claude Code lowers a value above a
  model's cap to the cap. The runner sets it to `max_tokens`.
- More credential variables than listed in 4.2 can move the CLI off the
  subscription (`ANTHROPIC_FOUNDRY_*`, `ANTHROPIC_AWS_*`, `ANTHROPIC_BEDROCK_*`,
  `ANTHROPIC_VERTEX_*`, `AWS_BEARER_TOKEN_BEDROCK`). The runner strips those too.

Not verified yet (check before relying on it):
- The exact error JSON when the subscription usage limit is hit. The runner
  stops on `"usage limit"` / `"rate limit"` / `"hit your limit"` in an error `result`.
- Whether `usage` reports thinking tokens separately (so far it doesn't).

## 3. Config changes

### `models.yaml`

Add the gateway under `apis:`:

```yaml
  claude-code:
    # Claude Code CLI (`claude -p`) on my own claude.ai subscription. Personal use
    # only — see docs/CLAUDE_CODE_GATEWAY.md. No base_url or key: the CLI's own login.
    family: claude-code
```

Add four pairs at the end of `pairs:`, with ids ending in `-cc`. Use Claude Code's model
ids (dashes, not OpenRouter's `anthropic/...` slugs):

```yaml
  - id: opus-4.8-vs-5.5-cc
    current: {id: claude-opus-4-8,  name: "Claude Opus 4.8 (CC)",  api: claude-code}
    target:  {id: claude-opus-5-5,  name: "Claude Opus 5.5 (CC)",  api: claude-code}
  - id: sonnet-5-vs-5.5-cc
    current: {id: claude-sonnet-5,   name: "Claude Sonnet 5 (CC)",   api: claude-code}
    target:  {id: claude-sonnet-5-5, name: "Claude Sonnet 5.5 (CC)", api: claude-code}
  - id: sonnet-4.6-vs-5.5-cc
    current: {id: claude-sonnet-4-6, name: "Claude Sonnet 4.6 (CC)", api: claude-code}
    target:  {id: claude-sonnet-5-5, name: "Claude Sonnet 5.5 (CC)", api: claude-code}
  - id: haiku-4.5-vs-5.5-cc
    current: {id: claude-haiku-4-5, name: "Claude Haiku 4.5 (CC)", api: claude-code}
    target:  {id: claude-haiku-5-5, name: "Claude Haiku 5.5 (CC)", api: claude-code}
```

Also update the `apis:` comment that still says `chat` "is the only family wired up".

### `common.py`

`ApiRef.base_url` is currently required. Give it a default of `""` so the
`claude-code` entry needs no URL. Leave `ApiRef.key()` as it is. The CLI has its own
login, and the runner must never pass a key to it.

## 4. Runner changes (`runner.py`)

### 4.1 Where

In `call_model`, the `api is not None` branch currently accepts families
`chat` / `responses`. Add `claude-code` as a third branch that **doesn't import or call
litellm**. Put it in its own function, e.g.
`_call_claude_code(model_slug, prompt, *, max_tokens, timeout_s, effort, max_retries, backoff_base_s) -> CallResult`.
Keep the existing retry and `CallResult` conventions, and keep `dry_run` behavior
identical to the other routes.

### 4.2 The command

```text
claude -p
  --model <model.id>
  --output-format json
  --tools ""
  --system-prompt <runner.SYSTEM_PROMPT>
  --setting-sources ""
  --strict-mcp-config
  --disable-slash-commands
  --exclude-dynamic-system-prompt-sections
  --no-session-persistence
  [--effort <level>]          # only when the suite sets one, see 4.4
```

- Prompt on **stdin** (`subprocess.run(..., input=prompt, text=True, capture_output=True, timeout=timeout_s)`).
- `cwd` = a fresh empty temp dir, so no project `CLAUDE.md`, settings or files leak in.
- Pass the command as a list (no shell).
- **Environment:** copy `os.environ` and remove `ANTHROPIC_API_KEY`,
  `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_BEDROCK`,
  `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`, so the CLI can only use the
  subscription login. Set the output-limit env var to `max_tokens` once confirmed (section 2).
- The `extra_headers` / `x-opencode-session` logic is Go-only and doesn't apply here.

### 4.3 Reading the result

| `CallResult` / `RunResult` field | From the CLI JSON |
|---|---|
| text | `result` (string); empty → `error = "empty completion (finish_reason=...)"` |
| finish_reason | `stop_reason`: `end_turn` → `stop`, `max_tokens` → `length`, anything else as-is |
| error | `is_error` true → a short message with `api_error_status` and the start of `result` |
| input_tokens | `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` (total prompt, same meaning as the other routes) |
| cache_read_tokens / cache_write_tokens | `cache_read_input_tokens` / `cache_creation_input_tokens` |
| output_tokens | `output_tokens` |
| latency | wall-clock around the subprocess (keep `duration_ms` in the record too if easy) |
| provider | `"claude-code"` (the `ApiRef.id`) |
| model check | if `modelUsage` exists and doesn't contain `model.id`, record an error ("served by X, asked for Y"); never score a different model's answer |
| cost | see 4.5 |

A CLI crash, non-JSON stdout or a timeout returns a `CallResult` with `error` set, like
the other routes. Never raise.

Note that `input_tokens` here includes cache tokens. If the price table is ever used for
these runs, this interacts with the cached-token bug in section 8: fix that first, or
don't price these runs from the table.

### 4.4 Thinking / effort

The real suite sends OpenRouter `reasoning: {"effort": "medium"}`. On this route, map
`cfg.reasoning["effort"]` to `--effort <level>`, the same value for both models of a pair.
If the suite sets no effort, pass no flag. Record the effort used, so the report header
("Thinking budget sent") is true for this route. The Go route currently isn't: see section 8.

### 4.5 Cost

The subscription doesn't bill per call. `total_cost_usd` is Claude Code's **estimate at
API list prices**. Record it, but don't present it as a bill:

- Add a new `RunResult` field `cost_estimate_usd: float | None` and leave
  `billed_cost_usd` as `None`.
- In `report.py`, use the cost in this order: billed → estimate → price table. Teach
  `_cost_source` a third label, e.g. `"Claude Code estimate at API prices (12/12)"`, and
  make the "cost uses the pricing.py table" warning account for estimates.
- Make the same change in `mlflow_export._call_cost`.

### 4.6 Pre-flight check (once per run, before any call)

Run `claude auth status` (it prints JSON) and refuse to start unless `loggedIn` is true
and `authMethod == "claude.ai"`. The error should say why (e.g. "Claude Code is logged
in with an API key — this route is for the personal subscription only"). Also fail
early with a clear message if the `claude` binary isn't on PATH.

### 4.7 Retries and the usage limit

- Retry like the other routes on transient failures (`api_error_status` 429/5xx,
  "overloaded").
- **Don't retry when the subscription usage limit is hit.** Stop the whole run with a
  clear message, and keep the runs already written. Get the exact error text from a real
  limit hit or the docs; until then, match conservatively on `"usage limit"` /
  `"rate limit"` in `result`.

## 5. Things to keep unchanged

- The OpenRouter and OpenCode Go routes, and all existing pairs and scorecards.
- Prompt building (`build_prompt`), the scorers and the scoring formula.
- `SYSTEM_PROMPT`: the same text goes in through `--system-prompt`.

## 6. Tests (offline, write first)

New file `tests/test_claude_code_gateway.py`, modeled on `tests/test_go_gateway.py`.
Replace `subprocess.run` with a fake, so no test ever calls the real CLI:

1. Config: `api: claude-code` resolves via `cfg.api_for`; `ApiRef` works without `base_url`.
2. The command has every lean flag from 4.2, `--model <id>`, and no `--effort` unless
   the suite sets one; the prompt goes on stdin, not argv.
3. The environment passed to the subprocess has none of the stripped variables, even
   when they are set in the test's environment.
4. A success JSON → text, tokens (prompt total includes cache tokens),
   `finish_reason == "stop"`, `provider == "claude-code"`, `cost_estimate_usd` set,
   `billed_cost_usd is None`.
5. `stop_reason: max_tokens` → `finish_reason == "length"`.
6. `is_error: true` → error recorded, no text graded.
7. `modelUsage` names a different model → error, not a scored answer.
8. Non-JSON output, non-zero exit and timeout → error, no exception.
9. Usage-limit error → no retry, run stops with a clear message.
10. Pre-flight: `authMethod` other than `claude.ai`, or `claude` missing → refuses to run.
11. `report.py`: cost source label for estimates; billed > estimate > table precedence.
12. `--effort` mapping from the real suite's `reasoning.effort`.

`pytest -q` must still pass. The two `test_r1_scorer.py` tests need Docker running.

## 7. Rollout (after review, step by step)

1. `pytest -q` passes, diff reviewed, then commit on `claude-code-gateway`.
2. Smoke test, about 2 small calls:
   `python runner.py --pair haiku-4.5-vs-5.5-cc --case r3_oracle_to_postgres`.
   Check the run JSON: model, tokens (prompt overhead ≈ 600 not 9k), finish reason,
   estimate.
3. Full Haiku pair: `python runner.py --pair haiku-4.5-vs-5.5-cc --repeats 3`, then
   `python report.py --pair haiku-4.5-vs-5.5-cc`.
4. Then Sonnet pairs, then Opus last. Expect the subscription limit to cap how much
   runs per day, especially Opus and the real suite (`--suite real`, 50k–110k tokens
   per prompt). Spread over several days if needed. Never mark a partial run as the
   scorecard.
5. When writing up results: label them "via Claude Code (subscription)", estimated cost,
   not comparable to the OpenRouter numbers.

## 8. Other open items from the 2026-10-15 review (separate small PRs)

Not part of this change, but found in the same review:

1. **Cached tokens counted twice in table-priced cost.** `pricing.cost_usd` charges all
   `input_tokens` at the full price and then adds `cache_read_tokens`, but
   OpenAI-style / Responses / DeepSeek usage already includes cached tokens in
   `input_tokens`. Affects the Go pairs (no billed cost). Fix: price
   `input − cache_read` at the input price.
2. **Done (#23).** **GLM thinking can be graded as the answer.** The chat route's empty-content
   fallback now reads `reasoning_content`, against the `models.yaml` comment ("never
   graded as the answer"). Decide which is intended; most likely, treat a
   reasoning-only reply as an empty answer (error).
3. `call_kwargs.update(extra_params)` lets `params:` in `models.yaml` overwrite
   `api_key` / `api_base` / `extra_headers`. Merge params first or reject those keys.
4. The real-suite report header prints "Thinking budget sent: {effort: medium}" for
   the Go route, but the Go route doesn't send it.
5. `cases/sources.ensure` ignores files that aren't in the lock, so a file removed from
   the lock stays in the prompt listing. Consider a `--clean` option.
6. `@requires_maven` in `tests/test_r1_scorer.py` doesn't notice Docker being down, so
   those tests fail instead of skipping.
