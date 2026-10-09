# ai-model-lifecycle — Gate 1 New Model Evaluation

Dev box for scoring AI models on fixed coding tasks (Time / Quality / Cost).

## Layout
- `cases/` — frozen golden test artifacts (R1/R3/R4/R5)
- `models.yaml` — candidate model matrix
- `runner.py` — litellm harness
- `scorers/` — deterministic checks
- `report.py` — scorecard (raw + normalized token/cost/time views)
- `docker/` — Postgres (and optional Oracle) containers for DB cases

## Setup
1. `cp .env.example .env` and fill `OPENROUTER_TOKEN`
2. `docker compose -f docker/docker-compose.yml up -d`
3. `uv sync` (or `pip install -r requirements.txt`)
4. `python runner.py --pair opus-4.8-vs-5.5`

## Harness (Gate 1)

```bash
# run the frozen cases against one pair (writes runs/<pair>/<model>.<case>.json)
python runner.py --pair opus-4.8-vs-5.5
python runner.py --pair opus-4.8-vs-5.5 --case r3_oracle_to_postgres
python runner.py --all-pairs

# build prompts only, no network (CI-safe)
python runner.py --pair opus-4.8-vs-5.5 --dry-run

# score + build the scorecard
python report.py --pair opus-4.8-vs-5.5           # live scorers
python report.py --pair opus-4.8-vs-5.5 --no-score # fast, uses runner ok-flag
python report.py --pair opus-4.8-vs-5.5 --date 20261008  # score one past run date

# individual scorers
python -m scorers.r1_scorer --output-file <model-output.txt>

# tests
pytest -q
```

## Scoring notes
- `report.py` scores **one run date** (latest by default) so runs from different
  prompt/scorer versions are never mixed. It reports pass rates with 95% Wilson
  intervals, a Fisher exact p-value for the current-vs-target gap, per-case
  passes/runs, and every failing run with its reason. Provider/API errors are
  listed separately and excluded from quality, time and cost.
- R1 needs Maven: local `mvn` if installed, otherwise Docker
  (`maven:3.9-eclipse-temurin-17`, deps cached in the `aidb_m2` volume). Without
  either, R1 build checks are unverified and the case fails.
- R4/R5 run the model's SQL with real `psql` (local, else inside the
  `aidb-postgres` container) in a throwaway schema per run.

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

Output runs to `runs/<pair_id>/` (gitignored), scorecard at `runs/<pair_id>/REPORT.md`.
