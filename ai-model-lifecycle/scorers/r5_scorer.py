"""scorers/r5_scorer.py — ETL into Dashboard + reconciliation scorer.

Steps:
  1. Ensure source tables exist (reuse R4 seed if empty; otherwise use whatever
     the continuity chain already produced).
  2. Apply the dashboard schema, then run the MODEL's ETL SQL.
  3. Verify reconciliation: source_order_count - loaded_order_count == 0
     (both from the model's OWN etl_run_log row, and independently recomputed).
  4. Verify idempotency: run the ETL twice; dashboard row counts must be stable.
  5. Verify both dashboard tables are non-empty.

Robustness: no Postgres / malformed SQL -> structured fail, never a crash.

Usage:
    python -m scorers.r5_scorer --output-file <model-output.txt>
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import ScoreResult, cli, parse_files, pg_available

CASE_ID = "r5_etl_dashboard"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID


def _table_counts(cur, table: str) -> int | None:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        return int(cur.fetchone()[0])
    except Exception:
        return None


def score(output_text: str, *, model_slug: str = "", workdir: Path | None = None) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)

    files = parse_files(output_text)
    sql_text = "\n".join(files.values()) if files else output_text
    if not sql_text.strip():
        res.reason = "no SQL found in model output"
        return res

    ok, dsn = pg_available()
    if not ok:
        res.details["postgres"] = dsn
        res.passed = False
        res.reason = f"postgres unavailable ({dsn})"
        return res

    try:
        import psycopg2  # type: ignore

        # Ensure source tables exist with data. If R4 hasn't run in this DB, seed
        # a default set so R5 is independently scorable.
        from cases.r4_schema_load_optimize import seed as r4_seed  # type: ignore

        dash_schema = (CASE_DIR / "dashboard_schema.sql").read_text(encoding="utf-8")

        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = 'orders';"
                )
                has_orders = cur.fetchone()[0] > 0
                order_count = _table_counts(cur, "orders") if has_orders else 0
                if not has_orders or not order_count:
                    cur.execute(
                        "DROP TABLE IF EXISTS order_items, orders, products, customers CASCADE;"
                    )
                    conn.commit()
                    cur.execute(
                        (CASE_DIR.parent / "r4_schema_load_optimize" / "schema.sql").read_text(
                            encoding="utf-8"
                        )
                    )
                    conn.commit()
                    cur.execute(r4_seed.build_sql(rows=20_000))
                    conn.commit()

                # apply dashboard schema, then the model's ETL
                cur.execute(dash_schema)
                conn.commit()
                cur.execute(sql_text)
                conn.commit()

                # --- reconciliation (independent recompute) ---------------- #
                cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED';")
                src = int(cur.fetchone()[0])
                cur.execute("SELECT COALESCE(SUM(order_count), 0) FROM dash_revenue_by_category;")
                loaded = int(cur.fetchone()[0])
                res.details["source_order_count"] = src
                res.details["loaded_order_count"] = loaded
                res.checks["reconciliation_zero"] = (src - loaded) == 0

                # --- model's own etl_run_log row --------------------------- #
                cur.execute(
                    "SELECT source_order_count, loaded_order_count, mismatch "
                    "FROM etl_run_log ORDER BY run_id DESC LIMIT 1;"
                )
                row = cur.fetchone()
                if row:
                    res.details["etl_log"] = {
                        "source_order_count": int(row[0]),
                        "loaded_order_count": int(row[1]),
                        "mismatch": int(row[2]),
                    }
                    res.checks["log_mismatch_zero"] = int(row[2]) == 0
                else:
                    res.checks["log_mismatch_zero"] = False
                    res.details["etl_log"] = None

                # --- dataset non-empty ------------------------------------- #
                cat_n = _table_counts(cur, "dash_revenue_by_category") or 0
                cty_n = _table_counts(cur, "dash_revenue_by_country") or 0
                res.details["dash_rows"] = {"category": cat_n, "country": cty_n}
                res.checks["dataset_loads"] = cat_n > 0 and cty_n > 0

                # --- idempotency: run ETL a 2nd time ----------------------- #
                first = (cat_n, cty_n)
                cur.execute("DELETE FROM etl_run_log;")
                cur.execute(sql_text)
                conn.commit()
                second = (
                    _table_counts(cur, "dash_revenue_by_category"),
                    _table_counts(cur, "dash_revenue_by_country"),
                )
                res.details["idempotent_counts"] = {"first": first, "second": second}
                res.checks["idempotent"] = first == second
            conn.rollback()
    except Exception as exc:  # noqa: BLE001
        for k in ("reconciliation_zero", "log_mismatch_zero", "dataset_loads", "idempotent"):
            res.checks.setdefault(k, False)
        res.details["error"] = f"{type(exc).__name__}: {exc}"

    required = ["reconciliation_zero", "log_mismatch_zero", "dataset_loads", "idempotent"]
    res.passed = all(res.checks.get(k, False) for k in required)
    res.score = 1.0 if res.passed else 0.0
    if not res.passed:
        res.reason = "failed checks: " + ", ".join(k for k in required if not res.checks.get(k))
    else:
        res.reason = "ETL idempotent, dashboard loaded, reconciliation mismatch = 0"
    return res


if __name__ == "__main__":
    raise SystemExit(cli(score))
