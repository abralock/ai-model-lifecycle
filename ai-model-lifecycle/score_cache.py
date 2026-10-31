"""score_cache.py — scorer results memoized by (scorer source, case, answer).

Scoring a real-suite answer takes a Maven or Angular build, so reports that
score many saved answers (mlflow_export.py, leaderboard.py) share this cache.
A key includes a fingerprint of every scorer source file, so changing a scorer
re-scores; a result the scorer could not verify (missing Docker, Postgres or a
setup cache, a scorer crash) is never cached, so fixing the setup re-scores it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from scorers.dispatch import score_case as _score_case
from verify_failures import _HARNESS_PATTERNS

HARNESS_DIR = Path(__file__).resolve().parent
CACHE_FILE = HARNESS_DIR / ".mlflow_score_cache.json"


def _scorer_fingerprint() -> str:
    h = hashlib.sha256()
    # every scorer file, hidden test fixtures included: a changed hidden test
    # changes the verdict as much as a changed scorer does
    for f in sorted((HARNESS_DIR / "scorers").rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            h.update(f.relative_to(HARNESS_DIR).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()[:16]


class ScoreCache:
    """Memoizes scorer results by (scorer source, case, answer)."""

    def __init__(self, path: Path | None = CACHE_FILE, scorer=_score_case):
        self.path, self.scorer = path, scorer
        self.fp = _scorer_fingerprint()
        self.data: dict = {}
        if path and path.exists():
            self.data = json.loads(path.read_text())

    def __call__(self, case_id: str, output_text: str, slug: str):
        key = hashlib.sha256(f"{self.fp}\0{case_id}\0{output_text}".encode()).hexdigest()
        if key in self.data:
            return SimpleNamespace(**self.data[key])
        sr = self.scorer(case_id, output_text, slug)
        result = {"passed": bool(sr.passed), "reason": sr.reason or ""}
        # a harness failure (unverified, scorer crash) says nothing about the
        # answer: keep it out of the cache so a fixed setup re-scores it
        if not _HARNESS_PATTERNS.search(result["reason"]):
            self.data[key] = result
            if self.path:
                self.path.write_text(json.dumps(self.data))
        return SimpleNamespace(**result)
