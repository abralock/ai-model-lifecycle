"""scorers/r4_scorer.py — Schema + Bulk Load + Optimize scorer.

Steps:
  1. Run the MODEL's script (create tables, load data, add index) with real psql
     semantics — autocommit per statement, meta-commands honored, VACUUM legal —
     inside a fresh, isolated scratch schema (`r4_<uuid>`). See
     `scorers.base.run_psql`. This is how the prompt's deliverable would be run
     by an engineer, so harness mechanics can no longer fail a correct answer.
  2. Verify the expected row count was loaded.
  3. ANALYZE the tables (as autovacuum would in any real database), then run
     `EXPLAIN (ANALYZE, BUFFERS)` on the frozen target_query.sql and assert an
     index/bitmap index scan on `orders` and NO seq scan on `orders`.
  4. Assert query latency < threshold_ms (default 1000).
  5. Drop the scratch schema, so nothing leaks into later scoring (e.g. R5).

Robustness: no Postgres / malformed SQL -> structured fail, never a crash.

Usage:
    python -m scorers.r4_scorer --output-file <model-output.txt> [--rows 100000]
"""

from __future__ import annotations

import re
import time
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

CASE_ID = "r4_schema_load_optimize"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID
DEFAULT_ROWS = 100_000
DEFAULT_THRESHOLD_MS = 1000.0
TABLES = ("customers", "products", "orders", "order_items")


def score(
    output_text: str,
    *,
    model_slug: str = "",
    workdir: Path | None = None,
    rows: int = DEFAULT_ROWS,
    threshold_ms: float = DEFAULT_THRESHOLD_MS,
) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)

    files = parse_files(output_text)
    sql_text = "\n".join(files.values()) if files else output_text
    if not sql_text.strip():
        res.reason = "no SQL found in model output"
        return res

    res.checks["adds_index"] = bool(re.search(r"\bcreate\s+(unique\s+)?index\b", sql_text, re.I))

    ok, dsn = pg_available()
    if not ok:
        res.details["postgres"] = dsn
        res.passed = False
        res.reason = f"postgres unavailable ({dsn})"
        return res

    schema = new_schema_name("r4")
    try:
        import psycopg2  # type: ignore
        target_q = (CASE_DIR / "target_query.sql").read_text(encoding="utf-8")

        create_schema(dsn, schema)
        rc, out = run_psql(sql_text, schema)
        res.checks["script_runs"] = rc == 0
        if rc != 0:
            res.details["error"] = f"model script failed under psql (rc={rc}): {out[-600:]}"
            raise _ScriptFailed()

        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{schema}";')

                cur.execute("SELECT COUNT(*) FROM orders;")
                loaded = cur.fetchone()[0]
                res.details["orders_loaded"] = loaded
                res.details["rows_expected"] = rows
                res.checks["loaded"] = loaded >= rows

                for t in TABLES:
                    cur.execute(f"ANALYZE {t};")

                cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + target_q)
                plan = "\n".join(r[0] for r in cur.fetchall())
                res.details["plan"] = plan

                res.checks["index_scan"] = bool(
                    re.search(r"(Index Scan|Index Only Scan|Bitmap Index Scan).*on \S*orders", plan)
                )
                res.checks["no_seq_scan_orders"] = not bool(
                    re.search(r"Seq Scan on orders\b", plan)
                )

                m = re.search(r"Execution Time:\s*([\d.]+)\s*ms", plan)
                if m:
                    exec_ms = float(m.group(1))
                else:  # pragma: no cover - EXPLAIN ANALYZE always reports this
                    t0 = time.time()
                    cur.execute(target_q)
                    cur.fetchall()
                    exec_ms = (time.time() - t0) * 1000
                res.details["exec_ms"] = exec_ms
                res.checks["latency_ok"] = exec_ms < threshold_ms

                # informational: a dataset with no matching rows makes the plan
                # degenerate (and the latency check trivial)
                cur.execute(f"SELECT COUNT(*) FROM ({target_q.rstrip().rstrip(';')}) q;")
                res.details["target_query_rows"] = cur.fetchone()[0]
    except _ScriptFailed:
        pass
    except Exception as exc:  # noqa: BLE001
        res.details["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        drop_schema(dsn, schema)

    required = ["adds_index", "script_runs", "loaded", "index_scan", "no_seq_scan_orders", "latency_ok"]
    res.passed = all(res.checks.get(k, False) for k in required)
    res.score = 1.0 if res.passed else 0.0
    if not res.passed:
        res.reason = "failed checks: " + ", ".join(k for k in required if not res.checks.get(k))
    else:
        res.reason = (
            f"index scan on orders, no seq scan, {res.details.get('exec_ms', 0):.1f}ms "
            f"< {threshold_ms}ms"
        )
    return res


class _ScriptFailed(Exception):
    """The model's script exited non-zero under psql."""


if __name__ == "__main__":
    raise SystemExit(cli(score))
