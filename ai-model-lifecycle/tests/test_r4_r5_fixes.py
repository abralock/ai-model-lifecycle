"""tests/test_r4_r5_fixes.py — regression tests for the R4/R5 audit fixes.

R4: the scorer must strip maintenance statements (`VACUUM`) that Postgres forbids
    inside a transaction block, so a correct-but-VACUUM-containing solution is
    still evaluated on schema + load + index.

R5: the reconciliation gate must be *passable* but still discriminating — a
    correct order-grain ETL reconciles to mismatch 0, while the models'
    line-grain ETL (which double-counts multi-category orders) must fail.

Pure-logic tests run offline; DB-backed tests auto-skip without Postgres.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from common import load_env
from scorers import r4_scorer, r5_scorer
from scorers.base import pg_available, parse_files

load_env()
RUNS = Path(__file__).resolve().parent.parent / "runs" / "opus-4.8-vs-5.5"
_HAS_PG = pg_available()[0]
requires_pg = pytest.mark.skipif(not _HAS_PG, reason="postgres not reachable")


# --------------------------------------------------------------------------- #
# R4 — maintenance-statement stripping (pure logic, offline)                    #
# --------------------------------------------------------------------------- #
def test_strip_maintenance_removes_vacuum_and_adds_analyze():
    sql = "CREATE INDEX i ON t (a);\nVACUUM ANALYZE orders;\nANALYZE products;"
    out, stripped = r4_scorer.strip_maintenance(sql)
    assert stripped is True
    assert "VACUUM" not in out.upper()
    assert "ANALYZE orders;" in out
    assert "ANALYZE products;" in out  # a bare ANALYZE stays untouched
    assert "CREATE INDEX i ON t (a);" in out


def test_strip_maintenance_is_noop_without_vacuum():
    sql = "CREATE INDEX i ON t (a);\nANALYZE orders;"
    out, stripped = r4_scorer.strip_maintenance(sql)
    assert stripped is False
    assert out == sql


def test_strip_maintenance_handles_plain_vacuum():
    out, stripped = r4_scorer.strip_maintenance("VACUUM FULL orders;")
    assert stripped is True
    assert "VACUUM" not in out.upper()


# --------------------------------------------------------------------------- #
# R4 — VACUUM-containing solution passes on the real model output (DB)          #
# --------------------------------------------------------------------------- #
@requires_pg
def test_r4_vacuum_solution_still_passes():
    """Opus 5.5's R4 output embeds `VACUUM ANALYZE`; before the fix it scored
    FAIL purely because VACUUM cannot run in the scorer's transaction. It must
    now PASS on the merits of its index."""
    import json

    txt = (RUNS / "anthropic__claude-opus-5.5.r4_schema_load_optimize.json").read_text()
    out = json.loads(txt)["output_text"]
    assert "VACUUM" in out.upper(), "fixture precondition"
    r = r4_scorer.score(out, model_slug="t/m")
    assert r.passed is True, r.reason
    assert r.checks["maintenance_statements_stripped"] is True
    assert r.checks["index_scan"] and r.checks["no_seq_scan_orders"]


# --------------------------------------------------------------------------- #
# R5 — spec reconciliation is achievable only at order grain (pure logic)       #
# --------------------------------------------------------------------------- #
def test_r5_spec_mentions_controlling_category():
    spec = (
        Path(__file__).resolve().parent.parent
        / "cases" / "r5_etl_dashboard" / "etl_spec.md"
    ).read_text(encoding="utf-8").lower()
    assert "controlling category" in spec
    assert "multi-category" in spec or "more than one product category" in spec
    # the hard gate wording is preserved
    assert "mismatch must equal 0" in spec


# --------------------------------------------------------------------------- #
# R5 — the fixed gate is passable, and still rejects the line-grain rollup (DB) #
# --------------------------------------------------------------------------- #
@requires_pg
def test_r5_correct_order_grain_etl_passes_on_both_datasets():
    from audits.rescore_r4_r5 import apply_r4_source

    correct = (
        "### FILE: etl.sql\n```sql\n"
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
        "INSERT INTO dash_revenue_by_country (month,country,revenue,customer_count)\n"
        "SELECT to_char(o.order_date,'YYYY-MM'), cu.country, 0, COUNT(DISTINCT o.customer_id)\n"
        "FROM orders o JOIN customers cu ON cu.customer_id=o.customer_id WHERE o.status='COMPLETED' GROUP BY 1,2;\n"
        "INSERT INTO etl_run_log (started_at,finished_at,source_order_count,loaded_order_count,mismatch)\n"
        "SELECT now(),now(),\n"
        " (SELECT COUNT(*) FROM orders WHERE status='COMPLETED'),\n"
        " (SELECT COALESCE(SUM(order_count),0) FROM dash_revenue_by_category),\n"
        " (SELECT COUNT(*) FROM orders WHERE status='COMPLETED')\n"
        " - (SELECT COALESCE(SUM(order_count),0) FROM dash_revenue_by_category);\n"
        "COMMIT;\n```\n"
    )
    for model in ("anthropic__claude-opus-4.8", "anthropic__claude-opus-5.5"):
        apply_r4_source(model)
        r = r5_scorer.score(correct, model_slug=model)
        assert r.passed is True, f"{model}: {r.reason} / {r.checks}"
        assert r.details["source_order_count"] == r.details["loaded_order_count"] > 0


@requires_pg
def test_r5_reconciliation_rejects_empty_rollup():
    """A model that leaves the rollup empty must NOT pass: loaded == 0 only
    reconciles when the source is empty, which is not the intent."""
    from audits.rescore_r4_r5 import apply_r4_source

    apply_r4_source("anthropic__claude-opus-4.8")
    cheat = (
        "### FILE: etl.sql\n```sql\nBEGIN;\n"
        "TRUNCATE TABLE dash_revenue_by_category;\n"
        "TRUNCATE TABLE dash_revenue_by_country;\n"
        "INSERT INTO dash_revenue_by_country (month,country,revenue,customer_count)\n"
        "SELECT '2026-01','US',0,0;\n"
        "INSERT INTO etl_run_log (started_at,finished_at,source_order_count,loaded_order_count,mismatch)\n"
        "SELECT now(),now(),(SELECT COUNT(*) FROM orders WHERE status='COMPLETED'),0,\n"
        "(SELECT COUNT(*) FROM orders WHERE status='COMPLETED');\nCOMMIT;\n```\n"
    )
    r = r5_scorer.score(cheat, model_slug="t/m")
    assert r.passed is False
    assert r.checks["reconciliation_zero"] is False
