"""scorers/base.py — shared scorer contracts and helpers.

Every scorer exposes:

    score(output_text: str, *, workdir: Path | None = None, **kw) -> ScoreResult

and is callable as a module:  python -m scorers.<name> --output-file <path> [--json]

A scorer NEVER raises for malformed model output — it returns ScoreResult(passed=False,
reason=...). This keeps the overall run alive (requirement: "never crash the whole run").
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any


@dataclass
class ScoreResult:
    case_id: str
    model_slug: str = ""
    passed: bool = False
    score: float = 0.0                      # 0.0..1.0
    reason: str = ""
    checks: dict[str, bool] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# parsing the model's `### FILE: path` fenced-block output                     #
# --------------------------------------------------------------------------- #
_FILE_RE = re.compile(
    r"^#{1,4}\s*FILE:\s*(?P<path>.+?)\s*$"      # header line
    r"\s*\n```[^\n]*\n(?P<body>.*?)```",        # fenced body (non-greedy)
    re.DOTALL | re.MULTILINE,
)
_DELETE_RE = re.compile(r"^#{1,4}\s*DELETE:\s*(?P<path>.+?)\s*$", re.MULTILINE)


def parse_files(output_text: str) -> dict[str, str]:
    """Extract {relative_path: content} from a `### FILE:` fenced-block output.

    Tolerant: if no FILE blocks are found, returns {} (caller decides fail).
    """
    files: dict[str, str] = {}
    for m in _FILE_RE.finditer(output_text or ""):
        path = m.group("path").strip().strip("`").strip()
        files[path] = m.group("body")
    return files


def parse_deletes(output_text: str) -> list[str]:
    """Extract paths listed via `### DELETE: <path>` lines."""
    return [m.group("path").strip().strip("`").strip() for m in _DELETE_RE.finditer(output_text or "")]


def write_files(files: dict[str, str], dest: Path) -> list[str]:
    """Write parsed files under `dest`, guarding against path traversal.

    Returns the list of written paths (relative). Absolute paths or paths that
    escape `dest` are skipped for safety.
    """
    dest = dest.resolve()
    written: list[str] = []
    for rel, body in files.items():
        target = (dest / rel).resolve()
        if not str(target).startswith(str(dest)):
            continue  # path traversal attempt — skip
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        written.append(rel)
    return written


# --------------------------------------------------------------------------- #
# Postgres connection helper (shared by R3/R4/R5)                              #
# --------------------------------------------------------------------------- #
def pg_dsn() -> str:
    """Build a psycopg2 DSN from env (falls back to the .env.example defaults)."""
    import os

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "aidb")
    user = os.environ.get("POSTGRES_USER", "ai")
    pw = os.environ.get("POSTGRES_PASSWORD", "ai")
    return f"host={host} port={port} dbname={db} user={user} password={pw}"


def pg_available() -> tuple[bool, str]:
    """Return (True, dsn) if psycopg2 can connect, else (False, reason)."""
    try:
        import psycopg2  # type: ignore
    except Exception as exc:  # pragma: no cover
        return False, f"psycopg2 unavailable: {exc}"
    dsn = pg_dsn()
    try:
        with psycopg2.connect(dsn, connect_timeout=5):
            pass
        return True, dsn
    except Exception as exc:  # pragma: no cover - depends on runtime env
        return False, f"postgres not reachable: {exc}"


# --------------------------------------------------------------------------- #
# Isolated scratch schemas + psql-semantics execution (shared by R4/R5)        #
#                                                                              #
# Model scripts are written for `psql`: statement-by-statement autocommit,     #
# meta-commands like `\set ON_ERROR_STOP on`, and VACUUM outside any txn.      #
# Running them through one psycopg2 `cur.execute()` wraps everything in a      #
# single implicit transaction and rejects meta-commands, which fails correct   #
# answers for harness reasons. So we execute them with real psql instead —     #
# the local binary if present, else the one inside the Postgres container.     #
# --------------------------------------------------------------------------- #
def new_schema_name(prefix: str) -> str:
    """A unique, collision-free, lowercase identifier for a scratch schema."""
    import uuid

    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def create_schema(dsn: str, schema: str) -> None:
    import psycopg2  # type: ignore

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA "{schema}";')


def drop_schema(dsn: str, schema: str) -> None:
    """Best-effort DROP SCHEMA ... CASCADE; never raises."""
    import psycopg2  # type: ignore

    try:
        with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;')
    except Exception:  # pragma: no cover - cleanup only
        pass


def _psql_command() -> list[str] | None:
    """Return the argv prefix that runs psql against the harness DB, or None."""
    import os
    import shutil

    user = os.environ.get("POSTGRES_USER", "ai")
    db = os.environ.get("POSTGRES_DB", "aidb")
    if shutil.which("psql"):
        return ["psql", pg_dsn()]
    container = os.environ.get("POSTGRES_CONTAINER", "aidb-postgres")
    if shutil.which("docker"):
        return ["docker", "exec", "-i", "-e", "PGOPTIONS", container, "psql", "-U", user, "-d", db]
    return None


def run_psql(sql: str, schema: str, timeout: int = 600) -> tuple[int, str]:
    """Run `sql` through psql with search_path pinned to `schema`.

    ON_ERROR_STOP=1 so any failing statement fails the script (exit code 3).
    Returns (returncode, combined output tail).
    """
    import os
    import subprocess

    cmd = _psql_command()
    if cmd is None:
        return 127, "psql not available (neither local psql nor docker)"
    env = dict(os.environ, PGOPTIONS=f"-c search_path={schema}")
    try:
        p = subprocess.run(
            cmd + ["-X", "-q", "-v", "ON_ERROR_STOP=1"],
            input=sql, capture_output=True, text=True, timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired:
        return 124, f"psql timeout after {timeout}s"
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))[-2000:]


# --------------------------------------------------------------------------- #
# CLI shim                                                                     #
# --------------------------------------------------------------------------- #
def cli(score_fn, argv: list[str] | None = None) -> int:
    """Standard `--output-file` CLI for every scorer. Prints JSON ScoreResult."""
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--output-file", required=True, help="path to the model's raw output text")
    ap.add_argument("--model", default="", help="model slug (annotation only)")
    ap.add_argument("--workdir", default=None, help="optional working dir for the scorer")
    args = ap.parse_args(argv)

    text = Path(args.output_file).read_text(encoding="utf-8")
    workdir = Path(args.workdir) if args.workdir else None
    result = score_fn(text, model_slug=args.model, workdir=workdir)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":  # pragma: no cover
    print("scorers.base is a library module", file=sys.stderr)
