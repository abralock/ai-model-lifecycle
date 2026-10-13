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
    r"^#{1,4}\s*FILE:\s*(?P<path>.+?)\s*$",        # header line
    re.MULTILINE,
)
_DELETE_RE = re.compile(r"^#{1,4}\s*DELETE:\s*(?P<path>.+?)\s*$", re.MULTILINE)


def parse_files(output_text: str) -> dict[str, str]:
    """Extract {relative_path: content} from a `### FILE:` fenced-block output.

    Line-oriented (not one big regex) so it is robust to the following real-world
    model quirks, any of which used to yield an empty body and score a correct
    answer as "no SQL found":
      * a stray fence ````` before the ``### FILE:`` header,
      * a language tag on the fence (`````sql` / ````python`)
      * ``` / `` or `---`-style blocks,
      * the header placed INSIDE the fence, directly above the content.

    Algorithm: scan lines; on a ``### FILE: <path>`` header, walk forward until the
    next line that is (or starts with) a fence, then capture until the matching
    closing fence. Tolerant: if no FILE blocks are found, returns {}.
    """
    text = output_text or ""
    files: dict[str, str] = {}
    lines = text.splitlines()
    n = len(lines)

    def _fence(line: str) -> str | None:
        """Return the fence marker ('```' or '~~~') if `line` is a fence, else None.

        A fence is any line whose stripped form starts with ``` or ~~~. A *bare*
        fence (marker with no trailing language tag) is distinguishable from a
        tagged fence (`````sql`) so stray wrapper fences around the header can be
        skipped without eating the real content fence.
        """
        s = line.strip()
        for marker in ("```", "~~~"):
            if s.startswith(marker):
                return marker
        return None

    i = 0
    inside = False  # inside a fence opened before (outside of) any file body
    while i < n:
        m = _FILE_RE.match(lines[i])
        if not m:
            if _fence(lines[i]):
                inside = not inside
            i += 1
            continue
        path = m.group("path").strip().strip("`").strip()
        # Header INSIDE an open fence, directly above the content
        # (```sql / ### FILE: x / ...content... / ```): the body is the lines
        # up to the closing fence. Only when there IS content before that fence;
        # otherwise it is the stray-wrapper case handled below.
        if inside:
            j = i + 1
            while j < n and not _fence(lines[j]):
                j += 1
            body = lines[i + 1:j]
            if any(line.strip() for line in body):
                files[path] = "\n".join(body) + "\n"
                inside = False
                i = j + 1
                continue
        inside = False
        # Find the opening content fence. A tagged fence (`````sql) is always the
        # opener. A bare `` ``` `` is a stray wrapper fence (models open/close an
        # empty fence around the header) and is skipped *only* when the next
        # non-blank line is another fence (the real opener or closer).
        open_idx = None
        j = i + 1
        while j < n:
            f = _fence(lines[j])
            if f is None:
                j += 1
                continue
            # tagged fence -> definite opener
            if len(lines[j].strip()) > len(f):
                open_idx = j
                break
            # bare fence: skip only if the next non-blank line is also a fence
            k = j + 1
            while k < n and not lines[k].strip():
                k += 1
            if k < n and _fence(lines[k]) is not None:
                j = k
                continue
            # next non-blank line is real content -> this bare fence is the opener
            open_idx = j
            break
        if open_idx is None:
            i += 1
            continue
        # Capture body from the line after the opener until the closing fence.
        body: list[str] = []
        j = open_idx + 1
        while j < n and not _fence(lines[j]):
            body.append(lines[j])
            j += 1
        files[path] = "\n".join(body) + ("\n" if body else "")
        i = j + 1
    return files


def parse_deletes(output_text: str) -> list[str]:
    """Extract paths listed via `### DELETE: <path>` lines."""
    return [m.group("path").strip().strip("`").strip() for m in _DELETE_RE.finditer(output_text or "")]


# --------------------------------------------------------------------------- #
# `### EDIT: path` + SEARCH/REPLACE blocks (for cases too big to re-emit)       #
# --------------------------------------------------------------------------- #
_EDIT_RE = re.compile(r"^#{1,4}\s*EDIT:\s*(?P<path>.+?)\s*$", re.MULTILINE)
_ANY_HEADER_RE = re.compile(r"^#{1,4}\s*(FILE|EDIT|DELETE):", re.MULTILINE)
_SR_RE = re.compile(
    r"^<{5,9} SEARCH[^\n]*\n(?P<search>.*?)^={5,9}[ \t]*\n(?P<replace>.*?)^>{5,9} REPLACE[^\n]*$",
    re.MULTILINE | re.DOTALL,
)


@dataclass
class Edit:
    path: str
    search: str
    replace: str


def parse_edits(output_text: str) -> list[Edit]:
    """Extract SEARCH/REPLACE edits from `### EDIT: <path>` sections, in order.

    A section runs from its header to the next FILE/EDIT/DELETE header (or the
    end); fences inside it are ignored. Each block is

        <<<<<<< SEARCH
        exact existing lines
        =======
        replacement lines
        >>>>>>> REPLACE
    """
    text = output_text or ""
    edits: list[Edit] = []
    for m in _EDIT_RE.finditer(text):
        nxt = _ANY_HEADER_RE.search(text, m.end())
        section = text[m.end(): nxt.start() if nxt else len(text)]
        path = m.group("path").strip().strip("`").strip()
        for b in _SR_RE.finditer(section):
            edits.append(Edit(path, b.group("search"), b.group("replace")))
    return edits


def _strip_trailing_ws(s: str) -> str:
    return "\n".join(line.rstrip() for line in s.replace("\r\n", "\n").split("\n"))


def _unique_dedented_match(body: str, search: str) -> tuple[int, int] | None:
    """(start, end) line indexes where SEARCH's lines equal the file's ignoring
    leading/trailing whitespace, if that happens exactly once; else None."""
    want = [ln.strip() for ln in search.splitlines()]
    if not any(want):
        return None
    have = [ln.strip() for ln in body.splitlines()]
    n = len(want)
    hits = [i for i in range(len(have) - n + 1) if have[i:i + n] == want]
    return (hits[0], hits[0] + n) if len(hits) == 1 else None


def apply_edits(edits: list[Edit], dest: Path) -> tuple[list[str], list[str]]:
    """Apply edits to files under `dest`, in order. Returns (applied, failures).

    The SEARCH text must occur in the file; the first occurrence is replaced.
    Matching is exact, except that trailing whitespace and CRLF line endings
    are ignored. Failing that, a SEARCH that is part of a line (its text
    without the final line break) matches if it occurs exactly once in the
    file, and is replaced in place: `@a.b.Param` inside `f(@a.b.Param T t)`.
    Last, whole lines match ignoring their indentation, again only where that
    happens exactly once (the REPLACE lines are written as given). An empty SEARCH on a missing file creates it. Paths that escape `dest` are
    refused like any other failure.
    """
    dest = dest.resolve()
    applied: list[str] = []
    failures: list[str] = []
    for e in edits:
        target = (dest / e.path).resolve()
        if not str(target).startswith(str(dest)):
            failures.append(f"{e.path}: path escapes the project")
            continue
        if not target.is_file():
            if e.search.strip():
                failures.append(f"{e.path}: file not found")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(e.replace, encoding="utf-8")
            applied.append(e.path)
            continue
        body = target.read_text(encoding="utf-8")
        if e.search and e.search in body:
            target.write_text(body.replace(e.search, e.replace, 1), encoding="utf-8")
            applied.append(e.path)
            continue
        norm_body, norm_search = _strip_trailing_ws(body), _strip_trailing_ws(e.search)
        if norm_search.strip() and norm_search in norm_body:
            target.write_text(norm_body.replace(norm_search, _strip_trailing_ws(e.replace), 1),
                              encoding="utf-8")
            applied.append(e.path)
            continue
        # a fragment of a line: the block format always ends SEARCH with a line
        # break, which the middle of a line does not have. Unique matches only,
        # so an ambiguous fragment still fails instead of editing the wrong spot.
        frag = e.search[:-1] if e.search.endswith("\n") else e.search
        if frag.strip() and body.count(frag) == 1:
            repl = e.replace[:-1] if e.replace.endswith("\n") else e.replace
            target.write_text(body.replace(frag, repl, 1), encoding="utf-8")
            applied.append(e.path)
            continue
        hit = _unique_dedented_match(body, e.search)
        if hit is not None:
            lines = body.splitlines(keepends=True)
            lines[hit[0]:hit[1]] = [e.replace]
            target.write_text("".join(lines), encoding="utf-8")
            applied.append(e.path)
            continue
        first = next((ln for ln in e.search.splitlines() if ln.strip()), "")[:80]
        failures.append(f"{e.path}: SEARCH text not found (starts {first!r})")
    return applied, failures


@dataclass
class AppliedOutput:
    written: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    edited: list[str] = field(default_factory=list)
    edit_failures: list[str] = field(default_factory=list)

    @property
    def touched(self) -> bool:
        return bool(self.written or self.deleted or self.edited or self.edit_failures)


def apply_output(output_text: str, dest: Path, strip_prefix: str = "") -> AppliedOutput:
    """Apply a model answer to the project copied at `dest`: DELETEs, then FILEs, then EDITs.

    `strip_prefix` drops a leading folder a model may have copied from the case
    listing (e.g. "project/") so `project/pom.xml` and `pom.xml` mean the same.
    """
    def norm(p: str) -> str:
        p = p.strip()
        if p.startswith("./"):
            p = p[2:]
        return p[len(strip_prefix):] if strip_prefix and p.startswith(strip_prefix) else p

    out = AppliedOutput()
    dest_r = dest.resolve()
    for rel in parse_deletes(output_text):
        target = (dest_r / norm(rel)).resolve()
        if str(target).startswith(str(dest_r)) and target.is_file():
            target.unlink()
            out.deleted.append(norm(rel))
    files = {norm(k): v for k, v in parse_files(output_text).items()}
    out.written = write_files(files, dest)
    edits = [Edit(norm(e.path), e.search, e.replace) for e in parse_edits(output_text)]
    out.edited, out.edit_failures = apply_edits(edits, dest)
    return out


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


def run_command(cmd: list[str], cwd: Path | None = None, timeout: int = 900,
                env: dict[str, str] | None = None) -> tuple[int, str]:
    """Run `cmd`, return (exit code, stdout+stderr). Never raises.

    Output goes to a temp file, not a pipe: a browser helper that Cypress or
    Playwright leaves behind keeps an inherited pipe open, so waiting for the
    pipe to close hung for the whole timeout after the tests had finished. We
    wait for the process itself, then kill its process group to clear such
    stragglers. On timeout the output so far is kept (it shows where it got
    stuck); exit code 124 = timeout, 127 = command not found.
    """
    import os
    import signal
    import subprocess
    import tempfile

    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as log:
        try:
            proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, start_new_session=True)
        except FileNotFoundError:
            return 127, f"command not found: {cmd[0]}"
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            rc = 124
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            proc.wait()
        log.seek(0)
        out = log.read()
    if rc == 124:
        out += f"\ntimeout after {timeout}s: {' '.join(cmd[:6])} ..."
    return rc, out


def cache_dir() -> Path:
    """Where real-suite scorers keep large, re-creatable inputs (frontends, app builds).

    $GATE1_CACHE, else ~/.cache/ai-model-lifecycle. Kept outside the repo on
    purpose: it holds node_modules and build output, gigabytes that git (and
    some synced folders) should never see.
    """
    import os

    return Path(os.environ.get("GATE1_CACHE") or Path.home() / ".cache" / "ai-model-lifecycle")


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
