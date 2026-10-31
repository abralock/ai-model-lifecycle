# ai-model-lifecycle — Gate 1 New Model Evaluation

Dev box for scoring AI models on fixed coding tasks (Time / Quality / Cost).

## Layout
- `cases/` — frozen golden test artifacts (R1/R3/R4/R5)
- `models.yaml` — candidate model matrix
- `runner.py` — litellm harness
- `scorers/` — deterministic checks
- `report.py` — scorecard (raw + normalized token/cost/time views)
- `docker/` — Postgres container for the DB cases

## Setup

New to this repo, or running it on a home PC? Follow
**[RUN_AT_HOME.md](RUN_AT_HOME.md)** for a step-by-step guide (prerequisites,
Windows/WSL notes, cost, troubleshooting, opencode/Claude Code prompts).

To browse results in a web UI with history and side-by-side compare, see
**[MLFLOW.md](MLFLOW.md)** (optional; `runs/` stays the source of truth).

How the overall score and verdict in `REPORT.md` are calculated, with worked
examples: **[SCORING.md](SCORING.md)**. What the Time axis measures (one
request per assignment, thinking included; grading and retries excluded):
**[docs/LATENCY.md](docs/LATENCY.md)**.

Short version (Docker running, Python 3.11+):

```bash
cp .env.example .env                       # then set OPENROUTER_TOKEN
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
#   or: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
source .venv/bin/activate
docker compose -f docker/docker-compose.yml up -d
pytest -q                                  # must pass with nothing skipped
python runner.py --pair opus-4.8-vs-5.5 --repeats 3
python report.py --pair opus-4.8-vs-5.5
```

There is no `pyproject.toml`, so `uv sync` does not apply; install from
`requirements.txt` as above.

## Harness (Gate 1)

Two ways a model is tested; see [docs/AGENTIC.md](docs/AGENTIC.md):

* **Agentic migration (primary)** — `agentic.py`: the model works on the project
  the way a developer would (change code, build, test, fix) in a Docker sandbox
  until its goal is met, then the same acceptance check scores what it delivered.
* **Single-shot screening** — `runner.py`: one reply, nothing built or tested.
  Quick and cheap, and the only test every route can take, but not a migration.

```bash
# agentic migration: one-time setup, then a pair's Claude Code model on every task
docker build -t gate1-agent:latest docker/agent
claude setup-token        # then add CLAUDE_CODE_OAUTH_TOKEN=... to .env
python agentic.py --pair sonnet-5.5-cc-vs-deepseek-v4-pro --role current
python agentic.py --pair sonnet-5.5-cc-vs-deepseek-v4-pro --role current \
    --case r1b_jhipster_boot3 --repeats 3 --time-limit 3600   # -> runs/<pair>/agentic/<run>/REPORT.md
python leaderboard.py     # agentic ranking first, single-shot screening after it

# run the frozen cases against one pair (writes runs/<pair>/<model>.<case>.json)
python runner.py --pair opus-4.8-vs-5.5
python runner.py --pair opus-4.8-vs-5.5 --case r3_oracle_to_postgres
python runner.py --all-pairs

# build prompts only, no network, writes no run files (CI-safe)
python runner.py --pair opus-4.8-vs-5.5 --dry-run

# score + build the scorecard
python report.py --pair opus-4.8-vs-5.5           # live scorers
python report.py --pair opus-4.8-vs-5.5 --no-score # fast, uses runner ok-flag
python report.py --pair opus-4.8-vs-5.5 --list-runs              # run ids, complete/partial
python report.py --pair opus-4.8-vs-5.5 --run 20261009T143005Z   # score a past run
# Pass@T budgets: suite defaults (models.yaml time_budgets_s) or per report:
python report.py --pair opus-4.8-vs-5.5 --time-budget 30 --time-budget 60 --time-budget 120
# thinking-effort sweep (docs/LATENCY.md): one run id per level, then one table
python runner.py --pair opus-5.5-cc-vs-kimi-k3 --role current --effort low,medium,high,xhigh,max --repeats 3
python report.py --pair opus-5.5-cc-vs-kimi-k3 --by-effort        # -> REPORT.effort.md
# CI-style repair rounds (separate from the score): show a failed answer's model what
# CI reported and let it fix up its answer, up to N rounds -> runs/<pair>/repair/<run>/REPORT.md
python repair.py --pair opus-5.5-cc-vs-kimi-k3 --suite real --run <run id> --rounds 3
# docs-assisted run (separate from the score): Claude Code models may look up current
# library docs through Context7's MCP server; every lookup is recorded. Optional
# CONTEXT7_API_KEY in .env raises Context7's rate limits.
python runner.py --pair opus-5.5-cc-vs-kimi-k3 --suite real --role current --docs context7
python report.py --pair opus-5.5-cc-vs-kimi-k3 --suite real --run <run id>

# individual scorers
python -m scorers.r1_scorer --output-file <model-output.txt>

# tests
pytest -q
```

## Scoring notes
- Each `runner.py` invocation gets one **run id** (its UTC start time, e.g.
  `20261009T143005Z`) stamped on every file it writes. `report.py` scores **one
  run** (by default the latest *complete* one: every configured case, both
  models; a newer partial run such as `--case r4_...` is named in the header but
  not scored — use `--run <id>` for it), so a re-run — even the same day, or one that
  crosses midnight UTC — never mixes with or overwrites an earlier one. Legacy
  date-only runs (`20261008`) keep working as run ids. `REPORT.md` only changes
  when `report.py` is run: check its `Run:` header line. It reports pass rates with 95% Wilson
  intervals, a Fisher exact p-value for the current-vs-target gap, per-case
  passes/runs, and every failing run with its reason. Provider/API errors are
  listed separately and excluded from quality, time and cost.
- R1 needs Maven: local `mvn` if installed, otherwise Docker
  (`maven:3.9-eclipse-temurin-17`, deps cached in the `aidb_m2` volume). Without
  either, R1 build checks are unverified and the case fails.
- R4/R5 run the model's SQL with real `psql` (local, else inside the
  `aidb-postgres` container) in a throwaway schema per run.

## OpenCode Go (open-weight models)

Pairs tagged `api: opencode-go` (e.g. `glm-5.2-vs-5.3`,
`deepseek-v4.1-flash-vs-v4-pro`) run through an
[OpenCode Go](https://opencode.ai/v2/docs/console/go) subscription instead of
OpenRouter. Same cases, scorers, scorecard and overall-score math; the only
differences:

- **Key:** create it at [opencode.ai/console](https://opencode.ai/console)
  (subscribe to Go → copy the API key), then set `OPENCODE_GO_API_KEY` in `.env`.
- **Cost** comes from the `pricing.py` table at Go's list prices — that spend
  counts against the subscription's monthly quota, it is not marginal billing.
  The `Cost source` line says `price table (pricing.py)` for these pairs.
- **Provider pinning does not apply** — Go is one gateway, so both models share
  its infrastructure by construction. Watch the quota caps (≈20% of the monthly
  limit per 5 h per model) when running `--repeats 3` across several Go pairs.
- Go's chat-completions models are wired up (`family: chat` in the
  `apis:` map): GLM, DeepSeek, Kimi, LongCat, MiMo, Hy, Space Bunny. So is
  the Responses API family (`family: responses`, via the
  `opencode-go-responses` gateway entry): GPT Luna (pair
  `gpt-5.6-luna-vs-6-luna`); Grok and Muse Spark share that endpoint. And the
  Anthropic-messages family via a model-level `family: messages` override
  (pair `qwen3.8-flash-vs-glm-5.3-flash`); MiniMax shares that dialect.

To add another Go pair, copy an existing one in `models.yaml` and add the
models' Go list prices to `pricing.py` — no code changes needed.

## Claude Code (personal subscription)

Pairs ending in `-cc` (`opus-4.8-vs-5.5-cc`, `sonnet-5-vs-5.5-cc`,
`sonnet-4.6-vs-5.5-cc`, `haiku-4.5-vs-5.5-cc`) run the same Claude models
through the Claude Code CLI (`claude -p`) on the owner's **personal claude.ai
subscription** instead of OpenRouter. Personal use only — plan, verified CLI
behavior and open questions: **[docs/CLAUDE_CODE_GATEWAY.md](docs/CLAUDE_CODE_GATEWAY.md)**.
Same cases, scorers and scorecard math; the differences:

- **No key.** The CLI's own login is used. The runner refuses to start unless
  `claude auth status` reports `authMethod: "claude.ai"`, and it strips API /
  cloud-provider credential variables from the CLI's environment, so a run can
  never bill an API account by accident.
- **Cost is an estimate**, not a bill: Claude Code's `total_cost_usd` at API
  list prices, recorded as `cost_estimate_usd` (`billed_cost_usd` stays null).
  The `Cost source` line reads `Claude Code estimate at API prices (12/12)`.
- **Subscription usage limit:** hitting it stops the whole run (exit code 3).
  Runs already written are kept, but that is a partial run, not a scorecard;
  re-run after the limit resets.
- **Output-limit handling:** an answer that runs past the output limit is
  recorded as cut off (`finish_reason: length`, scored as a FAIL) — Claude Code
  otherwise continues it over several requests and returns only the last part.
  Each run file records `num_turns` and `duration_api_ms`.
- `-cc` scorecards are a **different measurement** (Claude Code's own request,
  no temperature control, cache behavior the harness doesn't control). Never
  compare them number-for-number with the OpenRouter scorecards.

## Layout (pilot)
- `models.yaml` — candidate matrix (pair-agnostic; add pairs to scale to 7)
- `runner.py` — litellm harness (temp=0, fixed max_tokens, retry/backoff)
- `common.py` / `pricing.py` — config, run IO, token price table
- `cases/` — frozen golden artifacts:
  - `r1_springboot2to3/` — Boot 2.7 Maven module (javax.*, spring.factories)
  - `r3_oracle_to_postgres/` — 2 Oracle PL/SQL procs + golden plpgsql + golden CSV
  - `r4_schema_load_optimize/` — schema + bulk seeder + slow target query
  - `r5_etl_dashboard/` — ETL spec + dashboard schema
- `scorers/` — `r1`(mvn) `r3`(postgres parity) `r4`(explain) `r5`(reconcile) + `dispatch.py`
- `report.py` — scorecard with raw + normalized token/cost/time views
- `docker/` — Postgres 16 for the data cases

Output runs to `runs/<pair_id>/` (committed as the durable record), scorecard at `runs/<pair_id>/REPORT.md`.

## Real-project suite (`--suite real`)

Two cases built from real open-source projects, scored by their own tests;
scorecard at `runs/<pair_id>/REPORT.real.md`:

| Case | Fetched from (our fork) | Forked from (upstream) | Branch · commit | Task |
|---|---|---|---|---|
| `r1b_jhipster_boot3` | [abralock/jhipster-sample-app](https://github.com/abralock/jhipster-sample-app) | [jhipster/jhipster-sample-app](https://github.com/jhipster/jhipster-sample-app) | `main` · [`7d39dfa`](https://github.com/abralock/jhipster-sample-app/tree/7d39dfaa9edeae5ba8322bb44b7d7487764ef934) (tag `v7.9.3`) | Spring Boot 2.7 → 3 |
| `r2_gwt_to_angular` | [abralock/GWTP-Samples](https://github.com/abralock/GWTP-Samples) | [ArcBees/GWTP-Samples](https://github.com/ArcBees/GWTP-Samples) | `master` · [`7dce06a`](https://github.com/abralock/GWTP-Samples/tree/7dce06a479529944de10eab06b9b38d2e944926d/carstore) (`carstore/`) | GWT → Angular 18 |

The project code is **not committed here**: it is fetched from the forks into
`cases/r1b_jhipster_boot3/project/` and `cases/r2_gwt_to_angular/{gwt,e2e}/`
(gitignored). `cases/sources.lock.json` pins each fork's commit and the SHA-256
of every file used, so a fetch reproduces exactly the prompt the committed runs
used, and a changed fork is refused. The runner and scorers fetch on first use;
to fetch or check by hand:

```bash
python -m cases.sources            # fetch (needs git + network once)
python -m cases.sources --check    # verify only
```

The scorers also need one-time caches (Docker, about 3 GB):
`bash cases/r2_gwt_to_angular/setup.sh` and
`bash cases/r1b_jhipster_boot3/setup_e2e.sh`. Then:

```bash
python runner.py --pair sonnet-5-vs-5.5 --suite real --repeats 3
python report.py --pair sonnet-5-vs-5.5 --suite real
```
