"""tests/test_r3_scorer.py — regression tests for the R3 parity scorer (Bug 1).

These prove the parity check is *sound*: the model's SQL must be executed in an
isolated schema where it defines every expected table + procedure itself.

DB-backed tests auto-skip when Postgres is unreachable.

    pytest -q tests/test_r3_scorer.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from common import load_env
from scorers.base import pg_available

load_env()

CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / "r3_oracle_to_postgres"

_HAS_PG = pg_available()[0]
requires_pg = pytest.mark.skipif(not _HAS_PG, reason="postgres not reachable")


def _fenced(path: str, body: str) -> str:
    return f"### FILE: {path}\n```sql\n{body}\n```\n"


def test_junk_never_passes_offline():
    """`SELECT 1;` must never score PASS, even without a DB (conservative fail)."""
    from scorers.r3_scorer import score

    r = score(_fenced("postgres/procedures.sql", "SELECT 1;"), model_slug="t/m")
    assert r.passed is False
    assert r.score == 0.0
    assert r.reason


@requires_pg
def test_junk_select_1_fails_with_did_not_define():
    """Regression: dialect-clean junk must FAIL with a 'did not define' reason.

    Before the fix, `SELECT 1;` scored a false 100% PASS because the scorer
    loaded+committed the golden schema/procedures first.
    """
    from scorers.r3_scorer import score

    r = score(_fenced("postgres/procedures.sql", "SELECT 1;"), model_slug="t/m")
    assert r.passed is False, "SELECT 1; must not pass parity"
    assert r.checks.get("dialect_clean") is True  # junk is dialect-clean...
    assert r.checks.get("parity") is False  # ...but must still fail parity
    assert "did not define" in r.reason
    assert r.details.get("missing_objects")  # e.g. table:customers, procedure:sp_customer_tier


@requires_pg
def test_correct_translation_passes_with_parity():
    """A correct plpgsql translation (the golden) must PASS with parity."""
    from scorers.r3_scorer import score

    golden = (CASE_DIR / "golden_postgres.sql").read_text(encoding="utf-8")
    r = score(_fenced("postgres/schema.sql", golden), model_slug="t/m")
    assert r.passed is True, r.reason
    assert r.checks["dialect_clean"] and r.checks["parity"]


@requires_pg
def test_commit_inside_procedure_passes():
    """Regression (Opus 5.5, run 20261009T022349Z): the Oracle source COMMITs,
    and Postgres allows COMMIT in a procedure when CALL runs outside an explicit
    transaction (psql / app autocommit). The scorer must CALL that way rather
    than fail a faithful translation with 'invalid transaction termination'."""
    from scorers.r3_scorer import score

    golden = (CASE_DIR / "golden_postgres.sql").read_text(encoding="utf-8")
    first_end = golden.index("END;", golden.index("PROCEDURE sp_customer_tier"))
    with_commit = golden[:first_end] + "    COMMIT;\n" + golden[first_end:]
    r = score(_fenced("postgres/schema.sql", with_commit), model_slug="t/m")
    assert r.passed is True, f"{r.reason} / {r.details.get('error')}"


@requires_pg
def test_wrong_results_fail_parity_without_missing_objects():
    """A translation that defines all objects but returns wrong data must FAIL
    on result-set mismatch (not on missing objects)."""
    from scorers.r3_scorer import score

    golden = (CASE_DIR / "golden_postgres.sql").read_text(encoding="utf-8")
    # Break the tier threshold so tiers differ from golden, objects still exist.
    broken = golden.replace("IF rec.total_spend >= 1000 THEN", "IF rec.total_spend >= 999999 THEN")
    assert broken != golden
    r = score(_fenced("postgres/schema.sql", broken), model_slug="t/m")
    assert r.passed is False
    assert not r.details.get("missing_objects")
    assert "result set != golden" in r.reason


@requires_pg
def test_no_schema_leak_after_scoring():
    """Scratch schemas are dropped; nothing leaks into the database."""
    import psycopg2  # type: ignore

    from scorers.base import pg_dsn
    from scorers.r3_scorer import score

    # Run once to force scratch-schema creation/drop.
    score(_fenced("postgres/procedures.sql", "SELECT 1;"), model_slug="t/m")

    conn = psycopg2.connect(pg_dsn())
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT nspname FROM pg_namespace WHERE nspname LIKE 'r3_%';")
            leftovers = cur.fetchall()
        assert leftovers == [], f"scratch schemas leaked: {leftovers}"
    finally:
        conn.rollback()
        conn.close()
