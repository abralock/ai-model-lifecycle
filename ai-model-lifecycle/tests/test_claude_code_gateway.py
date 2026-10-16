"""tests/test_claude_code_gateway.py — the Claude Code gateway (family: claude-code).

Models with `api: claude-code` are called through the Claude Code CLI
(`claude -p`) on the personal claude.ai subscription instead of OpenRouter
(plan: docs/CLAUDE_CODE_GATEWAY.md). The call must:
  * use the lean flags (Claude Code's own instructions otherwise add 5-10k
    uneven input tokens per call) and send the prompt on stdin;
  * never be able to bill an API key (credential env vars stripped, and a
    pre-flight check that the CLI is logged in with claude.ai);
  * record Claude Code's cost as an estimate, never as a bill;
  * refuse to score another model's answer, and stop the whole run (no retry)
    when the subscription usage limit is hit.

All offline: subprocess.run is replaced by a fake, the real CLI is never called.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

import common
import mlflow_export
import report
import runner
from common import ApiRef, load_config

PAIR = "haiku-4.5-vs-5.5-cc"
CASE = "r3_oracle_to_postgres"
ANSWER = "### FILE: x.sql\n```sql\nSELECT 1;\n```\n"

LEAN_FLAGS = [
    "--output-format", "json",
    "--tools", "",
    "--setting-sources", "",
    "--strict-mcp-config",
    "--disable-slash-commands",
    "--exclude-dynamic-system-prompt-sections",
    "--no-session-persistence",
]

AUTH_OK = {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty"}


def _success(model: str = "claude-haiku-5-5", **over: Any) -> dict[str, Any]:
    """A `claude -p --output-format json` success object (shape verified 2026-10-15)."""
    out = {
        "type": "result", "subtype": "success",
        "is_error": False, "api_error_status": None,
        "result": ANSWER, "stop_reason": "end_turn",
        "duration_ms": 4321, "duration_api_ms": 4000, "num_turns": 1,
        "session_id": "s-1", "total_cost_usd": 0.0123,
        "usage": {"input_tokens": 600, "cache_creation_input_tokens": 300,
                  "cache_read_input_tokens": 100, "output_tokens": 50},
        "modelUsage": {model: {"inputTokens": 600, "outputTokens": 50}},
    }
    out.update(over)
    return out


def _error(result: str, status: int | None = None) -> dict[str, Any]:
    return _success(is_error=True, result=result, api_error_status=status,
                    stop_reason=None, total_cost_usd=0.0, modelUsage={},
                    usage={"input_tokens": 0, "output_tokens": 0})


class FakeClaude:
    """Stands in for subprocess.run. `replies` is a list consumed one per
    `claude -p` call: a dict (JSON stdout, exit 0), a (stdout, returncode)
    tuple, or an exception instance to raise. `claude auth status` answers
    with `auth` (a dict) on every call."""

    def __init__(self, replies: list[Any], auth: dict[str, Any] | None = None):
        self.replies = list(replies)
        self.auth = AUTH_OK if auth is None else auth
        self.calls: list[dict[str, Any]] = []

    @property
    def model_calls(self) -> list[dict[str, Any]]:
        return [c for c in self.calls if "-p" in c["cmd"]]

    def __call__(self, cmd, **kw):
        self.calls.append({"cmd": list(cmd), **kw})
        if cmd[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(cmd, 0, json.dumps(self.auth), "")
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        if isinstance(reply, tuple):
            stdout, code = reply
            return subprocess.CompletedProcess(cmd, code, stdout, "boom on stderr")
        return subprocess.CompletedProcess(cmd, 0, json.dumps(reply), "")


@pytest.fixture
def claude(monkeypatch, tmp_path):
    """Install a FakeClaude (replies set by the test) and isolate runs/."""
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(runner.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    fake = FakeClaude([])
    monkeypatch.setattr(runner.subprocess, "run", fake)
    return fake


def _call(prompt="the prompt", *, effort=None, max_retries=3, model="claude-haiku-5-5"):
    return runner._call_claude_code(model, prompt, max_tokens=32000, timeout_s=60,
                                    effort=effort, max_retries=max_retries, backoff_base_s=0.0)


# --------------------------------------------------------------------------- #
# 1. config                                                                    #
# --------------------------------------------------------------------------- #
def test_apiref_needs_no_base_url():
    api = ApiRef(id="claude-code", family="claude-code")
    assert api.base_url == "" and api.key() is None


def test_repo_cc_pairs_resolve_to_claude_code():
    cfg = load_config()
    cc = [p for p in cfg.pairs if p.id.endswith("-cc")]
    assert {p.id for p in cc} == {"opus-4.8-vs-5.5-cc", "sonnet-5-vs-5.5-cc",
                                  "sonnet-4.6-vs-5.5-cc", "haiku-4.5-vs-5.5-cc"}
    for pair in cc:
        for m in (pair.current, pair.target):
            api = cfg.api_for(m)
            assert api is not None and api.id == "claude-code" and api.family == "claude-code"
            assert not api.base_url and not api.api_key_env       # the CLI's own login only
            assert m.id.startswith("claude-") and "/" not in m.id and "." not in m.id
            assert m.name.endswith("(CC)")


# --------------------------------------------------------------------------- #
# 2. the command                                                               #
# --------------------------------------------------------------------------- #
def test_command_has_lean_flags_and_prompt_on_stdin(claude):
    claude.replies = [_success()]
    res = _call("PROMPT-TEXT")
    assert res.error is None

    call = claude.model_calls[0]
    cmd = call["cmd"]
    assert cmd[:2] == ["claude", "-p"]
    assert cmd[cmd.index("--model") + 1] == "claude-haiku-5-5"
    for flag in LEAN_FLAGS:
        assert flag in cmd
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--setting-sources") + 1] == ""
    assert cmd[cmd.index("--output-format") + 1] == "json"
    assert cmd[cmd.index("--system-prompt") + 1] == runner.SYSTEM_PROMPT
    assert "--effort" not in cmd
    # the prompt goes on stdin (real-suite prompts are 50k-110k tokens), not argv
    assert call["input"] == "PROMPT-TEXT"
    assert "PROMPT-TEXT" not in cmd
    assert call.get("shell") in (None, False)
    assert call["timeout"] == 60
    # a fresh empty working dir: no project CLAUDE.md, settings or files leak in
    assert call["cwd"] and call["cwd"] != str(common.REPO_ROOT)


def test_output_limit_is_passed_via_env(claude):
    claude.replies = [_success()]
    _call()
    assert claude.model_calls[0]["env"]["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "32000"


# --------------------------------------------------------------------------- #
# 3. the environment can only use the subscription login                       #
# --------------------------------------------------------------------------- #
STRIPPED = [
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "ANTHROPIC_FOUNDRY_API_KEY", "ANTHROPIC_AWS_API_KEY", "AWS_BEARER_TOKEN_BEDROCK",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
]


def test_credential_env_vars_are_stripped(claude, monkeypatch):
    for var in STRIPPED:
        monkeypatch.setenv(var, "set-in-test")
    monkeypatch.setenv("HOME_TEST_MARKER", "kept")
    claude.replies = [_success()]
    _call()
    runner.claude_code_preflight()
    for call in claude.calls:                     # the model call AND the auth check
        env = call["env"]
        for var in STRIPPED:
            assert var not in env, var
        assert env["HOME_TEST_MARKER"] == "kept"  # everything else is passed through


# --------------------------------------------------------------------------- #
# 4-5. reading a success                                                       #
# --------------------------------------------------------------------------- #
def test_success_json_is_read(claude):
    claude.replies = [_success()]
    res = _call()
    assert res.error is None and res.text == ANSWER
    assert res.finish_reason == "stop"
    assert res.provider == "claude-code"
    # the prompt total includes cache tokens (same meaning as the other routes)
    assert res.usage["input_tokens"] == 600 + 300 + 100
    assert res.usage["cache_read_tokens"] == 100
    assert res.usage["cache_write_tokens"] == 300
    assert res.usage["output_tokens"] == 50
    assert res.usage["total_tokens"] == 1000 + 50
    assert res.cost_estimate_usd == pytest.approx(0.0123)
    assert res.billed_cost_usd is None            # the subscription does not bill per call
    assert res.attempts == 1


def test_run_case_records_estimate_not_bill(claude):
    claude.replies = [_success()]
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, CASE, pair.target, "target", run_id="20261016T000000Z")
    assert res.ok and res.provider == "claude-code"
    assert res.cost_estimate_usd == pytest.approx(0.0123) and res.billed_cost_usd is None
    assert res.provider_requested is None
    saved = json.loads(next(common.RUNS_DIR.rglob("*.json")).read_text())
    assert saved["cost_estimate_usd"] == pytest.approx(0.0123)
    assert saved["billed_cost_usd"] is None
    assert saved["provider"] == "claude-code"


def test_max_tokens_stop_reason_maps_to_length(claude):
    claude.replies = [_success(stop_reason="max_tokens")]
    assert _call().finish_reason == "length"


def test_empty_result_is_an_empty_completion(claude):
    claude.replies = [_success(result="   ", stop_reason="max_tokens")]
    res = _call()
    assert res.text == ""
    assert res.error == "empty completion (finish_reason=length)"
    # an empty completion is the model's own behaviour: a FAIL, not an infra error
    assert not report.is_infra_error({"ok": False, "error": res.error})


# --------------------------------------------------------------------------- #
# 6-7. errors and the model check                                              #
# --------------------------------------------------------------------------- #
def test_is_error_records_error_and_grades_nothing(claude):
    claude.replies = [_error("API Error: 400 invalid request", status=400)]
    res = _call()
    assert res.text == ""
    assert res.error and "400" in res.error and "invalid request" in res.error
    assert report.is_infra_error({"ok": False, "error": res.error})
    assert len(claude.model_calls) == 1           # a 400 is not retried


def test_other_model_served_is_an_error(claude):
    # asked for Sonnet 5, served Sonnet 5.5 (whose id starts with the asked one)
    claude.replies = [_success(model="claude-sonnet-5-5")]
    res = _call(model="claude-sonnet-5")
    assert res.text == ""
    assert "claude-sonnet-5-5" in res.error and "claude-sonnet-5" in res.error


def test_dated_model_id_is_the_same_model(claude):
    claude.replies = [_success(model="claude-haiku-4-5-20251001")]
    res = _call(model="claude-haiku-4-5")
    assert res.error is None and res.text == ANSWER


def test_transient_error_is_retried(claude):
    claude.replies = [_error("API Error: 529 Overloaded", status=529), _success()]
    res = _call()
    assert res.error is None and res.text == ANSWER and res.attempts == 2


# --------------------------------------------------------------------------- #
# 8. CLI failures never raise                                                  #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("reply, expect", [
    (("this is not json", 0), "non-JSON"),
    (("", 1), "exit"),
    (subprocess.TimeoutExpired(["claude"], 60), "timed out"),
    (FileNotFoundError("claude"), "not found"),
], ids=["non-json", "non-zero-exit", "timeout", "missing-binary"])
def test_cli_failures_become_errors(claude, reply, expect):
    claude.replies = [reply] * 5
    res = _call(max_retries=2)
    assert res.text == "" and res.error and expect in res.error
    assert report.is_infra_error({"ok": False, "error": res.error})


# --------------------------------------------------------------------------- #
# 9. the subscription usage limit stops the run                                #
# --------------------------------------------------------------------------- #
LIMIT = _error("Claude AI usage limit reached|1760620800", status=429)


def test_usage_limit_is_not_retried(claude):
    claude.replies = [LIMIT, _success()]
    res = _call(max_retries=5)
    assert len(claude.model_calls) == 1
    assert res.stop_run and "usage limit" in res.stop_run.lower()


def test_usage_limit_stops_run_and_keeps_written_runs(claude):
    claude.replies = [_success(model="claude-haiku-4-5"), LIMIT, _success()]
    cfg = load_config()
    with pytest.raises(runner.UsageLimitReached, match="usage limit"):
        runner.run_pair(cfg, PAIR, case=CASE, repeats=2, run_id="20261016T000000Z")
    assert len(claude.model_calls) == 2           # stopped at the limit, no retry, no more calls
    files = list(common.RUNS_DIR.rglob("*.json"))
    assert len(files) == 1                        # the run before the limit is kept...
    assert json.loads(files[0].read_text())["ok"] is True   # ...and the limit hit is not a run


def test_main_reports_usage_limit_cleanly(claude, monkeypatch, capsys):
    monkeypatch.setattr(runner, "load_env", lambda: None)
    claude.replies = [LIMIT]
    rc = runner.main(["--pair", PAIR, "--case", CASE])
    assert rc != 0
    assert "usage limit" in capsys.readouterr().err.lower()


# --------------------------------------------------------------------------- #
# 10. pre-flight                                                               #
# --------------------------------------------------------------------------- #
def test_preflight_accepts_subscription_login(claude):
    runner.claude_code_preflight()
    assert claude.calls[0]["cmd"] == ["claude", "auth", "status"]


@pytest.mark.parametrize("auth, expect", [
    ({"loggedIn": True, "authMethod": "apiKey"}, "API key"),
    ({"loggedIn": False}, "not logged in"),
], ids=["api-key", "logged-out"])
def test_preflight_refuses_non_subscription(claude, auth, expect):
    claude.auth = auth
    with pytest.raises(runner.ClaudeCodeNotReady, match=expect):
        runner.claude_code_preflight()


def test_preflight_refuses_missing_cli(claude, monkeypatch):
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    with pytest.raises(runner.ClaudeCodeNotReady, match="PATH"):
        runner.claude_code_preflight()


def test_run_pair_checks_auth_before_any_call(claude):
    claude.auth = {"loggedIn": True, "authMethod": "apiKey"}
    claude.replies = [_success()]
    with pytest.raises(runner.ClaudeCodeNotReady):
        runner.run_pair(load_config(), PAIR, case=CASE, run_id="20261016T000000Z")
    assert not claude.model_calls
    assert not list(common.RUNS_DIR.rglob("*.json"))


def test_main_reports_preflight_failure_cleanly(claude, monkeypatch, capsys):
    monkeypatch.setattr(runner, "load_env", lambda: None)
    claude.auth = {"loggedIn": True, "authMethod": "apiKey"}
    rc = runner.main(["--pair", PAIR, "--case", CASE])
    assert rc != 0 and "API key" in capsys.readouterr().err
    assert not claude.model_calls


def test_dry_run_calls_nothing(claude):
    results = runner.run_pair(load_config(), PAIR, dry_run=True, run_id="20261016T000000Z")
    assert results and all(r.ok for r in results)
    assert not claude.calls                       # no auth check, no model call
    assert not list(common.RUNS_DIR.rglob("*.json"))


def test_openrouter_pairs_skip_preflight(claude, monkeypatch):
    monkeypatch.setattr(runner, "call_model", lambda *a, **k: runner.CallResult(
        {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0,
         "cache_write_tokens": 0, "total_tokens": 2}, 1, 0.1, "out", "stop", None))
    runner.run_pair(load_config(), "haiku-4.5-vs-5.5", case=CASE, run_id="20261016T000000Z")
    assert not claude.calls


# --------------------------------------------------------------------------- #
# 12. effort                                                                   #
# --------------------------------------------------------------------------- #
def test_effort_flag_when_set(claude):
    claude.replies = [_success()]
    _call(effort="medium")
    cmd = claude.model_calls[0]["cmd"]
    assert cmd[cmd.index("--effort") + 1] == "medium"


def test_real_suite_effort_maps_to_flag():
    assert runner._claude_code_effort(load_config(suite="real").reasoning) == "medium"
    assert runner._claude_code_effort(load_config().reasoning) is None
    assert runner._claude_code_effort({"max_tokens": 16000}) is None


EFFORT_YAML = """
pairs:
  - id: h
    current: {id: claude-haiku-4-5, name: H45, api: claude-code}
    target:  {id: claude-haiku-5-5, name: H55, api: claude-code}
apis:
  claude-code:
    family: claude-code
defaults:
  reasoning: {effort: high}
cases: [r3_oracle_to_postgres]
"""


def test_run_case_sends_and_records_suite_effort(claude, tmp_path):
    (tmp_path / "models.yaml").write_text(EFFORT_YAML)
    cfg = load_config(tmp_path / "models.yaml")
    pair = cfg.get_pair("h")
    claude.replies = [_success(model="claude-haiku-4-5"), _success()]
    cur = runner.run_case(cfg, "h", CASE, pair.current, "current", run_id="20261016T000000Z")
    tgt = runner.run_case(cfg, "h", CASE, pair.target, "target", run_id="20261016T000000Z")
    for call in claude.model_calls:               # same value for both models of the pair
        assert call["cmd"][call["cmd"].index("--effort") + 1] == "high"
    # recorded, so the report's "Thinking budget sent" header is true for this route
    assert cur.reasoning_requested == tgt.reasoning_requested == {"effort": "high"}


def test_run_case_without_effort_records_none(claude):
    claude.replies = [_success()]
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, CASE, pair.target, "target", run_id="20261016T000000Z")
    assert "--effort" not in claude.model_calls[0]["cmd"]
    assert res.reasoning_requested is None


# --------------------------------------------------------------------------- #
# 11. report + MLflow cost: billed > Claude Code estimate > price table        #
# --------------------------------------------------------------------------- #
def _rec(role, slug, billed=None, estimate=None):
    return {"case_id": CASE, "role": role, "model_slug": slug, "model_name": slug,
            "ok": True, "input_tokens": 1000, "output_tokens": 500,
            "cache_read_tokens": 0, "cache_write_tokens": 0, "total_tokens": 1500,
            "latency_s": 10.0, "output_text": "", "billed_cost_usd": billed,
            "cost_estimate_usd": estimate, "provider": "claude-code", "error": None}


def test_report_uses_estimate_and_labels_it():
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [_rec("current", pair.current.id, estimate=0.5),
            _rec("current", pair.current.id, estimate=0.25),
            _rec("target", pair.target.id, estimate=0.1)]
    aggs = report.aggregate(runs, score=False)
    cur = aggs[(pair.current.id, "current")]
    assert cur.cost_usd == pytest.approx(0.75)
    assert report._cost_source(cur) == "Claude Code estimate at API prices (2/2)"
    md = report.render_pair(cfg, PAIR, aggs, runs, score=False)
    assert "Claude Code estimate at API prices" in md
    assert "pricing.py` table" not in md          # no table warning: nothing came from the table
    assert "estimate" in md.lower() and "subscription" in md.lower()


def test_cost_precedence_billed_then_estimate_then_table():
    slug = "claude-haiku-5-5"
    runs = [_rec("target", slug, billed=1.0, estimate=9.0),     # billed wins
            _rec("target", slug, estimate=0.5),                 # then the estimate
            _rec("target", slug)]                               # then the price table
    a = report.aggregate(runs, score=False)[(slug, "target")]
    table = report.cost_usd(slug, 1000, 500, 0, 0)
    assert a.cost_usd == pytest.approx(1.0 + 0.5 + table)
    assert a.billed_runs == 1 and a.estimate_runs == 1
    label = report._cost_source(a)
    assert "billed 1/3" in label and "estimate 1/3" in label and "price table" in label


def test_existing_cost_labels_unchanged():
    a = report.ModelAgg("m", "m", "target", runs=2, billed_runs=2)
    assert report._cost_source(a) == "billed by OpenRouter (2/2)"
    a = report.ModelAgg("m", "m", "target", runs=2, billed_runs=1)
    assert report._cost_source(a) == "billed 1/2, rest price table"
    a = report.ModelAgg("m", "m", "target", runs=2)
    assert report._cost_source(a) == "price table (pricing.py)"


def test_mlflow_call_cost_uses_estimate():
    slug = "claude-haiku-5-5"
    assert mlflow_export._call_cost(_rec("target", slug, billed=1.0, estimate=9.0)) == 1.0
    assert mlflow_export._call_cost(_rec("target", slug, estimate=0.5)) == 0.5
    assert mlflow_export._call_cost(_rec("target", slug)) == pytest.approx(
        report.cost_usd(slug, 1000, 500, 0, 0))


def test_mlflow_cost_source_tag():
    slug = "claude-haiku-5-5"
    assert mlflow_export._cost_source_tag([_rec("t", slug, billed=1.0)]) == "billed"
    assert mlflow_export._cost_source_tag([_rec("t", slug, estimate=0.5)]) == "claude code estimate"
    assert mlflow_export._cost_source_tag([_rec("t", slug, estimate=0.5), _rec("t", slug)]) == "price table"


def test_price_reference_hidden_when_unused_and_unpriced():
    """The -cc ids have no pricing.py row: showing the $3/$15 fallback as a
    "price reference" when every run has an estimate is misleading."""
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [_rec("current", pair.current.id, estimate=0.5),
            _rec("target", pair.target.id, estimate=0.1)]
    md = report.render_pair(cfg, PAIR, report.aggregate(runs, score=False), runs, score=False)
    assert "Price reference" not in md
    # ...but shown when a run fell back to the table (the prices it used)
    runs[1]["cost_estimate_usd"] = None
    md = report.render_pair(cfg, PAIR, report.aggregate(runs, score=False), runs, score=False)
    assert "Price reference" in md


def test_price_reference_kept_for_priced_models():
    cfg = load_config()
    pair = cfg.get_pair("haiku-4.5-vs-5.5")
    runs = [_rec("current", pair.current.id, billed=0.5), _rec("target", pair.target.id, billed=0.1)]
    md = report.render_pair(cfg, "haiku-4.5-vs-5.5", report.aggregate(runs, score=False), runs,
                            score=False)
    assert "Price reference" in md
