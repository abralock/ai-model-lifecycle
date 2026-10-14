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
examples: **[SCORING.md](SCORING.md)**.

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

```bash
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
- Only Go's chat-completions models are wired up (`family: chat` in the
  `apis:` map): GLM, DeepSeek, Kimi, LongCat, MiMo, Hy, Space Bunny. The
  MiniMax/Qwen3.x (Anthropic-messages) and Grok/GPT-Luna (Responses) families
  are not.

To add another Go pair, copy an existing one in `models.yaml` and add the
models' Go list prices to `pricing.py` — no code changes needed.

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
