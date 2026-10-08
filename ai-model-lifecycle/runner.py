#!/usr/bin/env python3
"""runner.py — Gate 1 model evaluation harness.

Iterates (pair × case × model) and calls each model through litellm with a frozen
prompt, capturing usage/latency/output into a per-run JSON:

    runs/<pair_id>/<model>.<case>.json

Design notes
------------
* temperature=0 and a fixed max_tokens so we measure model difference, not noise.
* 429 / transient errors are retried with exponential backoff, honoring any
  Retry-After header surfaced by litellm.
* A case supplies its own prompt + input artifacts: each cases/<case_id>/ dir may
  contain a `prompt.md` (the task), plus artifact files. The runner concatenates
  `prompt.md` + every artifact it is told to inline (see INLINE map below) into a
  single user message. This keeps the runner pair-agnostic and case-agnostic.
* NO live call happens at import time. Running with --dry-run only builds and
  prints the request payload; use that in CI / offline checks.

This module is intentionally runnable both as a CLI and importable as a library
(run_case / run_pair) for tests.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from common import (
    Config,
    ModelRef,
    case_dir,
    get_openrouter_token,
    load_config,
    load_env,
    run_path,
    save_run,
)

# Files, per case, that should be inlined into the prompt (relative to the case
# dir). Order matters. Cases not listed here are sent with only prompt.md plus a
# directory listing, and the model is told it may ask for more.
INLINE_ARTIFACTS: dict[str, list[str]] = {
    "r1_springboot2to3": [],          # whole Maven tree is attached as a file listing
    "r3_oracle_to_postgres": [
        "procedures/sp_customer_tier.sql",
        "procedures/sp_monthly_report.sql",
    ],
    "r4_schema_load_optimize": ["schema.sql", "target_query.sql"],
    "r5_etl_dashboard": ["etl_spec.md", "dashboard_schema.sql"],
}

SYSTEM_PROMPT = (
    "You are a senior software engineer. Complete the task exactly as specified. "
    "Output only the requested artifacts. When asked for files, emit each file in a "
    "fenced block preceded by a line `### FILE: <relative/path>`. Do not add commentary "
    "outside those blocks unless the task asks for it."
)


@dataclass
class RunResult:
    """One model-run record. Serialized verbatim to runs/<pair>/<model>.<case>.json."""

    pair_id: str
    case_id: str
    model_slug: str
    model_name: str
    role: str                       # "current" | "target"
    temperature: float
    max_tokens: int
    # --- usage ---
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0
    # --- timing ---
    latency_s: float = 0.0
    attempts: int = 0
    # --- payload ---
    prompt: str = ""
    output_text: str = ""
    # --- meta ---
    ok: bool = False
    error: str | None = None
    finish_reason: str | None = None
    created_at: float = 0.0


# --------------------------------------------------------------------------- #
# Prompt assembly                                                              #
# --------------------------------------------------------------------------- #
def _dir_listing(d: Path, limit: int = 200) -> str:
    files: list[str] = []
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.name != "prompt.md":
            files.append(str(p.relative_to(d)))
        if len(files) >= limit:
            break
    return "\n".join(files)


def build_prompt(case_id: str) -> str:
    """Read cases/<case_id>/prompt.md and inline the case's artifacts."""
    cd = case_dir(case_id)
    prompt_file = cd / "prompt.md"
    if not prompt_file.is_file():
        raise FileNotFoundError(f"missing prompt.md for case {case_id!r}: {prompt_file}")

    parts: list[str] = [prompt_file.read_text(encoding="utf-8").strip()]

    inlines = INLINE_ARTIFACTS.get(case_id, [])
    for rel in inlines:
        f = cd / rel
        if f.is_file():
            lang = rel.rsplit(".", 1)[-1]
            parts.append(f"\n--- ARTIFACT: {rel} ---\n```{lang}\n{f.read_text(encoding='utf-8').rstrip()}\n```")

    # Always attach a file listing so the model knows the full case shape.
    listing = _dir_listing(cd)
    if listing:
        parts.append(f"\n--- CASE FILE LISTING ({case_id}) ---\n{listing}")

    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# The actual model call (imported lazily so `import runner` needs no litellm)  #
# --------------------------------------------------------------------------- #
def _extract_usage(resp: Any) -> tuple[int, int, int, int, int]:
    """Pull (input, output, cache_read, cache_write, total) tokens from a response.

    litellm normalizes usage across providers; Anthropic surfaces cache info under
    prompt_tokens_details.cached_tokens / cache_creation_input_tokens. We probe
    several shapes defensively so a provider tweak never crashes the run.
    """
    usage = getattr(resp, "usage", None) or {}
    if not isinstance(usage, dict) and hasattr(usage, "model_dump"):
        usage = usage.model_dump()

    def g(*keys: str, default: int = 0) -> int:
        for k in keys:
            v = usage.get(k) if isinstance(usage, dict) else None
            if v is None and isinstance(usage, dict):
                # nested lookup, e.g. prompt_tokens_details.cached_tokens
                cur: Any = usage
                for part in k.split("."):
                    cur = cur.get(part) if isinstance(cur, dict) else None
                    if cur is None:
                        break
                v = cur
            if isinstance(v, (int, float)):
                return int(v)
        return default

    input_tokens = g("prompt_tokens", "input_tokens")
    output_tokens = g("completion_tokens", "output_tokens")
    cache_read = g(
        "prompt_tokens_details.cached_tokens",
        "cache_read_input_tokens",
        "cached_tokens",
    )
    cache_write = g("cache_creation_input_tokens", "cache_write_tokens")
    total = g("total_tokens") or (input_tokens + output_tokens)
    return input_tokens, output_tokens, cache_read, cache_write, total


def call_model(
    model_slug: str,
    prompt: str,
    *,
    temperature: float,
    max_tokens: int,
    timeout_s: int,
    max_retries: int,
    backoff_base_s: float,
    dry_run: bool = False,
) -> tuple[dict[str, Any], int, float, str, str | None, str | None]:
    """Call one model, returning (usage, attempts, latency_s, text, finish_reason, error).

    Retries on 429 / 5xx / transient errors with exponential backoff. Never
    raises for a provider error — returns an `error` string instead so the run
    loop records a failed run and continues.
    """
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0,
             "cache_write_tokens": 0, "total_tokens": 0}
    if dry_run:
        # Build the payload shape without hitting the network.
        return usage, 0, 0.0, "", None, None

    try:
        import litellm  # lazy import
    except Exception as exc:  # pragma: no cover
        return usage, 0, 0.0, "", None, f"litellm import failed: {exc}"

    token = get_openrouter_token()
    if not token:
        return usage, 0, 0.0, "", None, "OPENROUTER_TOKEN not set (check .env)"

    # Some frontier models are reasoning-only and accept a fixed temperature
    # (e.g. Opus 4.8/5.5 only accept temperature=1). Dropping unsupported params
    # lets litellm fall back to each model's default rather than hard-failing.
    litellm.drop_params = True

    last_err: str | None = None
    for attempt in range(1, max_retries + 1):
        t0 = time.time()
        try:
            # OpenRouter models must use the `openrouter/` prefix so litellm routes
            # through OpenRouter (honoring api_key) instead of the native Anthropic
            # provider path (which ignores api_key and looks for ANTHROPIC_API_KEY).
            router_slug = model_slug if model_slug.startswith("openrouter/") else f"openrouter/{model_slug}"
            resp = litellm.completion(
                model=router_slug,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_s,
                api_key=token,
            )
            latency = time.time() - t0
            i, o, cr, cw, tot = _extract_usage(resp)
            usage = {
                "input_tokens": i,
                "output_tokens": o,
                "cache_read_tokens": cr,
                "cache_write_tokens": cw,
                "total_tokens": tot,
            }
            msg = resp.choices[0].message
            text = msg.content or ""
            # Reasoning models (Opus 4.8/5.5) may return the answer in the
            # `reasoning` block and leave `content` empty. Prefer content,
            # fall back to reasoning so we don't grade an empty string.
            if not text.strip():
                reasoning = getattr(msg, "reasoning", None)
                psf = getattr(msg, "model_extra", {}) or {}
                reasoning = reasoning or psf.get("reasoning") or psf.get("reasoning_content")
                if reasoning:
                    text = reasoning if isinstance(reasoning, str) else str(reasoning)
            finish_reason = getattr(resp.choices[0], "finish_reason", None)
            return usage, attempt, latency, text, finish_reason, (None if text else f"empty completion (finish_reason={finish_reason})")

        except Exception as exc:  # noqa: BLE001 - we intentionally catch all
            last_err = f"{type(exc).__name__}: {exc}"
            status = getattr(exc, "status_code", None)
            retryable = status in (429, 500, 502, 503, 504, 529) or status is None
            if attempt >= max_retries or not retryable:
                break
            # Exponential backoff; honor Retry-After if the provider gave one.
            retry_after = None
            resp_hdr = getattr(exc, "response", None)
            if resp_hdr is not None:
                try:
                    retry_after = resp_hdr.headers.get("Retry-After")
                except Exception:
                    retry_after = None
            sleep_s = float(retry_after) if retry_after else backoff_base_s * (2 ** (attempt - 1))
            time.sleep(min(sleep_s, 60.0))

    return usage, max_retries, 0.0, "", None, last_err


# --------------------------------------------------------------------------- #
# Run one (model × case)                                                       #
# --------------------------------------------------------------------------- #
def run_case(
    cfg: Config,
    pair_id: str,
    case_id: str,
    model: ModelRef,
    role: str,
    *,
    dry_run: bool = False,
    rep: int = 0,
) -> RunResult:
    prompt = build_prompt(case_id)
    usage, attempts, latency, text, finish_reason, err = call_model(
        model.id,
        prompt,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        timeout_s=cfg.timeout_s,
        max_retries=cfg.max_retries,
        backoff_base_s=cfg.backoff_base_s,
        dry_run=dry_run,
    )
    result = RunResult(
        pair_id=pair_id,
        case_id=case_id,
        model_slug=model.id,
        model_name=model.name,
        role=role,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        latency_s=round(latency, 4),
        attempts=attempts,
        prompt=prompt,
        output_text=text,
        finish_reason=finish_reason,
        ok=err is None,
        error=err,
        created_at=time.time(),
        **usage,
    )
    path = run_path(pair_id, model.id, case_id, rep=rep)
    save_run(asdict(result), path)
    return result

def run_pair(
    cfg: Config,
    pair_id: str,
    *,
    case: str | None = None,
    dry_run: bool = False,
    repeats: int = 1,
) -> list[RunResult]:
    pair = cfg.get_pair(pair_id)
    results: list[RunResult] = []
    for case_id in cfg.selected_cases(case):
        for model, role in ((pair.current, "current"), (pair.target, "target")):
            for rep in range(repeats):
                res = run_case(cfg, pair_id, case_id, model, role, dry_run=dry_run)
                status = "OK" if res.ok else f"FAIL ({res.error})"
                tag = f" [rep {rep+1}/{repeats}]" if repeats > 1 else ""
                print(f"[{pair_id}] {role:7s} {model.name:20s} {case_id:24s} "
                      f"{res.latency_s:7.2f}s{tag}  {status}", file=sys.stderr)
                if res.ok:
                    results.append(res)
    return results


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gate 1 model evaluation harness")
    ap.add_argument("--pair", help="pair id from models.yaml (e.g. opus-4.8-vs-5.5)")
    ap.add_argument("--all-pairs", action="store_true", help="run every pair in models.yaml")
    ap.add_argument("--case", help="run a single case id (default: all cases for the pair)")
    ap.add_argument("--repeats", type=int, default=1, metavar="N",
                    help="run each (model, case) N times to capture latency/cost variance")
    ap.add_argument("--dry-run", action="store_true",
                    help="build prompts only, no network calls (CI-safe)")
    args = ap.parse_args(argv)

    load_env()
    cfg = load_config()

    if args.all_pairs:
        pair_ids = [p.id for p in cfg.pairs]
    elif args.pair:
        pair_ids = [args.pair]
    else:
        ap.error("pass --pair <id> or --all-pairs")

    for pid in pair_ids:
        run_pair(cfg, pid, case=args.case, dry_run=args.dry_run, repeats=args.repeats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
