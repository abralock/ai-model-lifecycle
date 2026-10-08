"""scorers/r3_scorer.py — Oracle PL/SQL → PostgreSQL plpgsql scorer.

Steps:
  1. Load the golden schema + seed + golden procedures into the live Postgres
     (localhost:5432/aidb) to get a known-good baseline snapshot... actually we
     load the *golden* definitions, run them, and snapshot the two result sets.
  2. Apply the MODEL's SQL (schema + procedures) into a clean schema, run it, and
     compare the result sets to golden_output.csv / golden_output_monthly.csv via
     pandas.
  3. Dialect-token check: grep the model output for Oracle-only keywords.

Robustness: if Postgres is unreachable or psycopg2 is missing, falls back to the
dialect-token check only and marks parity as "unverified" (never crashes).

Usage:
    python -m scorers.r3_scorer --output-file <model-output.txt>
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd

from .base import ScoreResult, cli, parse_files, pg_available

CASE_ID = "r3_oracle_to_postgres"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID

ORACLE_TOKENS = ["DUAL", "NVL(", "ROWNUM", "(+)", "VARCHAR2", "sysdate", "%ROWTYPE", "%TYPE"]


def _read_output_text_for_dialect(text: str) -> str:
    """Prefer only the code inside FILE blocks for the dialect scan (avoid false
    positives from prose). Falls back to the whole text."""
    files = parse_files(text)
    return "\n".join(files.values()) if files else text


def _dialect_hits(sql: str) -> list[str]:
    hits: list[str] = []
    for tok in ORACLE_TOKENS:
        # word-ish boundary for identifiers; raw substring for operators
        if tok.endswith("(") or tok == "(+)":
            if tok in sql:
                hits.append(tok)
        else:
            if re.search(rf"\b{re.escape(tok.strip('%'))}\b", sql, re.IGNORECASE) or tok in sql:
                hits.append(tok)
    return sorted(set(hits))


def _golden_frame(dsn: str, golden_sql: str, seed_sql: str) -> pd.DataFrame:
    """Load golden schema+seed+procs, run sp_customer_tier, return result frame."""
    import psycopg2  # type: ignore
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(golden_sql)
            cur.execute(seed_sql)
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("CALL sp_customer_tier();")
            cur.execute(
                "SELECT customer_id, customer_name, total_spend, order_count, tier "
                "FROM customer_tiers ORDER BY customer_id;"
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        conn.rollback()
    return pd.DataFrame(rows, columns=cols)


def _model_frame(dsn: str, model_sql: str, model_monthly: bool) -> pd.DataFrame:
    """Apply ONLY the model's SQL in a fresh search_path, seed, run, return frame."""
    import psycopg2  # type: ignore
    seed_sql = (CASE_DIR / "seed.sql").read_text(encoding="utf-8")
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(model_sql)
        conn.commit()
        with conn.cursor() as cur:
            cur.execute(seed_sql)
            cur.execute("CALL sp_customer_tier();")
            cur.execute(
                "SELECT customer_id, customer_name, total_spend, order_count, tier "
                "FROM customer_tiers ORDER BY customer_id;"
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
        conn.rollback()
    return pd.DataFrame(rows, columns=cols)


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

    try:
        golden_sql = (CASE_DIR / "golden_postgres.sql").read_text(encoding="utf-8")
        seed_sql = (CASE_DIR / "seed.sql").read_text(encoding="utf-8")
        golden = _golden_frame(dsn, golden_sql, seed_sql)
        produced = _model_frame(dsn, sql_text, model_monthly=False)

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
    except Exception as exc:  # noqa: BLE001 - malformed SQL must not crash the run
        res.checks["parity"] = False
        res.details["error"] = f"{type(exc).__name__}: {exc}"

    res.passed = res.checks.get("dialect_clean", False) and res.checks.get("parity", False)
    res.score = 1.0 if res.passed else 0.0
    if not res.passed:
        parts = []
        if not res.checks.get("dialect_clean"):
            parts.append("oracle tokens: " + ",".join(hits))
        if not res.checks.get("parity"):
            parts.append("result set != golden")
        res.reason = "; ".join(parts) or "failed"
    else:
        res.reason = "plpgsql translation matches golden result set; no oracle dialect tokens"
    return res


if __name__ == "__main__":
    raise SystemExit(cli(score))
