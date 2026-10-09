"""scorers/r5_scorer.py — ETL into Dashboard + reconciliation scorer.

Steps:
  1. Build a fresh, isolated scratch schema (`r5_<uuid>`) holding a FIXED source
     dataset: R4's frozen `schema.sql` + the deterministic R4 seeder (20k orders),
     extended with the cases etl_spec.md §5 exists for — multi-category orders
     (extra lines in other categories) and COMPLETED orders with no lines. The
     R4 seed alone has exactly one line per order, which would let a naive
     line-grain rollup pass. Every model is scored on identical data,
     independent of whatever earlier scoring left in the database.
  2. Apply the dashboard schema, then run the MODEL's ETL with psql semantics
     (see `scorers.base.run_psql`).
  3. Verify reconciliation: source_order_count - loaded_order_count == 0
     (both from the model's OWN etl_run_log row, and independently recomputed).
  4. Verify idempotency: run the ETL twice; dashboard row counts must be stable.
  5. Verify both dashboard tables are non-empty.
  6. Drop the scratch schema.

Note: the R3->R4->R5 *continuity* chain (R5 on the model's own R4 output) is
deliberately not scored here — mixing it in made results depend on scoring
order. It should be its own explicit check.

Robustness: no Postgres / malformed SQL -> structured fail, never a crash.

Usage:
    python -m scorers.r5_scorer --output-file <model-output.txt>
"""

from __future__ import annotations

from pathlib import Path

from .base import (
    ScoreResult,
    cli,
    create_schema,
    drop_schema,
    new_schema_name,
    parse_files,
    pg_available,
    run_psql,
)

CASE_ID = "r5_etl_dashboard"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID
R4_DIR = CASE_DIR.parent / "r4_schema_load_optimize"
FIXTURE_ROWS = 20_000

# Applied after the R4 seed (product category = product_id % 5, so product_id+1
# is always a different category). New lines get higher order_item_ids, so the
# seed's line stays each order's controlling line.
FIXTURE_EXTRA_SQL = f"""
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
SELECT {FIXTURE_ROWS} + o.order_id, o.order_id, 1 + (oi.product_id % 200), 2, 19.99
FROM   orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE  o.order_id % 2 = 0;                       -- 2-category orders

INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
SELECT {2 * FIXTURE_ROWS} + o.order_id, o.order_id, 1 + ((oi.product_id + 1) % 200), 1, 5.00
FROM   orders o JOIN order_items oi ON oi.order_id = o.order_id
WHERE  o.order_id % 5 = 0 AND oi.order_item_id <= {FIXTURE_ROWS};   -- 3-category

DELETE FROM order_items WHERE order_id % 97 = 0;  -- orders with no lines
ANALYZE order_items;
"""


def _table_counts(cur, table: str) -> int | None:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        return int(cur.fetchone()[0])
    except Exception:
        return None


def build_fixture(dsn: str, schema: str) -> None:
    """Create the fixed R5 source dataset + empty dashboard tables in `schema`."""
    import psycopg2  # type: ignore

    from cases.r4_schema_load_optimize import seed as r4_seed  # type: ignore

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}";')
        cur.execute((R4_DIR / "schema.sql").read_text(encoding="utf-8"))
        cur.execute(r4_seed.build_sql(rows=FIXTURE_ROWS))
        cur.execute(FIXTURE_EXTRA_SQL)
        cur.execute((CASE_DIR / "dashboard_schema.sql").read_text(encoding="utf-8"))


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

    schema = new_schema_name("r5")
    try:
        import psycopg2  # type: ignore

        create_schema(dsn, schema)
        build_fixture(dsn, schema)

        rc, out = run_psql(sql_text, schema)
        res.checks["etl_runs"] = rc == 0
        if rc != 0:
            res.details["error"] = f"model ETL failed under psql (rc={rc}): {out[-600:]}"

        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{schema}";')

                # --- reconciliation (independent recompute) ---------------- #
                cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED';")
                src = int(cur.fetchone()[0])
                cur.execute("SELECT COALESCE(SUM(order_count), 0) FROM dash_revenue_by_category;")
                loaded = int(cur.fetchone()[0])
                res.details["source_order_count"] = src
                res.details["loaded_order_count"] = loaded
                # an empty rollup must not "reconcile" to zero
                res.checks["reconciliation_zero"] = (src == loaded) and (loaded > 0)

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

        # --- idempotency: run the ETL a 2nd time ----------------------- #
        first = (cat_n, cty_n)
        rc2, out2 = run_psql(sql_text, schema)
        with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}";')
            second = (
                _table_counts(cur, "dash_revenue_by_category"),
                _table_counts(cur, "dash_revenue_by_country"),
            )
            cur.execute("SELECT COALESCE(SUM(order_count), 0) FROM dash_revenue_by_category;")
            loaded2 = int(cur.fetchone()[0])
        res.details["idempotent_counts"] = {"first": first, "second": second}
        res.checks["idempotent"] = rc2 == 0 and first == second and loaded2 == loaded
    except Exception as exc:  # noqa: BLE001
        res.details["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        drop_schema(dsn, schema)

    required = ["etl_runs", "reconciliation_zero", "log_mismatch_zero", "dataset_loads", "idempotent"]
    res.passed = all(res.checks.get(k, False) for k in required)
    res.score = 1.0 if res.passed else 0.0
    if not res.passed:
        res.reason = "failed checks: " + ", ".join(k for k in required if not res.checks.get(k))
    else:
        res.reason = "ETL idempotent, dashboard loaded, reconciliation mismatch = 0"
    return res


if __name__ == "__main__":
    raise SystemExit(cli(score))
