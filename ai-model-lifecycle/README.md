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

# individual scorers
python -m scorers.r1_scorer --output-file <model-output.txt>

# tests
pytest -q
```

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
