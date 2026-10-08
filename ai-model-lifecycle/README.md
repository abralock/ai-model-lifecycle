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
