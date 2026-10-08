#!/usr/bin/env python3
"""audits/rescore_r4_r5.py — re-score the opus-4.8-vs-5.5 R4/R5 runs.

Loads each model's OWN R4 source tables (continuity chain R4 -> R5), then runs
the R5 scorer against that model's R5 output. Also re-runs the R4 scorer.

This does NOT touch runs/*.json (the model outputs are ground truth) and makes
no live model calls.

Run:  .venv/bin/python -m audits.rescore_r4_r5
"""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg2

from common import RUNS_DIR
from scorers import r4_scorer, r5_scorer
from scorers.base import parse_files

PAIR = "opus-4.8-vs-5.5"
RUNS = RUNS_DIR / PAIR
DSN = "host=localhost port=5432 dbname=aidb user=ai password=ai"

MODELS = ("anthropic__claude-opus-4.8", "anthropic__claude-opus-5.5")


def load(case: str, model: str) -> str:
    import glob
    import json

    f = glob.glob(str(RUNS / f"{model}.{case}.*.json"))[0]
    return json.loads(open(f, encoding="utf-8").read())["output_text"]


def apply_r4_source(model: str, dsn: str = DSN) -> None:
    """Materialise `model`'s own R4 dataset as the R5 source tables."""
    sql = "\n".join(parse_files(load("r4_schema_load_optimize", model)).values())
    sql, _ = r4_scorer.strip_maintenance(sql)
    # drop the model's trailing self-verification EXPLAIN (returns rows)
    i = sql.rfind("EXPLAIN")
    if i != -1:
        sql = sql[:i]
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for t in ("order_items", "orders", "products", "customers"):
                cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
            cur.execute(sql)
            cur.execute("ANALYZE orders; ANALYZE order_items;")
    finally:
        conn.close()


def main() -> int:
    for model in MODELS:
        print("=" * 70)
        print(model)
        print("=" * 70)
        r4 = r4_scorer.score(load("r4_schema_load_optimize", model), model_slug=model)
        print(f"R4: passed={r4.passed}  reason={r4.reason}")
        print(f"    checks={r4.checks}")

        apply_r4_source(model)
        r5 = r5_scorer.score(load("r5_etl_dashboard", model), model_slug=model)
        print(f"R5: passed={r5.passed}  reason={r5.reason}")
        print(f"    checks={r5.checks}")
        for k in ("source_order_count", "loaded_order_count", "etl_log", "dash_rows", "error"):
            if k in r5.details:
                print(f"    {k}={r5.details[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
