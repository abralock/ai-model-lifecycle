"""common.py — shared helpers for the Gate 1 harness.

Loads config (models.yaml + .env), normalizes paths, and provides small utilities
used by runner.py, scorers/ and report.py. Pure-stdlib-aware so it imports cleanly
even before the optional deps are installed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent
RUNS_DIR = REPO_ROOT / "runs"
CASES_DIR = REPO_ROOT / "cases"
SCORERS_DIR = REPO_ROOT / "scorers"


# --------------------------------------------------------------------------- #
# .env loading (best-effort — never hard-fail if dotenv is absent)             #
# --------------------------------------------------------------------------- #
def load_env() -> None:
    """Load .env from the repo root if python-dotenv is available."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:  # pragma: no cover - optional at import time
        return
    load_dotenv(REPO_ROOT / ".env")


def get_openrouter_token() -> str | None:
    """Return the OpenRouter token from the environment (after load_env)."""
    return os.environ.get("OPENROUTER_TOKEN") or None


# --------------------------------------------------------------------------- #
# models.yaml                                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class ModelRef:
    id: str
    name: str


@dataclass
class Pair:
    id: str
    current: ModelRef
    target: ModelRef


@dataclass
class Config:
    pairs: list[Pair] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    cases: list[str] = field(default_factory=list)

    @property
    def temperature(self) -> float:
        return float(self.defaults.get("temperature", 0))

    @property
    def max_tokens(self) -> int:
        return int(self.defaults.get("max_tokens", 8192))

    @property
    def timeout_s(self) -> int:
        return int(self.defaults.get("timeout_s", 600))

    @property
    def max_retries(self) -> int:
        return int(self.defaults.get("max_retries", 5))

    @property
    def backoff_base_s(self) -> float:
        return float(self.defaults.get("backoff_base_s", 2))

    def get_pair(self, pair_id: str) -> Pair:
        for p in self.pairs:
            if p.id == pair_id:
                return p
        raise KeyError(f"pair id not found in models.yaml: {pair_id!r}")

    def selected_cases(self, only: str | None = None) -> list[str]:
        """Return the case list, optionally narrowed to a single case id.

        Keeps mutation off the shared Config object (runner used to reassign
        cfg.cases, which surprises callers that reuse the config).
        """
        if only:
            return [only]
        return list(self.cases)


def load_config(path: Path | str | None = None) -> Config:
    """Parse models.yaml into a Config."""
    path = Path(path) if path else (REPO_ROOT / "models.yaml")
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    pairs: list[Pair] = []
    for entry in raw.get("pairs", []) or []:
        pairs.append(
            Pair(
                id=entry["id"],
                current=ModelRef(**entry["current"]),
                target=ModelRef(**entry["target"]),
            )
        )
    return Config(
        pairs=pairs,
        defaults=raw.get("defaults", {}) or {},
        cases=list(raw.get("cases", []) or []),
    )


# --------------------------------------------------------------------------- #
# run IO                                                                       #
# --------------------------------------------------------------------------- #
def run_path(pair_id: str, model_slug: str, case_id: str, rep: int = 0, run_dt: str | None = None) -> Path:
    """Canonical path for a per-run JSON.

    The model slug contains '/' (e.g. anthropic/claude-opus-4.8); we keep the
    full slug in the filename but flatten '/' -> '__' to stay filesystem-safe.
    Date-stamped so repeated runs are never overwritten and history is preserved.
    """
    safe_model = model_slug.replace("/", "__")
    stamp = run_dt or datetime.now(timezone.utc).strftime("%Y%m%d")
    if rep > 0:
        return RUNS_DIR / pair_id / f"{safe_model}.{case_id}.{stamp}.r{rep}.json"
    return RUNS_DIR / pair_id / f"{safe_model}.{case_id}.{stamp}.json"


def save_run(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)


def load_runs(pair_id: str) -> list[dict[str, Any]]:
    """Load every per-run JSON for a pair. Missing dir -> empty list."""
    d = RUNS_DIR / pair_id
    if not d.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for f in sorted(d.glob("*.json")):
        if f.name == "REPORT.md" or f.suffix != ".json":
            continue
        try:
            with open(f, "r", encoding="utf-8") as fh:
                out.append(json.load(fh))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def case_dir(case_id: str) -> Path:
    return CASES_DIR / case_id
