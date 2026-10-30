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
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, NamedTuple

from cases import sources
from common import (
    ApiRef,
    Config,
    ModelRef,
    case_dir,
    get_openrouter_token,
    load_config,
    load_env,
    new_run_id,
    run_path,
    save_run,
)

# Files, per case, that should be inlined into the prompt (relative to the case
# dir). Order matters; glob patterns are expanded in sorted order. Cases not
# listed here are sent with only prompt.md plus a directory listing.
INLINE_ARTIFACTS: dict[str, list[str]] = {
    # the model must see the real sources to migrate them (with only a listing it
    # can either refuse or invent code, and invented code is not a migration)
    "r1_springboot2to3": ["pom.xml", "src/**/*"],
    "r3_oracle_to_postgres": [
        "procedures/sp_customer_tier.sql",
        "procedures/sp_monthly_report.sql",
    ],
    "r4_schema_load_optimize": ["schema.sql", "target_query.sql"],
    "r5_etl_dashboard": ["etl_spec.md", "dashboard_schema.sql"],
    # --- real suite (real open-source projects; see cases/<id>/README.md) ---
    "r1b_jhipster_boot3": [
        "project/pom.xml",
        "project/src/main/java/**/*.java",
        "project/src/main/resources/config/*.yml",
        "project/src/main/resources/logback-spring.xml",
    ],
    "r2_gwt_to_angular": [
        "gwt/**/*",
        "e2e/**/*",
        "workspace/package.json",
        "workspace/angular.json",
        "workspace/tsconfig.json",
        "workspace/src/main.ts",
        "workspace/src/index.html",
        "workspace/src/styles.css",
    ],
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
    suite: str = "sanity"           # case suite from models.yaml (common.load_config)
    rep: int = 0                    # repeat index (0-based) within one --repeats run
    run_id: str = ""                # one id per runner invocation (see common.new_run_id)
    # --- usage ---
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0
    # --- provider / billing (OpenRouter) ---
    provider_requested: dict[str, Any] | None = None   # routing prefs sent
    reasoning_requested: dict[str, Any] | None = None  # thinking budget sent (None = model default)
    reasoning_tokens: int = 0                           # of output_tokens, spent thinking (if reported)
    provider: str | None = None                         # provider that served it
    billed_cost_usd: float | None = None                # OpenRouter usage.cost
    # Claude Code's total_cost_usd: an estimate at API list prices, not a bill
    # (the subscription does not bill per call).
    cost_estimate_usd: float | None = None
    # Claude Code only: requests the CLI made for this answer (more than 1 =
    # it hit the output limit and was continued) and its time in the API.
    num_turns: int | None = None
    duration_api_ms: int | None = None
    # --- timing ---
    latency_s: float = 0.0
    # Client-observed reasoning-stream time; None on legacy/uninstrumented calls.
    thinking_time_s: float | None = None
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
# Notes about a case written after its runs (not task input) stay out of the
# listing, so adding one never changes the prompt the committed runs used.
_NOT_LISTED = {"prompt.md", "NEAR_MISS.md"}


def _dir_listing(d: Path, limit: int = 200) -> str:
    files: list[str] = []
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.name not in _NOT_LISTED:
            files.append(str(p.relative_to(d)))
        if len(files) >= limit:
            break
    return "\n".join(files)


def build_prompt(case_id: str) -> str:
    """Read cases/<case_id>/prompt.md and inline the case's artifacts.

    Real-suite sources are fetched from their forks first (cases/sources.py).
    """
    sources.ensure(case_id)
    cd = case_dir(case_id)
    prompt_file = cd / "prompt.md"
    if not prompt_file.is_file():
        raise FileNotFoundError(f"missing prompt.md for case {case_id!r}: {prompt_file}")

    parts: list[str] = [prompt_file.read_text(encoding="utf-8").strip()]

    inlines: list[str] = []
    for pattern in INLINE_ARTIFACTS.get(case_id, []):
        if any(ch in pattern for ch in "*?["):
            inlines += sorted(str(p.relative_to(cd)) for p in cd.glob(pattern) if p.is_file())
        else:
            inlines.append(pattern)
    for rel in inlines:
        f = cd / rel
        if f.is_file():
            try:
                body = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # binary (e.g. a TLS keystore): it stays in the project, not the prompt
            lang = rel.rsplit(".", 1)[-1]
            parts.append(f"\n--- ARTIFACT: {rel} ---\n```{lang}\n{body.rstrip()}\n```")

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
        "input_tokens_details.cached_tokens",   # Responses API shape
        "cache_read_input_tokens",
        "cached_tokens",
        "prompt_cache_hit_tokens",   # DeepSeek-style cache accounting
    )
    cache_write = g("cache_creation_input_tokens", "cache_write_tokens")
    total = g("total_tokens") or (input_tokens + output_tokens)
    return input_tokens, output_tokens, cache_read, cache_write, total


class CallResult(NamedTuple):
    usage: dict[str, Any]
    attempts: int
    latency_s: float
    text: str
    finish_reason: str | None
    error: str | None
    provider: str | None = None
    billed_cost_usd: float | None = None
    reasoning_tokens: int = 0
    cost_estimate_usd: float | None = None
    # Set when the whole run must stop (Claude Code subscription usage limit):
    # run_case raises UsageLimitReached with it instead of recording a run.
    stop_run: str | None = None
    num_turns: int | None = None
    duration_api_ms: int | None = None
    thinking_time_s: float | None = None


class _ThinkingTimer:
    """Measure client-observed reasoning phases in a streaming response.

    A phase starts at the first reasoning event and ends at the next visible
    answer event (or at end-of-stream for a thinking-only response). This is
    stream time, not provider-reported compute time.
    """

    def __init__(self):
        self.total = 0.0
        self.started_at: float | None = None
        self.seen_reasoning = False

    def reasoning(self, now: float) -> None:
        self.seen_reasoning = True
        if self.started_at is None:
            self.started_at = now

    def answer(self, now: float) -> None:
        if self.started_at is not None:
            self.total += max(0.0, now - self.started_at)
            self.started_at = None

    def finish(self, now: float) -> float | None:
        self.answer(now)
        return self.total if self.seen_reasoning else None


def _observe_stream_chunk(chunk: Any, timer: _ThinkingTimer, now: float) -> None:
    """Classify one LiteLLM chat/messages chunk without consuming its payload."""
    choices = chunk.get("choices") if isinstance(chunk, dict) else getattr(chunk, "choices", None)
    if not choices:
        return
    choice = choices[0]
    delta = choice.get("delta") if isinstance(choice, dict) else getattr(choice, "delta", None)
    if delta is not None and not isinstance(delta, dict) and hasattr(delta, "model_dump"):
        delta = delta.model_dump()
    if not isinstance(delta, dict):
        return
    reasoning = (delta.get("reasoning_content") or delta.get("reasoning")
                 or delta.get("thinking_blocks") or delta.get("reasoning_items"))
    if reasoning:
        timer.reasoning(now)
    if delta.get("content"):
        timer.answer(now)


def _extract_reasoning_tokens(resp: Any) -> int:
    """Output tokens spent on hidden thinking (usage.completion_tokens_details,
    or output_tokens_details for the Responses API), or 0."""
    usage = getattr(resp, "usage", None)
    if usage is not None and not isinstance(usage, dict) and hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    details = usage.get("completion_tokens_details") if isinstance(usage, dict) else None
    if not isinstance(details, dict):
        details = usage.get("output_tokens_details") if isinstance(usage, dict) else None
    n = details.get("reasoning_tokens") if isinstance(details, dict) else None
    return int(n) if isinstance(n, (int, float)) else 0


# --------------------------------------------------------------------------- #
# Responses API (family: responses — Go serves GPT Luna / Grok / Muse Spark)   #
# --------------------------------------------------------------------------- #
def _as_dict(obj: Any) -> dict[str, Any]:
    """model_dump a pydantic-ish response into a plain dict (best effort)."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            return {}
    return {}


def _responses_text(resp: Any) -> str:
    """Join the output_text parts of a Responses API reply.

    Reasoning items are skipped — hidden thinking is never graded as the
    answer (same rule as the chat route's reasoning_effort note).
    """
    data = _as_dict(resp)
    parts: list[str] = []
    for item in data.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for part in item.get("content") or []:
            if isinstance(part, dict) and part.get("type") == "output_text":
                t = part.get("text")
                if isinstance(t, str):
                    parts.append(t)
    return "\n".join(parts)


def _responses_finish_reason(resp: Any) -> str | None:
    """Map Responses API status onto a finish_reason-ish string."""
    status = _as_dict(resp).get("status")
    if status == "completed":
        return "stop"
    if status == "incomplete":
        reason = _as_dict(_as_dict(resp).get("incomplete_details")).get("reason")
        return str(reason) if reason else "incomplete"
    return str(status) if status else None


def _extract_billed_cost(resp: Any) -> float | None:
    """OpenRouter's billed cost for the call (usage.cost), if it reported one."""
    usage = getattr(resp, "usage", None)
    if usage is not None and not isinstance(usage, dict) and hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    cost = usage.get("cost") if isinstance(usage, dict) else getattr(usage, "cost", None)
    return float(cost) if isinstance(cost, (int, float)) else None


# --------------------------------------------------------------------------- #
# Claude Code CLI (family: claude-code — the personal claude.ai subscription)  #
# --------------------------------------------------------------------------- #
class ClaudeCodeNotReady(RuntimeError):
    """The Claude Code CLI is missing or not logged in with the subscription."""


class UsageLimitReached(RuntimeError):
    """The Claude Code subscription usage limit was hit: stop the whole run."""


# Lean flags: without them Claude Code's own instructions add 5,000-10,500
# input tokens per call, different per model (docs/CLAUDE_CODE_GATEWAY.md §2).
CLAUDE_CODE_FLAGS = [
    "--output-format", "json",
    "--tools", "",
    "--setting-sources", "",
    "--strict-mcp-config",
    "--disable-slash-commands",
    "--exclude-dynamic-system-prompt-sections",
    "--no-session-persistence",
]

# Credentials that would make the CLI use something other than the claude.ai
# login (an API key, a cloud provider, a proxy). Removed from the CLI's
# environment so it can never bill an API key by accident.
_CC_STRIPPED_ENV = {
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "AWS_BEARER_TOKEN_BEDROCK",
}
_CC_STRIPPED_PREFIXES = (
    "CLAUDE_CODE_USE_",          # BEDROCK / VERTEX / FOUNDRY / ...
    "ANTHROPIC_FOUNDRY_", "ANTHROPIC_AWS_", "ANTHROPIC_BEDROCK_", "ANTHROPIC_VERTEX_",
)

_CC_RETRY_STATUS = {429, 500, 502, 503, 504, 529}
# The exact text of a subscription limit hit is not confirmed yet; match
# conservatively and stop rather than retry into the limit.
_CC_LIMIT_RE = re.compile(r"usage limit|rate limit|hit your limit", re.IGNORECASE)


def _claude_code_env(max_tokens: int | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items()
           if k not in _CC_STRIPPED_ENV and not k.startswith(_CC_STRIPPED_PREFIXES)}
    if max_tokens:
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(max_tokens)
    return env


def _claude_code_effort(reasoning: dict[str, Any] | None) -> str | None:
    """The suite's thinking effort (models.yaml `reasoning: {effort: ...}`) as
    a `--effort` level, or None to leave each model's default."""
    effort = (reasoning or {}).get("effort")
    return str(effort) if effort else None


def claude_code_preflight() -> None:
    """Refuse to run unless the `claude` CLI is on PATH and logged in with the
    claude.ai subscription (checked with the same environment the calls use)."""
    if shutil.which("claude") is None:
        raise ClaudeCodeNotReady("Claude Code CLI `claude` not found on PATH")
    try:
        proc = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True,
                              timeout=60, env=_claude_code_env())
        status = json.loads(proc.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise ClaudeCodeNotReady(f"`claude auth status` failed: {exc}") from None
    if not status.get("loggedIn"):
        raise ClaudeCodeNotReady("Claude Code is not logged in — run `claude auth login` "
                                 "with your claude.ai account")
    method = status.get("authMethod")
    if method != "claude.ai":
        raise ClaudeCodeNotReady(
            f"Claude Code is logged in with {method!r}, not the claude.ai subscription "
            "(an API key or cloud provider would be billed) — this route is for the "
            "personal subscription only")


def _served_models_match(model_usage: Any, model_slug: str) -> tuple[bool, str]:
    """Whether Claude Code's `modelUsage` shows the asked-for model (a dated id
    like claude-haiku-4-5-20251001 counts; claude-sonnet-5-5 is not claude-sonnet-5)."""
    if not isinstance(model_usage, dict) or not model_usage:
        return True, ""
    pat = re.compile(rf"{re.escape(model_slug)}(-\d{{8}})?(\[.*\])?")
    served = ", ".join(sorted(model_usage))
    return any(pat.fullmatch(k) for k in model_usage), served


def _cc_usage(out: dict[str, Any]) -> tuple[dict[str, int], float | None, int]:
    """(usage, cost estimate, thinking tokens) from a `claude -p` JSON result.
    The prompt total includes cache tokens (same meaning as the other routes)."""
    u = out.get("usage") or {}
    cr = int(u.get("cache_read_input_tokens") or 0)
    cw = int(u.get("cache_creation_input_tokens") or 0)
    i = int(u.get("input_tokens") or 0) + cr + cw
    o = int(u.get("output_tokens") or 0)
    usage = {"input_tokens": i, "output_tokens": o, "cache_read_tokens": cr,
             "cache_write_tokens": cw, "total_tokens": i + o}
    cost = out.get("total_cost_usd")
    thinking = (u.get("output_tokens_details") or {}).get("thinking_tokens")
    return (usage, float(cost) if isinstance(cost, (int, float)) else None,
            int(thinking) if isinstance(thinking, (int, float)) else 0)


def _int_or_none(v: Any) -> int | None:
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _observe_claude_stream_event(payload: dict[str, Any], timer: _ThinkingTimer, now: float) -> None:
    """Read Claude Code's partial Anthropic stream events for thinking phases."""
    if payload.get("type") != "stream_event":
        return
    event = payload.get("event") or {}
    kind = event.get("type")
    if kind == "content_block_start":
        block_type = (event.get("content_block") or {}).get("type")
        if block_type in ("thinking", "redacted_thinking"):
            timer.reasoning(now)
        elif block_type == "text":
            timer.answer(now)
    elif kind == "content_block_delta":
        delta_type = (event.get("delta") or {}).get("type")
        if delta_type in ("thinking_delta", "signature_delta"):
            timer.reasoning(now)
        elif delta_type == "text_delta":
            timer.answer(now)


def _run_claude_code_stream(cmd: list[str], prompt: str, *, timeout_s: int,
                            cwd: str, env: dict[str, str]):
    """Run stream-json with partial messages and timestamp events as they arrive.

    Reader threads keep stdout/stderr draining while the main thread applies an
    inactivity timeout, reset by each stdout event. The returned CompletedProcess
    preserves the old gateway's error-handling shape; the separate dict is its
    final `result` event.
    """
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=cwd, env=env, bufsize=1,
    )
    events: queue.Queue[tuple[str, str | None]] = queue.Queue()
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def reader(stream, name: str, dest: list[str]) -> None:
        try:
            for line in stream:
                dest.append(line)
                events.put((name, line))
        finally:
            events.put((name, None))

    threads = [
        threading.Thread(target=reader, args=(proc.stdout, "stdout", stdout_lines), daemon=True),
        threading.Thread(target=reader, args=(proc.stderr, "stderr", stderr_lines), daemon=True),
    ]
    for thread in threads:
        thread.start()

    timer = _ThinkingTimer()
    result: dict[str, Any] | None = None
    deadline = time.time() + timeout_s
    try:
        assert proc.stdin is not None
        proc.stdin.write(prompt)
        proc.stdin.close()
        open_streams = 2
        while open_streams:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(cmd, timeout_s)
            try:
                name, line = events.get(timeout=remaining)
            except queue.Empty:
                raise subprocess.TimeoutExpired(cmd, timeout_s) from None
            if line is None:
                open_streams -= 1
                continue
            if name != "stdout":
                continue
            # A healthy long thinking phase must not hit a whole-call deadline:
            # timeout_s is the maximum silence between stdout events, including
            # the wait for the first one.
            deadline = time.time() + timeout_s
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                _observe_claude_stream_event(payload, timer, time.monotonic())
                if payload.get("type") == "result":
                    result = payload
        remaining = max(0.001, deadline - time.time())
        returncode = proc.wait(timeout=remaining)
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    finally:
        for thread in threads:
            thread.join(timeout=1)

    thinking_time = timer.finish(time.monotonic())
    completed = subprocess.CompletedProcess(
        cmd, returncode, "".join(stdout_lines), "".join(stderr_lines))
    return result, thinking_time, completed


def _call_claude_code(
    model_slug: str,
    prompt: str,
    *,
    max_tokens: int,
    timeout_s: int,
    effort: str | None,
    max_retries: int,
    backoff_base_s: float,
    measure_thinking: bool = False,
) -> CallResult:
    """One model call through `claude -p` (prompt on stdin, lean flags, a fresh
    empty working dir, credential env vars stripped). Never raises.

    `measure_thinking` opts into stream-json/partial-message instrumentation;
    the default JSON transport remains unchanged for existing evaluations.
    """
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0,
             "cache_write_tokens": 0, "total_tokens": 0}
    cmd = ["claude", "-p", "--model", model_slug, *CLAUDE_CODE_FLAGS,
           "--system-prompt", SYSTEM_PROMPT]
    if measure_thinking:
        cmd[cmd.index("--output-format") + 1] = "stream-json"
        cmd += ["--verbose", "--include-partial-messages"]
    if effort:
        cmd += ["--effort", effort]
    env = _claude_code_env(max_tokens)

    last_err: str | None = None
    attempt = 0
    for attempt in range(1, max_retries + 1):
        retryable = False
        thinking_time: float | None = None
        t0 = time.time()
        try:
            with tempfile.TemporaryDirectory(prefix="gate1-cc-") as cwd:
                if measure_thinking:
                    out, thinking_time, proc = _run_claude_code_stream(
                        cmd, prompt, timeout_s=timeout_s, cwd=cwd, env=env)
                else:
                    proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                          timeout=timeout_s, cwd=cwd, env=env)
                    out = None
            latency = time.time() - t0
        except subprocess.TimeoutExpired:
            last_err, retryable = f"claude -p timed out after {timeout_s}s", True
        except FileNotFoundError:
            return CallResult(usage, attempt, 0.0, "", None,
                              "Claude Code CLI `claude` not found on PATH")
        except OSError as exc:
            last_err = f"claude -p failed to start: {exc}"
        else:
            try:
                if not measure_thinking:
                    out = json.loads(proc.stdout)
                if not isinstance(out, dict):
                    raise ValueError("not a JSON object")
            except ValueError:
                tail = (proc.stderr or proc.stdout or "").strip()[-300:]
                last_err = (f"claude -p exit {proc.returncode}, non-JSON output: {tail!r}"
                            if proc.stdout.strip() else
                            f"claude -p exit {proc.returncode} with no output: {tail!r}")
            else:
                result = out.get("result") if isinstance(out.get("result"), str) else ""
                turns = _int_or_none(out.get("num_turns"))
                api_ms = _int_or_none(out.get("duration_api_ms"))
                if out.get("is_error") and out.get("api_error") == "max_output_tokens":
                    # Claude Code continued the answer up to 4 times and it never
                    # finished: cut off at the output limit, the model's own
                    # behaviour (a FAIL like any finish_reason=length), not an
                    # infra error, and not retried (it would hit the limit again).
                    usage, estimate, thinking = _cc_usage(out)
                    return CallResult(
                        usage, attempt, latency, "", "length",
                        f"empty completion (finish_reason=length): the answer exceeded the "
                        f"output limit ({max_tokens} tokens) over {turns or '?'} requests",
                        provider="claude-code", cost_estimate_usd=estimate,
                        reasoning_tokens=thinking, num_turns=turns, duration_api_ms=api_ms,
                        thinking_time_s=thinking_time)
                if out.get("is_error"):
                    status = out.get("api_error_status")
                    msg = f"claude -p error (api_error_status={status}): {result[:300]}"
                    if _CC_LIMIT_RE.search(result):
                        return CallResult(usage, attempt, latency, "", None, msg,
                                          provider="claude-code",
                                          stop_run=f"Claude Code subscription usage limit "
                                                   f"reached: {result[:300]}")
                    last_err = msg
                    retryable = status in _CC_RETRY_STATUS or "overloaded" in result.lower()
                else:
                    usage, estimate, thinking = _cc_usage(out)
                    stop = out.get("stop_reason")
                    finish_reason = {"end_turn": "stop", "max_tokens": "length"}.get(stop, stop)
                    ok_model, served = _served_models_match(out.get("modelUsage"), model_slug)
                    text = result if result.strip() else ""
                    if not ok_model:
                        # never score a different model's answer
                        text, err = "", f"served by {served}, asked for {model_slug}"
                    elif turns is not None and turns > 1:
                        # With no tools, more than one request means the answer hit
                        # the output limit and Claude Code continued it; `result` is
                        # only the last request's text, a fragment. Cut off at the
                        # limit, like finish_reason=length on the other routes.
                        text, finish_reason = "", "length"
                        err = (f"empty completion (finish_reason=length): the answer hit the "
                               f"output limit ({max_tokens} tokens) and Claude Code continued it "
                               f"over {turns} requests; only the last part is returned, so it "
                               "is not graded")
                    elif not text:
                        err = f"empty completion (finish_reason={finish_reason})"
                    else:
                        err = None
                    return CallResult(usage, attempt, latency, text, finish_reason, err,
                                      provider="claude-code", cost_estimate_usd=estimate,
                                      reasoning_tokens=thinking, num_turns=turns,
                                      duration_api_ms=api_ms, thinking_time_s=thinking_time)
        if not retryable or attempt >= max_retries:
            break
        time.sleep(min(backoff_base_s * (2 ** (attempt - 1)), 60.0))

    return CallResult(usage, attempt, 0.0, "", None, last_err)


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
    provider_prefs: dict[str, Any] | None = None,
    reasoning: dict[str, Any] | None = None,
    api: ApiRef | None = None,
    session: str | None = None,
    extra_params: dict[str, Any] | None = None,
    measure_thinking: bool = False,
) -> CallResult:
    """Call one model and return a CallResult.

    Two routes, picked by `api`:
    * `api=None` (default) — OpenRouter. `provider_prefs` (OpenRouter provider
      routing, e.g. {"order": ["Amazon Bedrock"], "allow_fallbacks": false}) is
      sent on every request so both models of a pair run on the same provider.
      Every request also asks OpenRouter to report its billed cost (usage.cost).
      `reasoning` (OpenRouter's reasoning preferences, e.g. {"max_tokens":
      16000}) caps hidden thinking, which otherwise shares max_tokens with the
      answer.
    * `api=<ApiRef>` — a non-OpenRouter gateway from models.yaml `apis:` (e.g.
      OpenCode Go). `family: chat` speaks OpenAI chat completions, `family:
      responses` speaks the OpenAI Responses API (Go serves GPT Luna / Grok /
      Muse Spark only at `/v1/responses`), `family: messages` speaks the
      Anthropic messages API (Go's MiniMax / Qwen3.x at `/v1/messages`).
      `family: claude-code` calls the Claude Code CLI (`claude -p`) on the
      personal subscription (see _call_claude_code); only its `effort` from
      `reasoning` is used.
      The gateway itself is already a single
      provider, so no provider pinning, usage-cost request or reasoning
      preferences are sent (they are OpenRouter-specific extensions). Go asks
      clients to identify themselves and send a stable session id, which the
      extra headers do (see https://opencode.ai/v2/docs/console/go).

    Retries on 429 / 5xx / transient errors with exponential backoff. Never
    raises for a provider error — returns an `error` string instead so the run
    loop records a failed run and continues.
    """
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0,
             "cache_write_tokens": 0, "total_tokens": 0}
    if dry_run:
        # Build the payload shape without hitting the network.
        return CallResult(usage, 0, 0.0, "", None, None)

    if api is not None and api.family == "claude-code":
        # The CLI, not litellm: no key, no OpenRouter extensions, no temperature.
        return _call_claude_code(
            model_slug, prompt, max_tokens=max_tokens, timeout_s=timeout_s,
            effort=_claude_code_effort(reasoning), max_retries=max_retries,
            backoff_base_s=backoff_base_s, measure_thinking=measure_thinking)

    try:
        import litellm  # lazy import
    except Exception as exc:  # pragma: no cover
        return CallResult(usage, 0, 0.0, "", None, f"litellm import failed: {exc}")

    # Some frontier models are reasoning-only and accept a fixed temperature
    # (e.g. Opus 4.8/5.5 only accept temperature=1). Dropping unsupported params
    # lets litellm fall back to each model's default rather than hard-failing.
    litellm.drop_params = True

    served_by: str | None = None     # recorded as RunResult.provider
    if api is not None:
        if api.family not in ("chat", "responses", "messages"):
            return CallResult(usage, 0, 0.0, "", None,
                              f"api {api.id!r} has unsupported family {api.family!r} "
                              "(wired up: 'chat', 'responses', 'messages')")
        key = api.key()
        if not key:
            return CallResult(usage, 0, 0.0, "", None,
                              f"{api.api_key_env} not set (check .env)")
        # chat/responses speak OpenAI dialects (litellm `openai/`); messages is
        # the Anthropic messages API (litellm `anthropic/` — it posts to
        # {api_base}/messages and normalizes the reply back to choices/message).
        prefix = "anthropic/" if api.family == "messages" else "openai/"
        model_str = model_slug if model_slug.startswith(prefix) else f"{prefix}{model_slug}"
        base = api.base_url
        if api.family == "messages" and base.rstrip("/").endswith("/v1"):
            # The Anthropic SDK appends /v1/messages to base_url itself, so the
            # gateway's .../v1 must be trimmed or the call 404s on /v1/v1/messages.
            base = base.rstrip("/")[: -len("/v1")]
        call_kwargs: dict[str, Any] = {
            "api_base": base,
            "api_key": key,
            "extra_headers": {
                "User-Agent": "ai-model-lifecycle-gate1/1.0",
                "x-opencode-session": session or "",
            },
        }
        served_by = api.id
    else:
        token = get_openrouter_token()
        if not token:
            return CallResult(usage, 0, 0.0, "", None, "OPENROUTER_TOKEN not set (check .env)")
        # OpenRouter models must use the `openrouter/` prefix so litellm routes
        # through OpenRouter (honoring api_key) instead of the native Anthropic
        # provider path (which ignores api_key and looks for ANTHROPIC_API_KEY).
        model_str = model_slug if model_slug.startswith("openrouter/") else f"openrouter/{model_slug}"
        extra_body: dict[str, Any] = {"usage": {"include": True}}
        if provider_prefs:
            extra_body["provider"] = provider_prefs
        if reasoning:
            extra_body["reasoning"] = reasoning
        call_kwargs = {"api_key": token, "extra_body": extra_body}

    # Per-model extra params from models.yaml (e.g. reasoning_effort for
    # thinking-only models like GLM-5.x on Go). litellm.drop_params=True drops
    # them where a provider rejects them.
    call_kwargs.update(extra_params or {})

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    # Go serves some models only over the OpenAI Responses API (GPT Luna, Grok,
    # Muse Spark); those use max_output_tokens (thinking included), not
    # max_tokens, and return their answer in output items, not choices.
    use_responses_api = api is not None and api.family == "responses"

    last_err: str | None = None
    for attempt in range(1, max_retries + 1):
        thinking_time: float | None = None
        t0 = time.time()
        try:
            # max_retries=0 everywhere: litellm's underlying OpenAI client
            # retries timeouts twice on its own (3 hidden attempts per call),
            # multiplying a dead call's wall time; this loop is the only retry
            # authority.
            if use_responses_api:
                resp = litellm.responses(
                    model=model_str,
                    input=messages,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    timeout=timeout_s,
                    max_retries=0,
                    **call_kwargs,
                )
            elif api is not None:
                # Keyed gateways stream. Go's non-streaming path can accept a
                # request and never send a byte (first seen 2026-10-26: Kimi K3
                # on r1b — ~73k-token prompt + max_tokens=128000 stalled
                # forever, while the same request streamed its first chunk in
                # under 2 s). Streaming sidesteps that buffering path and makes
                # timeout_s a between-chunks timeout: a healthy long call
                # survives, a stalled one fails at timeout_s.
                chunks = []
                timer = _ThinkingTimer()
                for chunk in litellm.completion(
                        model=model_str,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=timeout_s,
                        max_retries=0,
                        stream=True,
                        stream_options={"include_usage": True},
                        **call_kwargs):
                    if measure_thinking:
                        _observe_stream_chunk(chunk, timer, time.monotonic())
                    chunks.append(chunk)
                if measure_thinking:
                    thinking_time = timer.finish(time.monotonic())
                resp = litellm.stream_chunk_builder(chunks, messages=messages)
                if resp is None:
                    return CallResult(usage, attempt, time.time() - t0, "", None,
                                      "empty stream (no chunks returned)",
                                      provider=served_by)
            else:
                # OpenRouter billing (usage.cost) rides on the non-streaming
                # response, so this route keeps its transport.
                resp = litellm.completion(
                    model=model_str,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout_s,
                    max_retries=0,
                    **call_kwargs,
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
            if use_responses_api:
                text = _responses_text(resp)
                finish_reason = _responses_finish_reason(resp)
            else:
                msg = resp.choices[0].message
                # Only `content` is the answer. Hidden thinking (`reasoning` /
                # `reasoning_content`) is never graded, same as the Responses
                # route: a model that spends its whole budget thinking has no
                # answer and is recorded as an empty completion (a FAIL in
                # report.py). Grading the thinking scored Qwen3.8 Flash on 120k+
                # characters of it (tests/test_reasoning_not_graded.py).
                text = msg.content or ""
                if not text.strip():
                    text = ""
                finish_reason = getattr(resp.choices[0], "finish_reason", None)
            return CallResult(
                usage, attempt, latency, text, finish_reason,
                None if text else f"empty completion (finish_reason={finish_reason})",
                provider=served_by or getattr(resp, "provider", None),
                billed_cost_usd=_extract_billed_cost(resp),
                reasoning_tokens=_extract_reasoning_tokens(resp),
                thinking_time_s=thinking_time,
            )

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

    return CallResult(usage, max_retries, 0.0, "", None, last_err)


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
    run_id: str | None = None,
) -> RunResult:
    run_id = run_id or new_run_id()
    prompt = build_prompt(case_id)
    api = cfg.api_for(model)
    # OpenRouter provider pinning / reasoning prefs only apply to OpenRouter
    # models; a gateway like OpenCode Go is already one provider. The Claude
    # Code CLI takes the suite's thinking effort as `--effort`.
    provider_prefs = cfg.provider_for(pair_id) if api is None else None
    reasoning_prefs = cfg.reasoning if api is None else None
    if api is not None and api.family == "claude-code":
        effort = _claude_code_effort(cfg.reasoning)
        reasoning_prefs = {"effort": effort} if effort else None
    elif api is not None:
        effort = (model.params or {}).get("reasoning_effort")
        reasoning_prefs = {"effort": effort} if effort else None
    call = call_model(
        model.id,
        prompt,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens_for(model.id),
        timeout_s=cfg.timeout_s_for(pair_id),
        max_retries=cfg.max_retries,
        backoff_base_s=cfg.backoff_base_s,
        dry_run=dry_run,
        provider_prefs=provider_prefs,
        reasoning=reasoning_prefs,
        api=api,
        session=run_id,
        extra_params=model.params,
        measure_thinking=cfg.thinking_time,
    )
    if call.stop_run:
        raise UsageLimitReached(call.stop_run)
    usage, attempts, latency, text, finish_reason, err = call[:6]
    result = RunResult(
        pair_id=pair_id,
        case_id=case_id,
        model_slug=model.id,
        model_name=model.name,
        role=role,
        suite=cfg.suite,
        rep=rep,
        run_id=run_id,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens_for(model.id),
        latency_s=round(latency, 4),
        thinking_time_s=(round(call.thinking_time_s, 4)
                         if call.thinking_time_s is not None else None),
        attempts=attempts,
        prompt=prompt,
        output_text=text,
        finish_reason=finish_reason,
        ok=err is None,
        error=err,
        created_at=time.time(),
        provider_requested=provider_prefs,
        reasoning_requested=reasoning_prefs,
        reasoning_tokens=call.reasoning_tokens,
        provider=call.provider,
        billed_cost_usd=call.billed_cost_usd,
        cost_estimate_usd=call.cost_estimate_usd,
        num_turns=call.num_turns,
        duration_api_ms=call.duration_api_ms,
        **usage,
    )
    if not dry_run:  # a dry run's empty output must never become "the latest run"
        save_run(asdict(result), run_path(pair_id, model.id, case_id, rep=rep, run_id=run_id))
    return result

def run_pair(
    cfg: Config,
    pair_id: str,
    *,
    case: str | None = None,
    dry_run: bool = False,
    repeats: int = 1,
    run_id: str | None = None,
) -> list[RunResult]:
    """Run every (case, model, repeat) of a pair. All files share ONE run id,
    taken once at the start, so a run that crosses midnight UTC stays whole.

    A Claude Code pair is checked once, before any call, to be logged in with
    the claude.ai subscription (raises ClaudeCodeNotReady). Hitting the
    subscription usage limit raises UsageLimitReached; runs already written
    are kept.
    """
    pair = cfg.get_pair(pair_id)
    run_id = run_id or new_run_id()
    if not dry_run and any((api := cfg.api_for(m)) is not None and api.family == "claude-code"
                           for m in (pair.current, pair.target)):
        claude_code_preflight()
    results: list[RunResult] = []
    for case_id in cfg.selected_cases(case):
        for model, role in ((pair.current, "current"), (pair.target, "target")):
            for rep in range(repeats):
                res = run_case(cfg, pair_id, case_id, model, role, dry_run=dry_run, rep=rep,
                               run_id=run_id)
                status = "OK" if res.ok else f"FAIL ({res.error})"
                tag = f" [rep {rep+1}/{repeats}]" if repeats > 1 else ""
                print(f"[{pair_id}] {role:7s} {model.name:20s} {case_id:26s} "
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
    ap.add_argument("--suite", default=None,
                    help="case suite from models.yaml: sanity (default, the top-level `cases:`) "
                         "or a name under `suites:` such as real")
    ap.add_argument("--case", help="run a single case id (default: all cases of the suite)")
    ap.add_argument("--repeats", type=int, default=1, metavar="N",
                    help="run each (model, case) N times to capture latency/cost variance")
    ap.add_argument("--dry-run", action="store_true",
                    help="build prompts only, no network calls (CI-safe)")
    args = ap.parse_args(argv)

    load_env()
    cfg = load_config(suite=args.suite)

    if args.all_pairs:
        pair_ids = [p.id for p in cfg.pairs]
    elif args.pair:
        pair_ids = [args.pair]
    else:
        ap.error("pass --pair <id> or --all-pairs")

    run_id = new_run_id()
    print(f"run id: {run_id}  suite: {cfg.suite}", file=sys.stderr)
    for pid in pair_ids:
        try:
            run_pair(cfg, pid, case=args.case, dry_run=args.dry_run, repeats=args.repeats,
                     run_id=run_id)
        except ClaudeCodeNotReady as exc:
            print(f"[{pid}] not run: {exc}", file=sys.stderr)
            return 2
        except UsageLimitReached as exc:
            print(f"[{pid}] stopped: {exc}. Runs written so far are kept (run id {run_id}); "
                  "this is a partial run, not a scorecard. Re-run after the limit resets.",
                  file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
