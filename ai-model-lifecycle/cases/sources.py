"""cases/sources.py — fetch the real-suite case sources from their GitHub forks.

The real-project cases (r1b, r2) are built from open-source code that is NOT
committed here: it is fetched from our forks at a pinned commit, and only the
files the case uses are copied into the case folder (gitignored):

    r1b_jhipster_boot3/project/   abralock/jhipster-sample-app @ v7.9.3
    r2_gwt_to_angular/gwt/        abralock/GWTP-Samples @ 7dce06a (carstore client + shared)
    r2_gwt_to_angular/e2e/        the same commit (carstore Cucumber features + page objects)

`sources.lock.json` (next to this file) lists, per case, the fork, the full
commit and every file with its SHA-256. A fetch that does not reproduce those
bytes fails, so a changed fork can never silently change a task. Same files,
same place: the prompt the runner builds is the one the committed runs used.

Fetching needs git and network once; then the files stay until deleted.

    python -m cases.sources            # fetch every case (no-op when already there)
    python -m cases.sources --check    # verify only, exit 1 if anything is missing or changed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent
LOCK_FILE = CASES_DIR / "sources.lock.json"


class SourceError(RuntimeError):
    pass


def _lock() -> dict:
    return json.loads(LOCK_FILE.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_cache() -> Path:
    # same cache root as the real-suite scorers (scorers.base.cache_dir)
    root = Path(os.environ.get("GATE1_CACHE") or Path.home() / ".cache" / "ai-model-lifecycle")
    return root / "src"


def problems(case_id: str) -> list[str]:
    """Missing or changed files of a case's fetched sources ([] = all present and exact)."""
    out: list[str] = []
    for src in _lock().get(case_id, []):
        for rel, digest in src["files"].items():
            f = CASES_DIR / case_id / src["to"] / rel
            if not f.is_file():
                out.append(f"missing {f.relative_to(CASES_DIR)}")
            elif _sha256(f) != digest:
                out.append(f"changed {f.relative_to(CASES_DIR)}")
    return out


def _fetch_commit(repo: str, commit: str) -> Path:
    """A local git dir holding `commit` of `repo` (shallow, by full SHA; no tags needed)."""
    d = _git_cache() / repo.rstrip("/").split("/")[-1].removesuffix(".git")
    if not (d / ".git").is_dir():
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(d)], check=True)
    have = subprocess.run(["git", "-C", str(d), "cat-file", "-e", f"{commit}^{{commit}}"],
                          capture_output=True).returncode == 0
    if not have:
        r = subprocess.run(["git", "-C", str(d), "fetch", "-q", "--depth", "1", repo, commit],
                           capture_output=True, text=True)
        if r.returncode:
            raise SourceError(f"git fetch {repo} {commit} failed: {r.stderr.strip()}")
    return d


def fetch(case_id: str) -> None:
    """Copy the case's locked files from their fork into the case folder and verify them."""
    for src in _lock().get(case_id, []):
        git_dir = _fetch_commit(src["repo"], src["commit"])
        dest = CASES_DIR / case_id / src["to"]
        with tempfile.TemporaryDirectory() as tmp:
            paths = [f"{src['from']}/{rel}" if src["from"] else rel for rel in src["files"]]
            archive = subprocess.run(["git", "-C", str(git_dir), "archive", src["commit"], "--", *paths],
                                     capture_output=True, check=False)
            if archive.returncode:
                raise SourceError(f"{case_id}: git archive failed: {archive.stderr.decode().strip()}")
            subprocess.run(["tar", "-x", "-C", tmp], input=archive.stdout, check=True)
            base = Path(tmp) / src["from"] if src["from"] else Path(tmp)
            for rel in src["files"]:
                (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(base / rel, dest / rel)
    bad = problems(case_id)
    if bad:
        raise SourceError(f"{case_id}: fetched sources do not match sources.lock.json: {bad[:5]}")


def ensure(case_id: str) -> None:
    """Make sure a case's sources are present and exact; fetch them the first time.

    No-op for cases without locked sources (the sanity suite's own files).
    """
    if case_id not in _lock():
        return
    bad = problems(case_id)
    if not bad:
        return
    if any(p.startswith("changed") for p in bad):
        raise SourceError(f"{case_id}: sources differ from the pinned fork commit: {bad[:5]} "
                          f"(delete them and re-run `python -m cases.sources`)")
    print(f"fetching {case_id} sources from their fork (one time)...", file=sys.stderr)
    fetch(case_id)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch the real-suite case sources from their forks")
    ap.add_argument("--check", action="store_true", help="verify only; exit 1 if anything is missing or changed")
    ap.add_argument("cases", nargs="*", help="case ids (default: every case in sources.lock.json)")
    args = ap.parse_args(argv)
    lock = _lock()
    status = 0
    for case_id in args.cases or list(lock):
        try:
            if args.check:
                bad = problems(case_id)
                if bad:
                    raise SourceError(f"{len(bad)} problem(s), e.g. {bad[0]}")
            else:
                ensure(case_id)
            n = sum(len(s["files"]) for s in lock[case_id])
            forks = dict.fromkeys(f"{s['repo']} @ {s['commit'][:7]}" for s in lock[case_id])
            print(f"{case_id}: ok ({n} files from {', '.join(forks)})")
        except SourceError as exc:
            print(f"{case_id}: {exc}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
