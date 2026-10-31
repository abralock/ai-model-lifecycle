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


def test_only_claude_code_models_run_agentic(monkeypatch):
    cfg = load_config()
    with pytest.raises(ValueError, match="Claude Code"):
        agentic.run(cfg, PAIR, role="target")                 # DeepSeek via OpenCode Go


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
