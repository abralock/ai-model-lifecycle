"""scorers/r3_scorer.py — Oracle PL/SQL → PostgreSQL plpgsql scorer.

Steps:
  1. Dialect check: grep the model output for Oracle-only keywords.
  2. Parity check (SOUND): the model's SQL is applied into its OWN freshly
     created, isolated schema (`r3_model_*`), with `search_path` pointing at that
     schema only. The golden reference is built in a separate isolated schema
     (`r3_golden_*`) so the two never share objects or `search_path`.

     Crucially, the model must define EVERY expected object (tables + both
     procedures) inside its own schema. If it returns dialect-clean junk
     (e.g. `SELECT 1;`), the expected procedures will not exist -> FAIL with a
     clear "model did not define ..." reason, instead of trivially passing
     against a pre-seeded golden schema.
  3. Both temporary schemas are dropped afterwards, so no state leaks between
     runs.

Robustness: if Postgres is unreachable or psycopg2 is missing, falls back to the
dialect-token check only and marks parity as "unverified" (never crashes).

Usage:
    python -m scorers.r3_scorer --output-file <model-output.txt>
"""

from __future__ import annotations

import io
import re
import uuid
from pathlib import Path

import pandas as pd

from .base import ScoreResult, cli, parse_files, pg_available

CASE_ID = "r3_oracle_to_postgres"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID

# Oracle-only tokens. NOTE: %ROWTYPE/%TYPE are deliberately NOT listed — they are
# valid plpgsql and appear in correct translations.
ORACLE_TOKENS = ["DUAL", "NVL(", "ROWNUM", "(+)", "VARCHAR2", "sysdate"]

# Objects the model is required to create itself. If any is missing from the
# model's isolated schema, parity cannot be meaningful -> explicit FAIL.
EXPECTED_TABLES = (
    "customers",
    "orders",
    "customer_tiers",
    "products",
    "order_items",
    "monthly_report",
)
EXPECTED_PROCEDURES = ("sp_customer_tier", "sp_monthly_report")

# Result-set comparison contract for sp_customer_tier().
TIER_SELECT = (
    "SELECT customer_id, customer_name, total_spend, order_count, tier "
    "FROM customer_tiers ORDER BY customer_id;"
)


def _strip_sql_comments(sql: str) -> str:
    """Remove -- line comments and /* */ block comments so dialect scanning
    ignores explanatory notes that legitimately mention Oracle keywords."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _read_output_text_for_dialect(text: str) -> str:
    """Prefer only the code inside FILE blocks for the dialect scan (avoid false
    positives from prose). Falls back to the whole text. Comments are stripped."""
    files = parse_files(text)
    body = "\n".join(files.values()) if files else text
    return _strip_sql_comments(body)


def _dialect_hits(sql: str) -> list[str]:
    hits: list[str] = []
    for tok in ORACLE_TOKENS:
        # word-ish boundary for identifiers; raw substring for operators
        if tok.endswith("(") or tok == "(+)":
            if tok in sql:
                hits.append(tok)
        else:
            if re.search(rf"\b{re.escape(tok.strip('%'))}\b", sql, re.IGNORECASE):
                hits.append(tok)
    return sorted(set(hits))


# --------------------------------------------------------------------------- #
# isolated-schema helpers                                                      #
# --------------------------------------------------------------------------- #
def _new_schema_name(prefix: str) -> str:
    """A unique, collision-free, lowercase identifier for a scratch schema."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _drop_schema(conn, schema: str) -> None:
    """Best-effort DROP SCHEMA ... CASCADE, tolerated if already gone."""
    with conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;')


def _missing_objects(cur, schema: str) -> list[str]:
    """Return expected objects (tables + procedures) absent from `schema`."""
    missing: list[str] = []

    cur.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = %s;", (schema,)
    )
    tables = {row[0] for row in cur.fetchall()}
    for t in EXPECTED_TABLES:
        if t not in tables:
            missing.append(f"table:{t}")

    cur.execute(
        "SELECT p.proname FROM pg_proc p "
        "JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = %s;",
        (schema,),
    )
    procs = {row[0] for row in cur.fetchall()}
    for p in EXPECTED_PROCEDURES:
        if p not in procs:
            missing.append(f"procedure:{p}")

    return missing


def _golden_frame(dsn: str) -> pd.DataFrame:
    """Build the golden reference in its OWN isolated schema and return the
    sp_customer_tier() result frame. The schema is dropped afterwards."""
    import psycopg2  # type: ignore

    golden_sql = (CASE_DIR / "golden_postgres.sql").read_text(encoding="utf-8")
    seed_sql = (CASE_DIR / "seed.sql").read_text(encoding="utf-8")
    schema = _new_schema_name("r3_golden")

    conn = psycopg2.connect(dsn)
    # Autocommit, as psql or an application would CALL it: Postgres only
    # allows COMMIT inside a procedure when CALL is not wrapped in an explicit
    # transaction, and the Oracle source procedures COMMIT.
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{schema}";')
            # search_path EXCLUSIVELY our scratch schema: no golden object ever
            # lands in (or is read from) public/other schemas.
            cur.execute(f'SET search_path TO "{schema}";')
            cur.execute(golden_sql)
            cur.execute(seed_sql)
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("CALL sp_customer_tier();")
            cur.execute(TIER_SELECT)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        try:
            conn.rollback()
            _drop_schema(conn, schema)
            conn.commit()
        finally:
            conn.close()


def _model_frame(dsn: str, model_sql: str) -> pd.DataFrame:
    """Apply ONLY the model's SQL into a freshly created, isolated schema.

    Raises ``_MissingObjects`` if the model failed to define any expected
    table/procedure. The schema is dropped afterwards in all cases.
    """
    import psycopg2  # type: ignore

    seed_sql = (CASE_DIR / "seed.sql").read_text(encoding="utf-8")
    schema = _new_schema_name("r3_model")

    conn = psycopg2.connect(dsn)
    # Autocommit, as psql or an application would CALL it: Postgres only
    # allows COMMIT inside a procedure when CALL is not wrapped in an explicit
    # transaction, and the Oracle source procedures COMMIT.
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{schema}";')
            cur.execute(f'SET search_path TO "{schema}";')
            # model DDL + procedures (defining their own tables in this schema)
            cur.execute(model_sql)
        conn.commit()

        with conn.cursor() as cur:
            missing = _missing_objects(cur, schema)
        if missing:
            raise _MissingObjects(missing)

        with conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}";')
            cur.execute(seed_sql)
            cur.execute("CALL sp_customer_tier();")
            cur.execute(TIER_SELECT)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        try:
            conn.rollback()
            _drop_schema(conn, schema)
            conn.commit()
        finally:
            conn.close()


class _MissingObjects(Exception):
    """Raised when the model's schema lacks expected tables/procedures."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(", ".join(missing))


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce numeric columns to float and sort for a stable set comparison."""
    df = df.copy()
    for c in df.columns:
        if c not in ("customer_name", "tier"):
            try:
                df[c] = pd.to_numeric(df[c]).astype(float)
            except (ValueError, TypeError):
                pass
    return df.sort_values(by=list(df.columns)).reset_index(drop=True)


def score(output_text: str, *, model_slug: str = "", workdir: Path | None = None) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)

    files = parse_files(output_text)
    sql_text = "\n".join(files.values())
    if not sql_text.strip():
        sql_text = output_text  # model may have emitted a bare SQL block

    hits = _dialect_hits(_read_output_text_for_dialect(output_text))
    res.checks["dialect_clean"] = len(hits) == 0
    res.details["dialect_hits"] = hits

    ok, dsn = pg_available()
    if not ok:
        res.details["postgres"] = dsn
        # Without a DB we can only verify the dialect. Parity = unverified -> fail
        # conservatively (cannot prove correctness) but do not crash.
        res.checks["parity"] = False
        res.passed = False
        res.reason = f"postgres unavailable ({dsn}); dialect_clean={res.checks['dialect_clean']}"
        return res

    missing: list[str] = []
    try:
        golden = _golden_frame(dsn)
        produced = _model_frame(dsn, sql_text)

        g = _normalize(golden)
        p = _normalize(produced)
        equal = g.shape == p.shape and g.equals(p)
        # Also allow equality ignoring exact column order.
        if not equal:
            try:
                equal = g.reset_index(drop=True).equals(
                    p[sorted(p.columns)].reset_index(drop=True)
                )
            except Exception:
                equal = False
        res.checks["parity"] = bool(equal)
        if not equal:
            res.details["golden_shape"] = list(g.shape)
            res.details["produced_shape"] = list(p.shape)
            # small diff sample for the report
            res.details["golden_rows"] = g.head(10).to_dict("records")
            res.details["produced_rows"] = p.head(10).to_dict("records")
    except _MissingObjects as exc:
        # Sound failure: the model never defined the expected schema/procedures.
        res.checks["parity"] = False
        res.checks["objects_defined"] = False
        missing = exc.missing
        res.details["missing_objects"] = missing
        first = missing[0].split(":", 1)[1] if ":" in missing[0] else missing[0]
        res.details["error"] = f"model did not define {first}"
    except Exception as exc:  # noqa: BLE001 - malformed SQL must not crash the run
        res.checks["parity"] = False
        res.details["error"] = f"{type(exc).__name__}: {exc}"

    res.passed = res.checks.get("dialect_clean", False) and res.checks.get("parity", False)
    res.score = 1.0 if res.passed else 0.0
    if not res.passed:
        parts = []
        if not res.checks.get("dialect_clean"):
            parts.append("oracle tokens: " + ",".join(hits))
        if missing:
            first = missing[0].split(":", 1)[1] if ":" in missing[0] else missing[0]
            parts.append(f"model did not define {first}")
        elif not res.checks.get("parity"):
            parts.append("result set != golden")
        res.reason = "; ".join(parts) or "failed"
    else:
        res.reason = "plpgsql translation matches golden result set; no oracle dialect tokens"
    return res


if __name__ == "__main__":
    raise SystemExit(cli(score))
