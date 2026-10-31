"""tests/test_docs_mode.py — docs-assisted runs (runner.py --docs context7).

Single-shot runs give the model no tools. A docs-assisted run hands Claude
Code one MCP server — Context7, up-to-date library documentation — through
`--mcp-config` (with `--strict-mcp-config` still set, so nothing else the user
has configured leaks in) and allows only its two tools. Every lookup is
recorded. Docs runs are a variant like effort sweeps: never the scorecard, never
the leaderboard. Claude Code only for now; other routes are refused.

All offline: the CLI process is faked.
"""

from __future__ import annotations

import io
import json
import subprocess

import pytest

import common
import leaderboard
import report
import runner
from common import load_config

PAIR = "opus-5.5-cc-vs-kimi-k3"
GO_PAIR = "glm-5.2-vs-5.3"
CASE = "r3_oracle_to_postgres"
ANSWER = "### FILE: x.sql\n```sql\nSELECT 1;\n```\n"


def _result(**over):
    out = {"type": "result", "subtype": "success", "is_error": False, "api_error_status": None,
           "result": ANSWER, "stop_reason": "end_turn", "duration_ms": 9000,
           "duration_api_ms": 8000, "num_turns": 3, "session_id": "s", "total_cost_usd": 0.05,
           "usage": {"input_tokens": 600, "cache_creation_input_tokens": 0,
                     "cache_read_input_tokens": 0, "output_tokens": 50},
           "modelUsage": {"claude-opus-5-5": {"inputTokens": 600, "outputTokens": 50}}}
    out.update(over)
    return out


def _tool_use(name, inp):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "t", "name": name, "input": inp}]}}


LOOKUPS = [
    _tool_use("mcp__context7__resolve-library-id",
              {"libraryName": "problem-spring-web", "query": "Spring Boot 3"}),
    {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ids..."}]}},
    _tool_use("mcp__context7__query-docs",
              {"libraryId": "/zalando/problem-spring-web", "query": "jackson module"}),
]


class _Stdin:
    def write(self, text):
        pass

    def close(self):
        pass


class _Proc:
    def __init__(self, events):
        self.stdout = io.StringIO("".join(json.dumps(e) + "\n" for e in events))
        self.stderr = io.StringIO("")
        self.stdin = _Stdin()

    def wait(self, timeout=None):
        return 0

    def kill(self):
        pass


@pytest.fixture
def cli(monkeypatch, tmp_path):
    """Fake `claude -p`: records each command and the MCP config file it named."""
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(runner.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    monkeypatch.delenv("CONTEXT7_API_KEY", raising=False)
    seen = {"cmds": [], "configs": [], "events": [*LOOKUPS, _result()]}

    def popen(cmd, **kw):
        seen["cmds"].append(list(cmd))
        if "--mcp-config" in cmd:
            path = cmd[cmd.index("--mcp-config") + 1]
            seen["configs"].append(json.loads(open(path).read()))
        return _Proc(seen["events"])

    def run(cmd, **kw):
        seen["cmds"].append(list(cmd))
        if cmd[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(cmd, 0, json.dumps(
                {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty"}), "")
        return subprocess.CompletedProcess(cmd, 0, json.dumps(_result(num_turns=1)), "")

    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    monkeypatch.setattr(runner.subprocess, "run", run)
    return seen


def _call(docs="context7", **kw):
    return runner._call_claude_code("claude-opus-5-5", "the prompt", max_tokens=32000,
                                    timeout_s=60, effort=None, max_retries=2,
                                    backoff_base_s=0.0, docs=docs, **kw)


# --------------------------------------------------------------------------- #
# the Claude Code call                                                         #
# --------------------------------------------------------------------------- #
def test_docs_mode_gives_claude_code_context7_and_nothing_else(cli):
    res = _call()
    cmd = cli["cmds"][0]
    assert "--strict-mcp-config" in cmd                         # nothing else leaks in
    assert cmd[cmd.index("--tools") + 1] == ""                  # no built-in tools
    allowed = cmd[cmd.index("--allowedTools") + 1]
    assert set(allowed.split(",")) == {"mcp__context7__resolve-library-id",
                                       "mcp__context7__query-docs"}
    assert cli["configs"][0] == {"mcpServers": {"context7": {
        "type": "http", "url": "https://mcp.context7.com/mcp"}}}
    assert res.error is None and res.text == ANSWER


def test_the_api_key_goes_in_the_config_file_never_on_the_command_line(cli, monkeypatch):
    monkeypatch.setenv("CONTEXT7_API_KEY", "ctx7sk-not-a-real-key")
    _call()
    assert cli["configs"][0]["mcpServers"]["context7"]["headers"] == {
        "Authorization": "Bearer ctx7sk-not-a-real-key"}
    assert not any("ctx7sk-not-a-real-key" in arg for arg in cli["cmds"][0])


def test_tool_turns_are_not_mistaken_for_a_continued_answer(cli):
    """Without tools, num_turns > 1 means Claude Code continued an answer that
    hit the output limit; with docs lookups it is just the tool turns."""
    res = _call()
    assert res.error is None and res.finish_reason == "stop" and res.num_turns == 3


def test_every_lookup_is_recorded(cli):
    res = _call()
    assert res.docs_calls == [
        {"tool": "resolve-library-id",
         "input": {"libraryName": "problem-spring-web", "query": "Spring Boot 3"}},
        {"tool": "query-docs",
         "input": {"libraryId": "/zalando/problem-spring-web", "query": "jackson module"}},
    ]


def test_without_docs_the_single_shot_command_is_unchanged(cli):
    res = _call(docs=None)
    cmd = cli["cmds"][0]
    assert "--mcp-config" not in cmd and "--allowedTools" not in cmd
    assert cmd[cmd.index("--output-format") + 1] == "json"
    assert res.docs_calls is None


def test_waiting_for_a_tool_is_not_thinking_time():
    timer = runner._ThinkingTimer()
    ev = lambda kind, block: {"type": "stream_event", "event": {                # noqa: E731
        "type": "content_block_start", "content_block": {"type": block}}}
    runner._observe_claude_stream_event(ev("start", "thinking"), timer, 1.0)
    runner._observe_claude_stream_event(ev("start", "tool_use"), timer, 3.0)  # 30 s lookup
    runner._observe_claude_stream_event(ev("start", "text"), timer, 33.0)
    thinking, execution = timer.finish(35.0)
    assert thinking == pytest.approx(2.0) and execution == pytest.approx(2.0)


# --------------------------------------------------------------------------- #
# runs                                                                         #
# --------------------------------------------------------------------------- #
def test_run_case_records_the_docs_tool_and_lookups(cli, tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "claude_code_preflight", lambda: None)
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    res = runner.run_case(cfg, PAIR, CASE, pair.current, "current",
                          run_id="20261031T000000Z", docs="context7")
    assert res.docs_tool == "context7" and len(res.docs_calls) == 2
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["docs_tool"] == "context7" and len(saved["docs_calls"]) == 2


@pytest.mark.parametrize("pair_id, role", [(PAIR, "target"), (GO_PAIR, None),
                                           ("opus-4.8-vs-5.5", None)])
def test_other_routes_are_refused_before_any_call(cli, pair_id, role):
    cfg = load_config()
    with pytest.raises(ValueError, match="Claude Code"):
        runner.run_pair(cfg, pair_id, case=CASE, role=role, docs="context7")
    assert not [c for c in cli["cmds"] if "-p" in c]


def test_main_passes_docs_through(monkeypatch):
    seen = {}
    monkeypatch.setattr(runner, "run_pair", lambda cfg, pid, **kw: seen.update(kw) or [])
    assert runner.main(["--pair", PAIR, "--role", "current", "--docs", "context7"]) == 0
    assert seen["docs"] == "context7"
    with pytest.raises(SystemExit):
        runner.main(["--pair", PAIR, "--docs", "google"])


# --------------------------------------------------------------------------- #
# reports: a docs run is a variant, never the scorecard or the leaderboard     #
# --------------------------------------------------------------------------- #
def _write_full(d, rid, *, docs=None):
    cfg = load_config()
    d.mkdir(parents=True, exist_ok=True)
    for case in cfg.cases:
        for role in ("current", "target"):
            rec = {"case_id": case, "role": role, "model_slug": f"m-{role}", "ok": True,
                   "output_text": "x", "latency_s": 1.0, "docs_tool": docs}
            (d / f"m-{role}.{case}.{rid}.json").write_text(json.dumps(rec))


def test_scorecard_and_leaderboard_skip_docs_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    _write_full(tmp_path / PAIR, "20261030T000000Z")
    _write_full(tmp_path / PAIR, "20261031T000000Z", docs="context7")
    cfg = load_config()
    assert report.pick_run(cfg, PAIR) == ("20261030T000000Z", [])
    picked = leaderboard.selected_runs(cfg, PAIR)
    assert {rid for rid, _ in picked.values()} == {"20261030T000000Z"}


def test_a_docs_run_says_so_in_its_scorecard_header():
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    runs = [{"case_id": CASE, "role": role, "model_slug": m.id, "model_name": m.name,
             "ok": True, "output_text": "x", "latency_s": 1.0, "docs_tool": "context7",
             "docs_calls": [{"tool": "query-docs", "input": {}}] * (2 if role == "current" else 0)}
            for role, m in (("current", pair.current), ("target", pair.target))]
    md = report.render_pair(cfg, PAIR, report.aggregate(runs, score=False), runs, score=False)
    assert "Docs tool: context7" in md and "2 lookups" in md


# --------------------------------------------------------------------------- #
# the model is told the docs tools exist                                       #
# --------------------------------------------------------------------------- #
def test_docs_mode_tells_the_model_the_tools_exist(cli):
    """Live check 2026-10-31: with the tools available but unmentioned, Opus
    made zero lookups on r1b. Context7 is meant to be invoked ('use context7'
    or a standing rule), so docs mode adds one line to the system prompt."""
    _call()
    cmd = cli["cmds"][0]
    system = cmd[cmd.index("--system-prompt") + 1]
    assert system.startswith(runner.SYSTEM_PROMPT)
    assert "context7" in system and "documentation" in system
    # A soft "use them if you are unsure" hint still drew zero lookups (the
    # model is sure — wrongly); the hint must ask for the check outright.
    assert "Before you write your answer" in system and "every library" in system


def test_single_shot_system_prompt_is_unchanged(cli):
    _call(docs=None)
    cmd = cli["cmds"][0]
    assert cmd[cmd.index("--system-prompt") + 1] == runner.SYSTEM_PROMPT
