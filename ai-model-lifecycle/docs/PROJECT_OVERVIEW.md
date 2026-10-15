# Project Overview — ai-model-lifecycle (Gate 1)

> Reading notes taken on 2026-10-15. For how to operate the harness, see
> `README.md`, `RUN_AT_HOME.md`, `SCORING.md` and the `gate1-eval` skill.

## What this is

A **Gate 1 model-upgrade evaluation harness**: a *current* model and its
*target* (newer) model run the same fixed coding tasks; every answer is scored
automatically on **Time / Quality / Cost**; a scorecard is written per pair to
`runs/<pair>/REPORT.md`. It implements Gate 1 ("New Model Evaluation") of the
AI model lifecycle plan in `GATE1_BUILD_PLAN.md` (Gate 2 = capability
verification, later).

## Structure

| Path | Role |
|---|---|
| `runner.py` | litellm harness: temp=0, 32k max_tokens (128k for `real` suite), retry/backoff, per-run UTC run ids. OpenRouter pairs pinned to Amazon Bedrock (no fallbacks) so both models share infrastructure; `api: opencode-go` pairs go through the OpenCode Go subscription instead. |
| `models.yaml` | Pair matrix (`current` vs `target`), run defaults, gateway config, case lists per suite. |
| `cases/` | Frozen golden tasks (see below). |
| `scorers/` | Deterministic per-case checkers + `dispatch.py`. |
| `report.py` | Scorecard: Wilson CIs, Fisher p, normalized token/cost/time views, overall score (current = 100 baseline). |
| `verify_failures.py` | Re-scores failing runs; classifies MODEL / HARNESS? / FLAKY / INFRA. |
| `pricing.py` | Token price table (fallback when no billed cost; the source for Go pairs). |
| `mlflow_export.py` | Optional copy of results into MLflow (`runs/` stays source of truth). |
| `docker/` | Postgres 16 for the DB cases. |

## The tasks (cases)

**Default suite** (4 cases, from `models.yaml`):
- `r1_springboot2to3` — Spring Boot 2.7 → 3 migration; scored by real Maven build.
- `r3_oracle_to_postgres` — 2 Oracle PL/SQL procs → plpgsql; scored by Postgres parity against golden CSV.
- `r4_schema_load_optimize` — schema + bulk load + slow-query optimization; scored by EXPLAIN (runs the model's SQL with real `psql` in a throwaway schema).
- `r5_etl_dashboard` — ETL spec + dashboard schema; reconcile checks.

**`--suite real`** (scorecard `REPORT.real.md`): whole real codebases (~50–120k
tokens in prompt), fetched from pinned forks via `cases/sources.lock.json`
(SHA-256 per file): `r1b_jhipster_boot3` (Spring Boot 2.7→3) and
`r2_gwt_to_angular` (GWT → Angular 18). Needs one-time Docker caches
(`setup.sh` / `setup_e2e.sh`, ~3 GB).

## Key operating rules (from the gate1-eval skill)

1. Health check first: `docker compose -f docker/docker-compose.yml up -d`, then `pytest -q` must pass with nothing skipped.
2. Runs cost money — confirm before a full run; smoke-test with `--case r3_oracle_to_postgres` first.
3. A real evaluation is `--repeats 3`, all cases (never `--case` for a scorecard run).
4. Never report a failure without `verify_failures.py` evidence.
5. Both models must run on the same provider (`Provider (runs)` line in the report).
6. Cost should be `billed by OpenRouter (12/12)`; Go pairs correctly show `price table (pricing.py)`.
7. 12 runs/model is rarely significant — cite Fisher p, don't call winners on 1–2 task gaps.
8. Never read/print `.env`; no commits/pushes without human review.

## Current state of results (runs/)

| Pair | Status | Overall score |
|---|---|---|
| `opus-4.8-vs-5.5` | Full run, 12/12 quality both; 5.5 +141% slower, +24% costlier (p = 1.00) | ✅ |
| `sonnet-5-vs-5.5` | Full + real suite | **123.5** ✅ |
| `sonnet-4.6-vs-5.5` | Full | **112.7** ✅ |
| `haiku-4.5-vs-5.5` | Full + real suite | **111.1** ✅ |
| `glm-5.2-vs-5.3` | ⚠️ Partial only (smoke test, 1/4 cases) — not a scorecard | — |
| `gpt-5.6-luna-vs-6-luna` | Full run via OpenCode Go **Responses API** (new `family: responses` route, wired 2026-10-15). 12/12 quality both; 6 Luna +9.2% slower, −56.5% cheaper | **113.3** ✅ |

Notable config notes:
- GLM-5.x on Go is thinking-only; both GLM models use `reasoning_effort: low`
  to avoid burning the whole output budget on hidden reasoning.
- GPT Luna on Go is served only over the OpenAI Responses API — it uses the
  `opencode-go-responses` gateway entry (same base URL/key, `family: responses`),
  added to `runner.py` on 2026-10-15. Grok / Muse Spark share that endpoint.
- `deepseek-v4.1-flash-vs-v4-pro` pair is configured but has no runs yet.
- GPT Sol/Terra pairs from the plan are still commented out in `models.yaml`
  (check provider availability for both models before enabling).
