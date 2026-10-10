# Browse Gate 1 results in MLflow (optional)

`mlflow_export.py` copies Gate 1 results into an MLflow server, so you can
filter, chart and compare runs in a web UI instead of reading `REPORT.md` files.

It is **optional and read-only**: the run files in `runs/` stay the source of
truth and are still reviewed through pull requests. MLflow is a browsable copy.
Nothing in `runner.py` or `report.py` needs MLflow.

---

## For teammates: view the team's results (quick start)

You don't need to run any models or spend anything on OpenRouter: every result
is already in `runs/` in Git. You rebuild the same MLflow view on your machine.

**Before you start:** finish RUN_AT_HOME.md sections 1–2 (Docker, Python
environment, `.env`, `pytest -q` passes). Your OpenRouter key isn't used for
this; the Postgres settings in `.env` are.

```bash
git pull                                                              # latest runs/
source .venv/bin/activate
docker compose -f docker/docker-compose.yml --profile mlflow up -d    # Postgres + MLflow
uv pip install --python .venv/bin/python -r requirements-mlflow.txt  # once
python mlflow_export.py --all-pairs --all-runs                        # load every result
```

Then open **http://127.0.0.1:5050**.

- The first export takes **about 10 minutes**: every answer is re-checked by the
  same scorers `report.py` uses (R1 runs Maven builds). Later exports only add
  new runs and take seconds.
- Your numbers should match each pair's `REPORT.md`. Known exception: the R4
  index check can rarely flip on a borderline answer (Postgres samples rows
  when estimating), so one R4 result may occasionally differ.
- After someone pushes new results: `git pull`, then run the export again.
- **To compare current vs target:** open an experiment (e.g. `Gate1 /
  haiku-4.5-vs-5.5`), search `tags.level = 'model'`, switch to **Chart view**.
  Current is blue, target orange. Details in section 4.
- Done? `docker compose -f docker/docker-compose.yml --profile mlflow stop`

---

## 1. Start MLflow

MLflow runs in Docker next to Postgres. It only starts with `--profile mlflow`,
so the normal `docker compose ... up -d` is unchanged.

```bash
docker compose -f docker/docker-compose.yml --profile mlflow up -d
```

Open **http://127.0.0.1:5050**.

- Image: `ghcr.io/mlflow/mlflow:v3.17.0` (about 1.3 GB, downloaded once).
- Data is kept in the Docker volume `aidb_mlflow`, so it survives restarts.
- Port **5050**, not MLflow's usual 5000: on macOS, port 5000 is taken by the
  AirPlay Receiver.

## 2. Install the client

In the same environment as the harness (see RUN_AT_HOME.md, section 2.3):

```bash
uv pip install --python .venv/bin/python -r requirements-mlflow.txt
# or: .venv/bin/pip install -r requirements-mlflow.txt
```

The client version must match the server image (3.17).

## 3. Export results

Postgres must be running and Docker available: pass/fail is worked out by the
same scorers `report.py` uses.

```bash
python mlflow_export.py --all-pairs                        # latest complete run per pair
python mlflow_export.py --all-pairs --all-runs             # every complete run (history)
python mlflow_export.py --pair haiku-4.5-vs-5.5 --run 20261009T154316Z
```

- A run already exported for the same `--source` is skipped, so it's safe to
  run again after every new evaluation.
- Partial runs (missing tasks) are never exported.
- Scores are cached in `.mlflow_score_cache.json` (ignored by Git). The cache is
  keyed by the scorer code, so changing a scorer re-scores automatically.
- The first export of many runs takes a few minutes (R1 runs Maven builds);
  later exports are fast.

Results from someone else's checkout, labelled so they stay separate:

```bash
python mlflow_export.py --pair haiku-4.5-vs-5.5 --runs-dir ../their-checkout/runs --source teammate-laptop
```

A different server (for example SageMaker managed MLflow):

```bash
MLFLOW_TRACKING_URI=<server URI> python mlflow_export.py --all-pairs
```

## 4. What you see in MLflow

| MLflow item | Gate 1 meaning |
|---|---|
| Experiment `Gate1 / <pair>` | One model pair |
| Run `<run id> (<source>)` | One harness run. Metrics: `overall_score`, `fisher_p`, and **`current_*` / `target_*` pairs** for every model metric below (e.g. `current_cost_component` vs `target_cost_component`). Tags: `verdict`, `providers`, `cost_source`, `repeats`. Artifacts: **`comparison.png`** (current in blue vs target in orange: pass rate overall and per task, time, cost, cost per passed task, output tokens), `REPORT.md` and `calls.json` (one row per call). |
| ↳ Model run `<model> (current/target)` | One model in that run, coloured **blue (current) / orange (target)**. Metrics with the **same names for both models**: `pass_rate`, `passes`, `cost_usd`, `cost_per_task_usd`, `cost_per_passed_task_usd`, `mean_latency_s`, `output_tokens`, `pass_rate_r1` / `r3` / `r4` / `r5` per task, and the score components `quality_component`, `cost_component`, `time_component`, `overall_score` (current = 100). |
| ↳↳ Call run `<model> · <task> · rep N` | One model call: `passed`, `latency_s`, tokens, `cost_usd`; tags `result` (PASS/FAIL/INFRA) and `failure_reason`; artifact `output.txt` (the model's full answer). |

### See current vs target in charts (no setup)

1. Open the experiment (e.g. `Gate1 / haiku-4.5-vs-5.5`).
2. In the search box, enter `tags.level = 'model'`.
3. Switch the runs list to **Chart view** (chart icon next to the table icon).

Every metric (`pass_rate`, `cost_component`, `time_component`, `cost_per_task_usd`,
`mean_latency_s`, ...) gets one interactive chart with a **blue bar for the current
model and an orange bar for the target**. Untick runs in the list to keep only
the run you care about, or leave them all to see how results moved between runs.

A ready-made picture of one run: open the run → **Artifacts** → `comparison.png`.

### On a run's Model metrics tab

The run's own page lists `current_*` and `target_*` metrics as separate charts.
To put a pair in one chart (e.g. `current_cost_component` vs
`target_cost_component`), add a bar chart there and pick both metrics. MLflow
saves that layout in your browser, per run, so it can't be set up by the export;
the Chart view above needs no setup.

### Follow results over time

To follow one model over time, add `and params.role = 'target'`. For the pair's
overall score across runs, search `tags.level = 'run'` instead.

Other handy searches:

- **Every failure:** `tags.result = 'FAIL'`, then open a call run to read
  `failure_reason` and `output.txt`.
- **One task across runs:** `params.case = 'r4_schema_load_optimize'`.

## 5. Stop or reset

```bash
docker compose -f docker/docker-compose.yml --profile mlflow stop     # keep data
docker compose -f docker/docker-compose.yml --profile mlflow down     # remove containers, keep data
docker volume rm docker_aidb_mlflow                                   # delete all MLflow data
```

Deleting MLflow data loses nothing permanent: re-export from `runs/`.
