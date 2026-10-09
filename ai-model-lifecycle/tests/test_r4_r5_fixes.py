"""tests/test_r4_r5_fixes.py — R4/R5 scorer soundness.

R4: model scripts run with psql semantics in an isolated schema, so psql-valid
    scripts (VACUUM in any form, `\\set`, explicit BEGIN/COMMIT) are judged on
    schema + load + index, not on how the harness happens to execute SQL.
R5: every model is scored on the same fixed dataset in an isolated schema; the
    reconciliation gate is passable at order grain, rejects the line-grain
    rollup (multi-category double count), and rejects an empty rollup.
Both: no scratch schema or public table survives scoring.

Pure-logic tests run offline; DB-backed tests auto-skip without Postgres.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from common import load_env
from scorers import r4_scorer, r5_scorer
from scorers.base import pg_available, pg_dsn

load_env()
_HAS_PG = pg_available()[0]
requires_pg = pytest.mark.skipif(not _HAS_PG, reason="postgres not reachable")

R4_DIR = Path(__file__).resolve().parent.parent / "cases" / "r4_schema_load_optimize"


def _fenced(path: str, body: str) -> str:
    return f"### FILE: {path}\n```sql\n{body}\n```\n"


def _r4_solution(tail: str = "", head: str = "") -> str:
    """A correct R4 answer: frozen DDL + deterministic seed + covering index."""
    from cases.r4_schema_load_optimize import seed

    body = (
        head
        + (R4_DIR / "schema.sql").read_text(encoding="utf-8")
        + seed.build_sql(rows=100_000)
        + "\nCREATE INDEX idx_orders_status_date ON orders (status, order_date) INCLUDE (order_id);\n"
        + "CREATE INDEX idx_order_items_order ON order_items (order_id);\n"
        + tail
    )
    return _fenced("solution.sql", body)


def _scratch_schemas() -> list[str]:
    import psycopg2  # type: ignore

    with psycopg2.connect(pg_dsn()) as conn, conn.cursor() as cur:
        cur.execute("SELECT nspname FROM pg_namespace WHERE nspname ~ '^r[45]_[0-9a-f]{12}$';")
        return [r[0] for r in cur.fetchall()]


# --------------------------------------------------------------------------- #
# R4                                                                           #
# --------------------------------------------------------------------------- #
@requires_pg
@pytest.mark.parametrize("tail,head", [
    ("", ""),
    ("VACUUM ANALYZE orders;\n", ""),
    ("VACUUM (ANALYZE) customers;\nVACUUM (ANALYZE) orders;\n", ""),   # Opus 5.5's form
    ("", "\\set ON_ERROR_STOP on\nBEGIN;\n"),                            # psql meta + txn
], ids=["plain", "vacuum-analyze", "vacuum-paren-analyze", "psql-meta-begin"])
def test_r4_psql_valid_solution_passes(tail, head):
    if "BEGIN" in head:
        tail += "COMMIT;\n"
    r = r4_scorer.score(_r4_solution(tail, head), model_slug="t/m")
    assert r.passed is True, f"{r.reason} / {r.details.get('error')}"


@requires_pg
def test_r4_missing_index_fails_on_seq_scan():
    from cases.r4_schema_load_optimize import seed

    body = (R4_DIR / "schema.sql").read_text(encoding="utf-8") + seed.build_sql(rows=100_000)
    body += "\n-- CREATE INDEX nothing_useful ON products (category);\nCREATE INDEX i ON products (category);\n"
    r = r4_scorer.score(_fenced("solution.sql", body), model_slug="t/m")
    assert r.passed is False
    assert r.checks["no_seq_scan_orders"] is False


@requires_pg
def test_r4_broken_script_fails_with_reason():
    r = r4_scorer.score(_r4_solution(tail="SELEC oops;\n"), model_slug="t/m")
    assert r.passed is False
    assert r.checks["script_runs"] is False
    assert "psql" in r.details["error"]


# --------------------------------------------------------------------------- #
# R5                                                                           #
# --------------------------------------------------------------------------- #
def test_r5_spec_mentions_controlling_category():
    spec = (
        Path(__file__).resolve().parent.parent
        / "cases" / "r5_etl_dashboard" / "etl_spec.md"
    ).read_text(encoding="utf-8").lower()
    assert "controlling category" in spec
    assert "multi-category" in spec or "more than one product category" in spec
    assert "mismatch must equal 0" in spec


_COUNTRY = (
    "INSERT INTO dash_revenue_by_country (month,country,revenue,customer_count)\n"
    "SELECT to_char(o.order_date,'YYYY-MM'), cu.country, 0, COUNT(DISTINCT o.customer_id)\n"
    "FROM orders o JOIN customers cu ON cu.customer_id=o.customer_id\n"
    "WHERE o.status='COMPLETED' GROUP BY 1,2;\n"
)
_LOG = (
    "INSERT INTO etl_run_log (started_at,finished_at,source_order_count,loaded_order_count,mismatch)\n"
    "SELECT now(),now(),\n"
    " (SELECT COUNT(*) FROM orders WHERE status='COMPLETED'),\n"
    " (SELECT COALESCE(SUM(order_count),0) FROM dash_revenue_by_category),\n"
    " (SELECT COUNT(*) FROM orders WHERE status='COMPLETED')\n"
    " - (SELECT COALESCE(SUM(order_count),0) FROM dash_revenue_by_category);\n"
)

ORDER_GRAIN_ETL = _fenced("etl.sql", (
    "BEGIN;\n"
    "TRUNCATE TABLE dash_revenue_by_category;\n"
    "TRUNCATE TABLE dash_revenue_by_country;\n"
    "CREATE TEMP TABLE _ctl ON COMMIT DROP AS\n"
    "SELECT oi.order_id,\n"
    "  (ARRAY_AGG(p.category ORDER BY oi.order_item_id))[1] AS category,\n"
    "  (ARRAY_AGG(oi.quantity ORDER BY oi.order_item_id))[1] AS quantity,\n"
    "  (ARRAY_AGG(oi.quantity*oi.unit_price ORDER BY oi.order_item_id))[1] AS line_rev\n"
    "FROM order_items oi JOIN products p ON p.product_id=oi.product_id GROUP BY oi.order_id;\n"
    "INSERT INTO dash_revenue_by_category (month,category,revenue,order_count,units_sold)\n"
    "SELECT to_char(o.order_date,'YYYY-MM'), COALESCE(c.category,'(no items)'),\n"
    "  COALESCE(SUM(c.line_rev),0)::numeric(14,2), COUNT(DISTINCT o.order_id),\n"
    "  COALESCE(SUM(c.quantity),0)\n"
    "FROM orders o LEFT JOIN _ctl c ON c.order_id=o.order_id WHERE o.status='COMPLETED' GROUP BY 1,2;\n"
    + _COUNTRY + _LOG + "COMMIT;"
))

LINE_GRAIN_ETL = _fenced("etl.sql", (
    "TRUNCATE TABLE dash_revenue_by_category;\n"
    "TRUNCATE TABLE dash_revenue_by_country;\n"
    "INSERT INTO dash_revenue_by_category (month,category,revenue,order_count,units_sold)\n"
    "SELECT to_char(o.order_date,'YYYY-MM'), p.category, SUM(oi.quantity*oi.unit_price),\n"
    "  COUNT(DISTINCT o.order_id), SUM(oi.quantity)\n"
    "FROM orders o JOIN order_items oi ON oi.order_id=o.order_id\n"
    "JOIN products p ON p.product_id=oi.product_id WHERE o.status='COMPLETED' GROUP BY 1,2;\n"
    + _COUNTRY + _LOG
))


@requires_pg
def test_r5_order_grain_etl_passes():
    r = r5_scorer.score(ORDER_GRAIN_ETL, model_slug="t/m")
    assert r.passed is True, f"{r.reason} / {r.details.get('error')}"
    assert r.details["source_order_count"] == r.details["loaded_order_count"] > 0


@requires_pg
def test_r5_line_grain_etl_fails_on_multi_category_orders():
    r = r5_scorer.score(LINE_GRAIN_ETL, model_slug="t/m")
    assert r.passed is False
    assert r.checks["reconciliation_zero"] is False
    assert r.details["loaded_order_count"] > r.details["source_order_count"]


@requires_pg
def test_r5_fixture_has_multi_category_and_itemless_orders():
    import psycopg2  # type: ignore

    from scorers.base import create_schema, drop_schema, new_schema_name

    schema = new_schema_name("r5")
    create_schema(pg_dsn(), schema)
    try:
        r5_scorer.build_fixture(pg_dsn(), schema)
        with psycopg2.connect(pg_dsn()) as conn, conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}";')
            cur.execute(
                "SELECT COUNT(*) FROM (SELECT oi.order_id FROM order_items oi "
                "JOIN products p USING (product_id) GROUP BY oi.order_id "
                "HAVING COUNT(DISTINCT p.category) > 1) m;"
            )
            assert cur.fetchone()[0] > 1000
            cur.execute(
                "SELECT COUNT(*) FROM orders o WHERE status='COMPLETED' AND NOT EXISTS "
                "(SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id);"
            )
            assert cur.fetchone()[0] > 0
    finally:
        drop_schema(pg_dsn(), schema)


@requires_pg
def test_r5_reconciliation_rejects_empty_rollup():
    cheat = _fenced("etl.sql", (
        "TRUNCATE TABLE dash_revenue_by_category;\nTRUNCATE TABLE dash_revenue_by_country;\n"
        "INSERT INTO dash_revenue_by_country (month,country,revenue,customer_count)\n"
        "SELECT '2026-01','US',0,0;\n"
        "INSERT INTO etl_run_log (started_at,finished_at,source_order_count,loaded_order_count,mismatch)\n"
        "SELECT now(),now(),(SELECT COUNT(*) FROM orders WHERE status='COMPLETED'),0,\n"
        "(SELECT COUNT(*) FROM orders WHERE status='COMPLETED');"
    ))
    r = r5_scorer.score(cheat, model_slug="t/m")
    assert r.passed is False
    assert r.checks["reconciliation_zero"] is False


@requires_pg
def test_r5_result_independent_of_leftover_state():
    """A leftover (e.g. empty) public.orders from earlier scoring must not matter."""
    import psycopg2  # type: ignore

    with psycopg2.connect(pg_dsn()) as conn, conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.orders') IS NOT NULL;")
        preexisting = cur.fetchone()[0]
        if not preexisting:
            cur.execute("CREATE TABLE public.orders (order_id int);")
    try:
        assert r5_scorer.score(ORDER_GRAIN_ETL, model_slug="t/m").passed is True
    finally:
        if not preexisting:
            with psycopg2.connect(pg_dsn()) as conn, conn.cursor() as cur:
                cur.execute("DROP TABLE public.orders;")


@requires_pg
def test_no_scratch_schema_survives_scoring():
    r4_scorer.score(_r4_solution(), model_slug="t/m")
    r5_scorer.score(ORDER_GRAIN_ETL, model_slug="t/m")
    assert _scratch_schemas() == []
