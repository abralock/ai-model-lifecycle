"""common.py — shared helpers for the Gate 1 harness.

Loads config (models.yaml + .env), normalizes paths, and provides small utilities
used by runner.py, scorers/ and report.py. Pure-stdlib-aware so it imports cleanly
even before the optional deps are installed.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, replace
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
class ApiRef:
    """A non-OpenRouter inference gateway from the top-level `apis:` map in
    models.yaml (e.g. OpenCode Go, an OpenAI-compatible chat-completions API).

    `family` is the API dialect the gateway speaks for the models we route to
    it: "chat" (OpenAI chat completions), "responses" (OpenAI Responses API —
    Go serves GPT Luna / Grok / Muse Spark only at `/v1/responses`), or
    "messages" (Anthropic messages API — Go's MiniMax / Qwen3.x). A model may
    override it with its own `family:` (ModelRef.family) when one gateway
    serves different models over different dialects.
    """

    id: str
    base_url: str
    api_key_env: str = ""
    family: str = "chat"

    def key(self) -> str | None:
        """The gateway's API key from the environment (after load_env)."""
        return os.environ.get(self.api_key_env) if self.api_key_env else None


@dataclass
class ModelRef:
    id: str
    name: str
    # Key into Config.apis. None (default) = call through OpenRouter.
    api: str | None = None
    # Extra request params merged into the completion call (e.g.
    # {reasoning_effort: low} for thinking-heavy models). Set the same
    # value on both models of a pair to keep the comparison symmetric.
    params: dict[str, Any] | None = None
    # Dialect override for the gateway (e.g. `family: messages` on one model
    # whose gateway entry defaults to chat). None = use the gateway's family.
    # Lets one gateway (one provider string) serve models over different
    # dialects, so a pair can mix e.g. a messages-API model with a chat one.
    family: str | None = None


@dataclass
class Pair:
    id: str
    current: ModelRef
    target: ModelRef
    # OpenRouter provider routing for this pair. `provider_set` is False when the
    # pair doesn't mention `provider` (then defaults.provider applies); an
    # explicit `provider: null` turns pinning off for the pair.
    provider: dict[str, Any] | None = None
    provider_set: bool = False
    # Per-pair call timeout floor (slow gateways/models need more than
    # defaults.timeout_s; a suite demanding more still wins). None = default.
    timeout_s: int | None = None


DEFAULT_SUITE = "sanity"


@dataclass
class Config:
    pairs: list[Pair] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    cases: list[str] = field(default_factory=list)
    # Which case suite `cases` holds: "sanity" (the top-level `cases:` list) or
    # a name under `suites:` in models.yaml (see load_config).
    suite: str = DEFAULT_SUITE
    suites: list[str] = field(default_factory=list)
    # Non-OpenRouter gateways, keyed by their id in models.yaml `apis:`.
    apis: dict[str, ApiRef] = field(default_factory=dict)

    @property
    def report_name(self) -> str:
        """Scorecard filename for this suite: REPORT.md for sanity, else REPORT.<suite>.md."""
        return "REPORT.md" if self.suite == DEFAULT_SUITE else f"REPORT.{self.suite}.md"

    @property
    def temperature(self) -> float:
        return float(self.defaults.get("temperature", 0))

    @property
    def max_tokens(self) -> int:
        return int(self.defaults.get("max_tokens", 8192))

    def max_tokens_for(self, model_id: str) -> int:
        """Output limit for one model: `max_tokens_by_model` (for models that
        allow less than the suite's limit), else `max_tokens`."""
        per_model = self.defaults.get("max_tokens_by_model") or {}
        return int(per_model.get(model_id, self.max_tokens))

    @property
    def timeout_s(self) -> int:
        return int(self.defaults.get("timeout_s", 600))

    def timeout_s_for(self, pair_id: str) -> int:
        """Call timeout for a pair: never below its own `timeout_s` floor (slow
        gateways/models), but a suite may still demand more (real: 1800s)."""
        pair = self.get_pair(pair_id)
        if pair.timeout_s:
            return max(self.timeout_s, int(pair.timeout_s))
        return self.timeout_s

    @property
    def max_retries(self) -> int:
        return int(self.defaults.get("max_retries", 5))

    @property
    def backoff_base_s(self) -> float:
        return float(self.defaults.get("backoff_base_s", 2))

    @property
    def reasoning(self) -> dict[str, Any] | None:
        """OpenRouter `reasoning` preferences (e.g. {"max_tokens": 16000}), or None
        to leave each model's default thinking behavior alone."""
        return self.defaults.get("reasoning") or None

    def provider_for(self, pair_id: str) -> dict[str, Any] | None:
        """OpenRouter provider preferences for a pair (sent on every call).

        Both models of a pair should be served by the SAME provider, or the
        Time axis measures provider speed instead of model speed.
        """
        pair = self.get_pair(pair_id)
        if pair.provider_set:
            return pair.provider
        return self.defaults.get("provider")

    def get_pair(self, pair_id: str) -> Pair:
        for p in self.pairs:
            if p.id == pair_id:
                return p
        raise KeyError(f"pair id not found in models.yaml: {pair_id!r}")

    def api_for(self, model: ModelRef) -> ApiRef | None:
        """The gateway a model is called through, or None for OpenRouter.

        A dangling `api:` reference in models.yaml is a config typo — fail
        loudly here rather than after spending on calls. A model-level
        `family:` overrides the gateway's dialect for that model.
        """
        if model.api is None:
            return None
        try:
            api = self.apis[model.api]
        except KeyError:
            known = ", ".join(sorted(self.apis)) or "(none)"
            raise KeyError(
                f"model {model.id!r} references unknown api {model.api!r} "
                f"(known: {known}) — check the `apis:` map in models.yaml"
            ) from None
        if model.family:
            api = replace(api, family=model.family)
        return api

    def selected_cases(self, only: str | None = None) -> list[str]:
        """Return the case list, optionally narrowed to a single case id.

        Keeps mutation off the shared Config object (runner used to reassign
        cfg.cases, which surprises callers that reuse the config).
        """
        if only:
            return [only]
        return list(self.cases)


def load_config(path: Path | str | None = None, suite: str | None = None) -> Config:
    """Parse models.yaml into a Config.

    `suite` picks the case list: None or "sanity" -> the top-level `cases:`;
    any other name -> `suites.<name>.cases`, with that suite's other keys
    (e.g. max_tokens, timeout_s) overriding `defaults`. Everything downstream
    reads `cfg.cases` / `cfg.defaults`, so it needs no suite awareness.
    """
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
                provider=entry.get("provider"),
                provider_set="provider" in entry,
                timeout_s=entry.get("timeout_s"),
            )
        )
    suites: dict[str, Any] = raw.get("suites", {}) or {}
    defaults = dict(raw.get("defaults", {}) or {})
    cases = list(raw.get("cases", []) or [])
    apis = {
        api_id: ApiRef(id=api_id, **(spec or {}))
        for api_id, spec in (raw.get("apis", {}) or {}).items()
    }
    suite = suite or DEFAULT_SUITE
    if suite != DEFAULT_SUITE:
        if suite not in suites:
            known = ", ".join([DEFAULT_SUITE, *suites])
            raise KeyError(f"suite not found in models.yaml: {suite!r} (known: {known})")
        overrides = dict(suites[suite] or {})
        cases = list(overrides.pop("cases", []) or [])
        defaults.update(overrides)
    return Config(
        pairs=pairs,
        defaults=defaults,
        cases=cases,
        suite=suite,
        suites=[DEFAULT_SUITE, *suites],
        apis=apis,
    )


# --------------------------------------------------------------------------- #
# run IO                                                                       #
# --------------------------------------------------------------------------- #
def new_run_id() -> str:
    """A run id: the UTC start time of one runner invocation, e.g. 20261009T143005Z.

    Ids sort chronologically as strings, and a legacy date-only id (20261009)
    sorts before every new-style id of the same day.
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_path(pair_id: str, model_slug: str, case_id: str, rep: int = 0, run_id: str | None = None) -> Path:
    """Canonical path for a per-run JSON.

    The model slug contains '/' (e.g. anthropic/claude-opus-4.8); we keep the
    full slug in the filename but flatten '/' -> '__' to stay filesystem-safe.
    Stamped with the run id of the invocation that wrote it, so a later run
    (even on the same day) never overwrites or mixes with an earlier one.
    """
    safe_model = model_slug.replace("/", "__")
    stamp = run_id or new_run_id()
    if rep > 0:
        return RUNS_DIR / pair_id / f"{safe_model}.{case_id}.{stamp}.r{rep}.json"
    return RUNS_DIR / pair_id / f"{safe_model}.{case_id}.{stamp}.json"


def save_run(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)


def run_id_of(filename: str) -> str | None:
    """The run id in a run filename (see run_path), or None.

    Matches new ids (20261009T143005Z) and legacy date-only ids (20261009).
    """
    m = re.search(r"\.(\d{8}(?:T\d{6}Z)?)(?:\.r\d+)?\.json$", filename)
    return m.group(1) if m else None


def list_runs(pair_id: str) -> list[str]:
    """Every run id present for a pair, oldest first."""
    d = RUNS_DIR / pair_id
    if not d.is_dir():
        return []
    return sorted({rid for f in d.glob("*.json") if (rid := run_id_of(f.name))})


def load_runs(pair_id: str, run: str | None = None) -> list[dict[str, Any]]:
    """Load the per-run JSONs of ONE run for a pair. Missing dir -> empty list.

    `run` is a run id (see new_run_id; a legacy run's id is its YYYYMMDD date);
    by default the most recent run. Runs made under different prompts/scorers
    are never silently mixed into one scorecard. Each record gets `_file` (its
    filename) and `_run`.
    """
    d = RUNS_DIR / pair_id
    if not d.is_dir():
        return []
    if run is None:
        runs = list_runs(pair_id)
        if not runs:
            return []
        run = runs[-1]
    out: list[dict[str, Any]] = []
    for f in sorted(d.glob("*.json")):
        if run_id_of(f.name) != run:
            continue
        try:
            with open(f, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue
        rec["_file"], rec["_run"] = f.name, run
        out.append(rec)
    return out


def case_dir(case_id: str) -> Path:
    return CASES_DIR / case_id
