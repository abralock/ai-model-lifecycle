"""scorers/r4_scorer.py — Schema + Bulk Load + Optimize scorer.

Steps:
  1. Apply the MODEL's SQL (which must create tables, load data, add index).
  2. Verify the expected row count was loaded.
  3. Run `EXPLAIN (ANALYZE, BUFFERS)` on the frozen target_query.sql and assert
     there is an index/bitmap index scan on `orders` and NO seq scan on `orders`.
  4. Assert query latency < threshold_ms (default 1000).

The scorer does not require the model to have run Docker — it re-applies the
model's DDL/DML into the running Postgres.

Robustness: no Postgres / malformed SQL -> structured fail, never a crash.

Usage:
    python -m scorers.r4_scorer --output-file <model-output.txt> [--rows 100000]
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from .base import ScoreResult, cli, parse_files, pg_available

CASE_ID = "r4_schema_load_optimize"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID
DEFAULT_ROWS = 100_000
DEFAULT_THRESHOLD_MS = 1000.0


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

    try:
        import psycopg2  # type: ignore
        target_q = (CASE_DIR / "target_query.sql").read_text(encoding="utf-8")

        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                # reset schema so the model's DDL runs against a clean slate
                for t in ("order_items", "orders", "products", "customers"):
                    cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
                conn.commit()
                cur.execute(sql_text)
                conn.commit()

                # row count
                cur.execute("SELECT COUNT(*) FROM orders;")
                loaded = cur.fetchone()[0]
                res.details["orders_loaded"] = loaded
                res.details["rows_expected"] = rows
                res.checks["loaded"] = loaded >= rows

                # EXPLAIN (ANALYZE, BUFFERS) the frozen target query
                cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) " + target_q)
                plan_lines = [r[0] for r in cur.fetchall()]
                plan = "\n".join(plan_lines)
                res.details["plan"] = plan

                res.checks["index_scan"] = bool(
                    re.search(r"(Index Scan|Bitmap Index Scan).*on orders", plan)
                    or re.search(r"on orders", plan) and "Index" in plan
                )
                res.checks["no_seq_scan_orders"] = not bool(
                    re.search(r"Seq Scan on orders\b", plan)
                )

                # latency: parse the "Execution Time: X ms" line, else time a re-run
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
            conn.rollback()
    except Exception as exc:  # noqa: BLE001
        res.checks.setdefault("loaded", False)
        res.checks.setdefault("index_scan", False)
        res.checks.setdefault("no_seq_scan_orders", False)
        res.checks.setdefault("latency_ok", False)
        res.details["error"] = f"{type(exc).__name__}: {exc}"

    required = ["adds_index", "loaded", "index_scan", "no_seq_scan_orders", "latency_ok"]
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


if __name__ == "__main__":
    raise SystemExit(cli(score))
