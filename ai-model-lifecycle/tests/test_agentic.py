"""tests/test_agentic.py — agentic runs (agentic.py).

The model works on a copy of the project in a sandbox until its /goal is met;
what it delivered is scored by the case's own scorer. All offline: docker and
the agent are faked by a process that edits the workspace and prints a
Claude Code stream.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import pytest

import agentic
import common
from common import load_config
from scorers.base import parse_deletes, parse_files

PAIR = "sonnet-5.5-cc-vs-deepseek-v4-pro"


# --------------------------------------------------------------------------- #
# the task the agent gets                                                      #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("case_id", list(agentic.CASES))
def test_task_replaces_the_output_format_with_workspace_instructions(case_id):
    task = agentic.task_prompt(case_id)
    assert "## Workspace" in task and agentic.CASES[case_id].task_note in task
    assert "### FILE:" not in task                     # no reply format: it edits files


def test_task_keeps_the_acceptance_criteria():
    task = agentic.task_prompt("r2_gwt_to_angular")
    assert "## Acceptance criteria" in task and "gwt-debug-menubar" in task


@pytest.mark.parametrize("case_id", list(agentic.CASES))
def test_every_case_has_a_goal_and_deliverables(case_id):
    spec = agentic.CASES[case_id]
    assert len(spec.goal) > 40 and spec.deliverables


def test_every_suite_case_has_an_agentic_setup():
    cases = set(load_config().cases) | set(load_config(suite="real").cases)
    assert cases <= set(agentic.CASES)


# --------------------------------------------------------------------------- #
# the workspace: inputs only, never an answer key                              #
# --------------------------------------------------------------------------- #
def test_r3_workspace_has_the_oracle_results_but_not_the_reference_solution(tmp_path):
    agentic._setup_r3(tmp_path)
    files = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()}
    assert "seed.sql" in files and "expected/output.csv" in files
    assert any(f.startswith("oracle/") for f in files)
    assert not any("golden" in f for f in files)


@pytest.mark.parametrize("setup", [agentic._setup_r1, agentic._setup_r4, agentic._setup_r5])
def test_workspaces_hold_no_hidden_tests_or_readme(setup, tmp_path):
    setup(tmp_path)
    names = [p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")]
    assert names and not any("hidden" in n or n.endswith("README.md") or "prompt.md" in n
                             for n in names)


# --------------------------------------------------------------------------- #
# harvest: delivered files -> the answer the scorer reads                      #
# --------------------------------------------------------------------------- #
def test_the_answer_holds_changed_new_and_deleted_deliverables_only(tmp_path):
    spec = agentic.AgenticCase(goal="g", deliverables=["pom.xml", "src/main/**"],
                               setup=lambda ws: None, task_note="n",
                               exclude=["src/main/webapp/**"])
    (tmp_path / "src/main/java").mkdir(parents=True)
    (tmp_path / "src/main/webapp").mkdir(parents=True)
    (tmp_path / "src/test").mkdir(parents=True)
    (tmp_path / "pom.xml").write_text("<boot2/>")
    (tmp_path / "src/main/java/Same.java").write_text("same")
    (tmp_path / "src/main/java/Gone.java").write_text("old")
    before = agentic.snapshot(tmp_path, spec)
    (tmp_path / "pom.xml").write_text("<boot3/>")
    (tmp_path / "src/main/java/Gone.java").unlink()
    (tmp_path / "src/main/java/New.java").write_text("class New {}\n")
    (tmp_path / "src/main/webapp/app.ts").write_text("frontend")        # excluded
    (tmp_path / "src/test/T.java").write_text("test")                    # not a deliverable
    answer = agentic.answer_from(before, agentic.snapshot(tmp_path, spec))
    assert parse_files(answer) == {"pom.xml": "<boot3/>\n",
                                   "src/main/java/New.java": "class New {}\n"}
    assert parse_deletes(answer) == ["src/main/java/Gone.java"]


def test_r2_collects_assets_beside_src_app():
    spec = agentic.CASES["r2_gwt_to_angular"]
    for rel in ("src/app/app.component.ts", "src/styles.css", "src/images/ic_add.png"):
        assert agentic._match(rel, spec.deliverables)
    assert not agentic._match("e2e/java/RunCucumberTest.java", spec.deliverables)
    assert not agentic._match("node_modules/x/index.js", spec.deliverables)


def test_binary_deliverables_reach_the_scorer_intact(tmp_path):
    """Live 2026-10-31: Opus copied the GWT app's PNGs into src/app/assets and
    its CSS used them; dropping binaries failed a build that passed in the
    sandbox. They now travel base64-encoded and apply_output writes them."""
    from scorers.base import apply_output
    png = bytes(range(256)) * 40                                  # not valid UTF-8
    answer = agentic.answer_from({}, {"src/app/assets/logo.png": png,
                                      "src/app/app.component.ts": b"export class A {}\n"})
    assert parse_files(answer) == {"src/app/app.component.ts": "export class A {}\n"}
    applied = apply_output(answer, tmp_path)
    assert (tmp_path / "src/app/assets/logo.png").read_bytes() == png
    assert sorted(applied.written) == ["src/app/app.component.ts", "src/app/assets/logo.png"]


def test_a_binary_block_cannot_write_outside_the_project(tmp_path):
    from scorers.base import apply_output
    answer = "### BINARY: ../escape.png\n```base64\naGk=\n```\n"
    (tmp_path / "proj").mkdir()
    apply_output(answer, tmp_path / "proj")
    assert not (tmp_path / "escape.png").exists()


def test_files_come_in_the_order_they_are_applied():
    """r3's scorer runs the files in answer order: schema before procedures."""
    order = agentic.CASES["r3_oracle_to_postgres"].deliverables
    after = {"postgres/procedures.sql": b"CREATE PROCEDURE p() ...",
             "postgres/notes.sql": b"-- extra",
             "postgres/schema.sql": b"CREATE TABLE t (x int);"}
    answer = agentic.answer_from({}, after, order)
    assert list(parse_files(answer)) == ["postgres/schema.sql", "postgres/procedures.sql",
                                         "postgres/notes.sql"]


# --------------------------------------------------------------------------- #
# the sandbox command                                                          #
# --------------------------------------------------------------------------- #
def test_the_token_goes_by_name_and_no_api_key_reaches_the_sandbox(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat-not-real")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api-not-real")
    cmd = agentic.docker_command("n", tmp_path / "ws", tmp_path / "c", "claude-sonnet-5-5",
                                 "medium", postgres=True)
    assert not any("not-real" in arg for arg in cmd)
    assert cmd[cmd.index("-e") + 1] == "CLAUDE_CODE_OAUTH_TOKEN"
    env = agentic._container_env()
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "sk-ant-oat-not-real"
    assert "ANTHROPIC_API_KEY" not in env


def test_the_goal_and_task_never_appear_on_a_command_line(tmp_path):
    """Live 2026-10-31: on r2 the agent stopped its servers with `kill` on
    every process mentioning "java" and, the task being in claude's argv,
    killed its own session. Goal and task now travel in files."""
    agentic.write_control(tmp_path / "c", "the goal mentions java", "the task mentions java")
    cmd = agentic.docker_command("n", tmp_path / "ws", tmp_path / "c", "claude-sonnet-5-5",
                                 "medium", postgres=False)
    assert not any("java" in arg for arg in cmd)
    assert (tmp_path / "c" / "prompt.txt").read_text() == "/goal the goal mentions java"
    assert "< /gate1/prompt.txt" in cmd[cmd.index("-c") + 1]
    assert cmd[cmd.index("--append-system-prompt-file") + 1] == "/gate1/system.md"


def test_the_agent_gets_no_sub_agents_and_only_the_workspace_to_write(tmp_path):
    ws, control = tmp_path / "ws", tmp_path / "c"
    cmd = agentic.docker_command("n", ws, control, "claude-sonnet-5-5", "medium", postgres=False)
    assert cmd[cmd.index("--disallowedTools") + 1] == "Agent"
    assert "--strict-mcp-config" in cmd and cmd[cmd.index("--setting-sources") + 1] == ""
    assert cmd[cmd.index("--effort") + 1] == "medium"
    mounts = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-v"]
    assert mounts[:2] == [f"{ws}:/work", f"{control}:/gate1:ro"]
    assert all(not m.startswith("/") for m in mounts[2:])          # named cache volumes


# --------------------------------------------------------------------------- #
# one attempt, with a fake agent                                               #
# --------------------------------------------------------------------------- #
def _stream(**result):
    events = [
        {"type": "system", "subtype": "init"},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "1", "name": "Bash", "input": {"command": "mvn test"}}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "2", "name": "Edit", "input": {}}]}},
        {"type": "result", "subtype": "success", "is_error": False, "num_turns": 12,
         "duration_api_ms": 50000, "total_cost_usd": 1.25, "result": "Goal achieved.",
         "usage": {"input_tokens": 100, "output_tokens": 2000,
                   "cache_read_input_tokens": 9000, "cache_creation_input_tokens": 500},
         **result},
    ]
    return "".join(json.dumps(e) + "\n" for e in events)


class _FakeAgent:
    """Stands in for `docker run ... claude -p`: edits the mounted workspace."""

    def __init__(self, cmd, edit, stream, hang=False):
        ws = Path(cmd[cmd.index("-v") + 1].split(":")[0])
        edit(ws)
        self.stdout = io.StringIO(stream)
        self.hang, self.returncode = hang, None

    def wait(self, timeout=None):
        if self.hang and self.returncode is None:
            self.returncode = 137
            raise subprocess.TimeoutExpired("docker", timeout)
        self.returncode = self.returncode if self.returncode is not None else 0
        return self.returncode


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(agentic.sources, "ensure", lambda case_id: None)
    spec = agentic.AgenticCase(
        goal="pom says boot 3", deliverables=["pom.xml"], task_note="Edit pom.xml.",
        setup=lambda ws: (ws / "pom.xml").write_text("<boot2/>"))
    monkeypatch.setitem(agentic.CASES, "r1_springboot2to3", spec)
    killed = []
    monkeypatch.setattr(agentic.subprocess, "run",
                        lambda cmd, **kw: killed.append(cmd) or subprocess.CompletedProcess(cmd, 0))
    scored = []

    def scorer(case_id, text, slug):
        scored.append(text)
        ok = "<boot3/>" in text
        return type("R", (), {"passed": ok, "reason": "ok" if ok else "still boot 2",
                              "checks": {"boot3": ok}})()

    cfg = load_config()
    return {"cfg": cfg, "model": cfg.get_pair(PAIR).current, "killed": killed,
            "scored": scored, "scorer": scorer, "tmp": tmp_path}


def _attempt(env, **kw):
    return agentic.run_attempt(env["cfg"], PAIR, "current", env["model"], "r1_springboot2to3",
                               0, "20261031T000000Z", workroot=env["tmp"] / "work",
                               scorer=env["scorer"], **kw)


def test_a_delivered_migration_is_scored_and_recorded(env, monkeypatch):
    monkeypatch.setattr(agentic.subprocess, "Popen", lambda cmd, **kw: _FakeAgent(
        cmd, lambda ws: (ws / "pom.xml").write_text("<boot3/>"), _stream()))
    res = _attempt(env)
    assert res.ok and res.passed and not res.timed_out
    assert res.num_turns == 12 and res.tool_calls == 2 and res.cost_estimate_usd == 1.25
    assert res.files_changed == 1 and "<boot3/>" in env["scored"][0]
    saved = json.loads(agentic.record_path(PAIR, "20261031T000000Z", res.model_slug,
                                           "r1_springboot2to3", 0).read_text())
    assert saved["mode"] == "agentic" and saved["passed"] is True
    assert not (env["tmp"] / "work").exists() or not any((env["tmp"] / "work").iterdir())


def test_hitting_the_time_limit_stops_the_container_and_scores_what_is_there(env, monkeypatch):
    monkeypatch.setattr(agentic.subprocess, "Popen", lambda cmd, **kw: _FakeAgent(
        cmd, lambda ws: (ws / "pom.xml").write_text("<boot3/>"), "", hang=True))
    res = _attempt(env, time_limit_s=1)
    assert res.timed_out and res.ok and res.passed            # delivered before the limit
    assert any(c[:2] == ["docker", "kill"] for c in env["killed"])


def test_a_session_that_never_started_is_an_infra_error_and_not_scored(env, monkeypatch):
    class Dead(_FakeAgent):
        def wait(self, timeout=None):
            self.returncode = 125
            return 125
    monkeypatch.setattr(agentic.subprocess, "Popen", lambda cmd, **kw: Dead(
        cmd, lambda ws: None, "docker: Error response from daemon: no such image\n"))
    res = _attempt(env)
    assert not res.ok and "did not run" in res.error and res.passed is None
    assert env["scored"] == []


def test_a_claude_code_error_is_an_infra_error_not_a_model_fail(env, monkeypatch):
    """Live check 2026-10-31: without a login the CLI still emits a result
    event (num_turns 1, is_error) — that must never be scored as a fail."""
    monkeypatch.setattr(agentic.subprocess, "Popen", lambda cmd, **kw: _FakeAgent(
        cmd, lambda ws: None, _stream(is_error=True, num_turns=1,
                                      result="Not logged in · Please run /login")))
    res = _attempt(env)
    assert not res.ok and "Not logged in" in res.error and res.passed is None


@pytest.mark.parametrize("err", [
    "claude error: You've hit your 5-hour limit",
    "claude error: Credit balance is too low",         # live 2026-10-31: a non-subscription login
])
def test_a_usage_limit_stops_the_batch(env, monkeypatch, err):
    calls = []
    monkeypatch.setattr(agentic, "run_attempt", lambda *a, **kw: calls.append(a) or agentic.AgenticResult(
        pair_id=PAIR, case_id=a[4], model_slug="m", model_name="m", role="current", rep=a[5],
        run_id=a[6], ok=False, error=err))
    monkeypatch.setattr(agentic, "render_report", lambda *a: "")
    (env["tmp"] / "runs").mkdir(exist_ok=True)
    monkeypatch.setattr(agentic, "agentic_dir", lambda p, r: env["tmp"] / "runs")
    agentic.run(env["cfg"], PAIR, repeats=3)
    assert len(calls) == 1


def test_nothing_delivered_is_a_fail_not_an_error(env, monkeypatch):
    monkeypatch.setattr(agentic.subprocess, "Popen", lambda cmd, **kw: _FakeAgent(
        cmd, lambda ws: None, _stream(result="I could not finish.")))
    res = _attempt(env)
    assert res.ok and res.passed is False and res.files_changed == 0


def test_the_report_lists_pass_time_cost_and_turns(env, monkeypatch):
    monkeypatch.setattr(agentic.subprocess, "Popen", lambda cmd, **kw: _FakeAgent(
        cmd, lambda ws: (ws / "pom.xml").write_text("<boot3/>"), _stream()))
    _attempt(env)
    recs = agentic.load_records(PAIR, "20261031T000000Z")
    md = agentic.render_report(PAIR, "20261031T000000Z", recs)
    assert "| r1_springboot2to3 |" in md and "| 1/1 |" in md and "$1.25" in md
    assert "hidden tests" in md


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def test_preflight_needs_the_token(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    with pytest.raises(agentic.NotReady, match="setup-token"):
        agentic.preflight()


def test_claude_models_run_in_claude_code_and_go_models_in_opencode():
    cfg = load_config()
    pair = cfg.get_pair(PAIR)
    assert isinstance(agentic.backend_for(cfg, pair.current), agentic.ClaudeCodeBackend)
    assert isinstance(agentic.backend_for(cfg, pair.target), agentic.OpencodeBackend)  # DeepSeek
    openrouter = cfg.get_pair("opus-4.8-vs-5.5").current
    with pytest.raises(ValueError, match="Claude Code nor the OpenCode Go"):
        agentic.backend_for(cfg, openrouter)


def test_opencode_refuses_claude_only_effort_levels_before_running_anything():
    with pytest.raises(ValueError, match="opencode takes effort low, medium, high"):
        agentic.run(load_config(), PAIR, role="target", effort="xhigh")


@pytest.mark.parametrize("arg, expected", [
    ("sanity", None), ("real", None),
    ("r3_oracle_to_postgres,r4_schema_load_optimize",
     ["r3_oracle_to_postgres", "r4_schema_load_optimize"])])
def test_case_takes_a_list_or_a_suite(env, monkeypatch, arg, expected):
    seen = []
    monkeypatch.setattr(agentic, "run_attempt", lambda *a, **kw: seen.append(a[4]) or agentic.AgenticResult(
        pair_id=PAIR, case_id=a[4], model_slug="m", model_name="m", role="current", rep=0,
        run_id=a[6], ok=True, passed=True))
    monkeypatch.setattr(agentic, "render_report", lambda *a: "")
    (env["tmp"] / "runs").mkdir(exist_ok=True)
    monkeypatch.setattr(agentic, "agentic_dir", lambda p, r: env["tmp"] / "runs")
    agentic.run(env["cfg"], PAIR, case=arg)
    if expected is None:
        expected = list(load_config(suite=None if arg == "sanity" else arg).cases)
    assert seen == expected


# --------------------------------------------------------------------------- #
# timing from the session stream (docs/METRICS_PLAN.md, agentic)               #
# --------------------------------------------------------------------------- #
def _ev(kind, at, *blocks, **extra):
    return json.dumps({"type": kind, "timestamp": f"2026-10-31T13:00:{at:06.3f}Z",
                       "message": {"content": list(blocks)}, **extra})


def test_tool_time_merges_parallel_calls_and_thinking_is_summed():
    lines = [
        _ev("assistant", 1.0, {"type": "thinking"}, thinking_duration_ms=1500),
        _ev("assistant", 2.0, {"type": "tool_use", "id": "a"}),
        _ev("assistant", 3.0, {"type": "tool_use", "id": "b"}),        # parallel with a
        _ev("user", 6.0, {"type": "tool_result", "tool_use_id": "b"}),
        _ev("user", 7.0, {"type": "tool_result", "tool_use_id": "a"}),  # a: 2..7, b: 3..6
        _ev("assistant", 10.0, {"type": "tool_use", "id": "c"}),
        _ev("user", 12.5, {"type": "tool_result", "tool_use_id": "c"}),
        _ev("assistant", 13.0, {"type": "thinking"}, thinking_duration_ms=500),
    ]
    assert agentic.stream_timing(lines) == (7.5, 2.0)                 # 5 s + 2.5 s; 1.5 + 0.5


def test_no_tools_or_thinking_in_the_stream_is_not_zero():
    assert agentic.stream_timing([_ev("assistant", 1.0, {"type": "text"})]) == (None, None)


def test_wakeup_segments_sum_turns_and_tokens_but_not_running_totals():
    """Background tools (Monitor, ScheduleWakeup) give one result event per
    segment: num_turns/usage are per segment, cost and API time are running
    totals, and the last segment may have an empty message."""
    seg = lambda turns, cost, api, out, msg: json.dumps({
        "type": "result", "subtype": "success", "is_error": False, "num_turns": turns,
        "duration_api_ms": api, "total_cost_usd": cost, "result": msg,
        "usage": {"input_tokens": 10, "output_tokens": out,
                  "cache_read_input_tokens": 100, "cache_creation_input_tokens": 1}})
    res = agentic.AgenticResult(pair_id=PAIR, case_id="r1_springboot2to3", model_slug="m",
                                model_name="M", role="current", rep=0, run_id="r")
    agentic._summarize_stream([seg(116, 1.38, 600, 1000, "Build passes."),
                               seg(11, 2.62, 800, 50, "")], res)
    assert res.num_turns == 127
    assert res.output_tokens == 1050 and res.input_tokens == 20
    assert res.cache_read_tokens == 200 and res.cache_write_tokens == 2
    assert res.cost_estimate_usd == 2.62 and res.duration_api_ms == 800
    assert res.final_message == "Build passes." and res.error is None


def test_events_whose_message_is_text_do_not_break_parsing():
    """Claude Code can emit e.g. a system/permission_denied event whose
    `message` is a plain string; parsing must skip it, not crash the attempt."""
    lines = [
        json.dumps({"type": "assistant", "timestamp": "2026-11-01T00:00:00Z", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}]}}),
        json.dumps({"type": "system", "subtype": "permission_denied",
                    "message": "This command requires explicit approval."}),
        json.dumps({"type": "user", "timestamp": "2026-11-01T00:00:04Z", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1"}]}}),
        json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 3,
                    "total_cost_usd": 0.5, "result": "done", "usage": {}}),
    ]
    assert agentic.stream_timing(lines) == (4.0, None)
    res = agentic.AgenticResult(pair_id=PAIR, case_id="r1_springboot2to3", model_slug="m",
                                model_name="M", role="current", rep=0, run_id="r")
    agentic._summarize_stream(lines, res)
    assert res.num_turns == 3 and res.tool_calls == 1 and res.error is None



# --------------------------------------------------------------------------- #
# opencode backend                                                             #
# --------------------------------------------------------------------------- #
OC_KEY = "oc-test-key-0123456789"


def test_opencode_command_passes_the_key_by_name_and_the_goal_by_file(tmp_path):
    agentic.write_opencode_control(tmp_path / "c", "the goal mentions java",
                                   "the task mentions java", "glm-5.3", "medium")
    ws, control = tmp_path / "ws", tmp_path / "c"
    cmd = agentic.opencode_command("n", ws, control, "glm-5.3", postgres=True)
    assert not any("java" in a for a in cmd)
    envs = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-e"]
    assert envs[0] == "OPENCODE_API_KEY"                    # name only, no value
    assert "OPENCODE_CONFIG=/gate1/opencode.json" in envs and "GATE1_POSTGRES=1" in envs
    assert not any(e.startswith("OPENCODE_API_KEY=") for e in envs)
    mounts = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-v"]
    assert mounts[:2] == [f"{ws}:/work", f"{control}:/gate1:ro"]
    assert "< /gate1/prompt.txt" in cmd[cmd.index("-c") + 1]
    for flag in ("--standalone", "--auto", "--thinking"):
        assert flag in cmd
    assert cmd[cmd.index("--format") + 1] == "json"
    assert cmd[cmd.index("--model") + 1] == "opencode-go/glm-5.3"
    assert (control / "prompt.txt").read_text() == "/goal the goal mentions java"


def test_opencode_config_allows_only_go_and_no_sub_agents(tmp_path):
    agentic.write_opencode_control(tmp_path, "g", "t", "kimi-k3", "low")
    cfg = json.loads((tmp_path / "opencode.json").read_text())
    assert cfg["policies"] == [
        {"action": "provider.use", "resource": "*", "effect": "deny"},
        {"action": "provider.use", "resource": "opencode-go", "effect": "allow"}]
    assert cfg["permissions"][-1] == {"action": "subagent", "resource": "*", "effect": "deny"}
    assert cfg["model"] == {"providerID": "opencode-go", "model": "kimi-k3"}
    assert cfg["agents"]["build"]["request"]["body"] == {"reasoning_effort": "low"}
    assert cfg["agents"]["title"]["model"] == cfg["model"]
    assert cfg["instructions"] == ["/gate1/system.md"]
    assert cfg["lsp"] is False and cfg["formatter"] is False and cfg["snapshots"] is False
    assert cfg["mcp"] == {} and cfg["plugins"] == []
    no_effort = agentic.opencode_config("kimi-k3", None)
    assert "build" not in no_effort["agents"]


def test_each_agent_gets_only_its_own_credential(monkeypatch):
    monkeypatch.setenv("OPENCODE_GO_API_KEY", OC_KEY)
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "claude-token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "api-key")
    monkeypatch.setenv("OPENROUTER_TOKEN", "or-token")
    oc = agentic._opencode_env()
    assert oc["OPENCODE_API_KEY"] == OC_KEY
    assert not {"CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "OPENROUTER_TOKEN",
                "OPENCODE_GO_API_KEY"} & set(oc)
    cc = agentic._container_env()
    assert cc["CLAUDE_CODE_OAUTH_TOKEN"] == "claude-token"
    assert not {"OPENCODE_API_KEY", "OPENCODE_GO_API_KEY", "ANTHROPIC_API_KEY"} & set(cc)


def test_opencode_preflight_needs_the_go_key(monkeypatch):
    monkeypatch.delenv("OPENCODE_GO_API_KEY", raising=False)
    with pytest.raises(agentic.NotReady, match="OPENCODE_GO_API_KEY"):
        agentic.OpencodeBackend().preflight()


def _oc_stream(*, error=None, steps=True, key_leak=False):
    ev = []
    if steps:
        ev += [
            {"type": "step_start", "timestamp": 1_000_000, "part": {"type": "step-start"}},
            {"type": "reasoning", "timestamp": 1_001_000,
             "part": {"text": "think", "time": {"start": 1_000_000, "end": 1_002_000}}},
            {"type": "tool_use", "timestamp": 1_010_000, "part": {"tool": "shell", "state": {
                "status": "completed", "time": {"start": 1_003_000, "end": 1_010_000},
                "output": f"KEY={OC_KEY}" if key_leak else "ok"}}},
            {"type": "tool_use", "timestamp": 1_009_000, "part": {"tool": "read", "state": {
                "status": "completed", "time": {"start": 1_004_000, "end": 1_009_000}}}},
            {"type": "step_finish", "timestamp": 1_012_000, "part": {
                "reason": "tool-calls", "cost": 0.01,
                "tokens": {"input": 1000, "output": 200, "reasoning": 50,
                           "cache": {"read": 4000, "write": 0}}}},
            {"type": "step_start", "timestamp": 1_013_000, "part": {}},
            {"type": "text", "timestamp": 1_014_000, "part": {"text": "Goal met."}},
            {"type": "step_finish", "timestamp": 1_015_000, "part": {
                "reason": "stop", "cost": 0.02,
                "tokens": {"input": 500, "output": 100, "reasoning": 0,
                           "cache": {"read": 6000, "write": 10}}}},
        ]
    if error:
        ev.append({"type": "error", "timestamp": 1_016_000, "error": error})
    return "".join(json.dumps(e) + "\n" for e in ev)


def _summarize_oc(stream, model="glm-5.3"):
    res = agentic.AgenticResult(pair_id=PAIR, case_id="r1_springboot2to3", model_slug=model,
                                model_name="GLM-5.3", role="target", rep=0, run_id="r")
    agentic.summarize_opencode(stream.splitlines(), res, model)
    return res


def test_opencode_steps_sum_into_turns_tokens_cost_and_time():
    res = _summarize_oc(_oc_stream())
    assert res.num_turns == 2 and res.tool_calls == 2
    assert res.input_tokens == 1500 and res.output_tokens == 350 and res.reasoning_tokens == 50
    assert res.cache_read_tokens == 10000 and res.cache_write_tokens == 10
    assert res.cost_reported_usd == pytest.approx(0.03)
    assert res.cost_estimate_usd == pytest.approx(
        agentic.pricing.cost_usd("glm-5.3", 1500, 350, 10000, 10))
    assert res.tool_time_s == 7.0                          # 3–10 s, the read inside it counted once
    # steps 0–12 s and 13–15 s = 14 s of wall time, minus 7 s of tools
    assert res.duration_api_ms == 7000 and res.model_time_source == "derived"
    assert res.thinking_time_s == 2.0
    assert res.final_message == "Goal met." and res.error is None and res.agent_error is None


def test_opencode_provider_errors_are_infra_and_stop_the_batch():
    res = _summarize_oc(_oc_stream(steps=False, error={
        "type": "provider.auth", "message": "Upstream request failed: Invalid credential",
        "status": 401}))
    assert res.error.startswith("opencode error: provider.auth: Upstream request failed")
    assert agentic._OPENCODE_LIMIT_RE.search(res.error)
    quota = _summarize_oc(_oc_stream(error={"type": "unknown", "message": "weekly limit reached",
                                            "status": 429}))
    assert quota.error and agentic._OPENCODE_LIMIT_RE.search(quota.error)


def test_an_opencode_error_the_model_caused_is_scored_not_infra():
    res = _summarize_oc(_oc_stream(error={"type": "session.context-overflow",
                                          "message": "context window exceeded"}))
    assert res.error is None
    assert res.agent_error == "opencode error: session.context-overflow: context window exceeded"


def test_opencode_that_never_called_a_model_did_not_run():
    res = _summarize_oc("opencode: 1: exec: opencode: not found\n")
    assert res.error.startswith("agent did not run: opencode made no model call")
    assert "not found" in res.error and agentic._OPENCODE_LIMIT_RE.search(res.error)
    timed_out = agentic.AgenticResult(pair_id=PAIR, case_id="r1_springboot2to3", model_slug="m",
                                      model_name="M", role="target", rep=0, run_id="r",
                                      timed_out=True)
    agentic.summarize_opencode([], timed_out, "m")
    assert timed_out.error is None                          # the time limit is scored


def test_an_opencode_attempt_is_scored_recorded_and_its_key_redacted(env, monkeypatch):
    monkeypatch.setenv("OPENCODE_GO_API_KEY", OC_KEY)
    seen = {}

    def popen(cmd, **kw):
        seen["cmd"], seen["env"] = cmd, kw["env"]
        return _FakeAgent(cmd, lambda ws: (ws / "pom.xml").write_text("<boot3/>"),
                          _oc_stream(key_leak=True))

    monkeypatch.setattr(agentic.subprocess, "Popen", popen)
    model = env["cfg"].get_pair(PAIR).target                # DeepSeek V4 Pro on Go
    backend = agentic.OpencodeBackend()
    backend.version = "2.2.5"
    res = agentic.run_attempt(env["cfg"], PAIR, "target", model, "r1_springboot2to3", 0,
                              "20261101T000000Z", workroot=env["tmp"] / "work",
                              scorer=env["scorer"], backend=backend)
    assert res.ok and res.passed and res.num_turns == 2
    assert (res.agent, res.provider, res.agent_version, res.goal_mode) == (
        "opencode", "opencode-go", "2.2.5", "native")
    assert seen["env"]["OPENCODE_API_KEY"] == OC_KEY and OC_KEY not in " ".join(seen["cmd"])
    rec = agentic.record_path(PAIR, "20261101T000000Z", model.id, "r1_springboot2to3", 0)
    log = rec.with_suffix(".stream.jsonl").read_text()
    assert OC_KEY not in log and "[REDACTED]" in log
    assert OC_KEY not in rec.read_text()
    report = agentic.render_report(PAIR, "20261101T000000Z",
                                   agentic.load_records(PAIR, "20261101T000000Z"))
    assert "DeepSeek V4 Pro · opencode" in report


def test_the_batch_stops_at_the_spend_cap(env, monkeypatch):
    calls = []

    def attempt(*a, **kw):
        calls.append(a[4])
        return agentic.AgenticResult(pair_id=PAIR, case_id=a[4], model_slug="m", model_name="m",
                                     role="target", rep=a[5], run_id=a[6], ok=True, passed=True,
                                     cost_estimate_usd=3.0)

    monkeypatch.setattr(agentic, "run_attempt", attempt)
    monkeypatch.setattr(agentic, "render_report", lambda *a: "")
    monkeypatch.setattr(agentic, "agentic_dir", lambda p, r: env["tmp"])
    agentic.run(env["cfg"], PAIR, role="target", case="r1_springboot2to3", repeats=5,
                backend=agentic.OpencodeBackend(), max_spend_usd=5.0)
    assert len(calls) == 2                                   # $3, then $6 >= $5: stop
