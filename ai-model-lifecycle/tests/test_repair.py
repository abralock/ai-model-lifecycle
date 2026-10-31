"""tests/test_repair.py — CI-style repair rounds (repair.py).

Single-shot stays Gate 1's score. A repair round is a separate, agentic
measurement: a failed answer's model sees what CI would show (failed checks,
build/test output) plus the current content of the files the errors point at,
and replies with fix-up FILE/EDIT/DELETE blocks. The fix-up is scored on top of
the tree the earlier answers produced (the scorer's `base`), so the repair's own
edits must still apply. Records live under runs/<pair>/repair/<run>/ and never
feed REPORT.md, the effort sweep or the overall score.

All offline: the scorer and the model call are faked; the case tree is a tmp dir.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import common
import repair
import report
import runner
from common import load_config
from scorers.base import ScoreResult, apply_output

PAIR = "opus-5.5-cc-vs-kimi-k3"
CASE = "r1b_jhipster_boot3"
RID = "20261031T000132Z"

POM = "<project>\n  <dependencies>\n    <dependency>problem-spring-web</dependency>\n  </dependencies>\n</project>\n"
JACKSON = "import org.zalando.problem.jackson.ProblemModule;\nclass JacksonConfiguration {}\n"
FIX = ("### EDIT: pom.xml\n```xml\n<<<<<<< SEARCH\n    <dependency>problem-spring-web</dependency>\n"
       "=======\n    <dependency>problem-spring-web</dependency>\n"
       "    <dependency>jackson-datatype-problem</dependency>\n>>>>>>> REPLACE\n```\n")
FIRST_ANSWER = ("### FILE: src/main/java/Jackson.java\n```java\n" + JACKSON + "```\n")
COMPILE_ERROR = ("[ERROR] /w/src/main/java/Jackson.java:[1,35] package "
                 "org.zalando.problem.jackson does not exist")


@pytest.fixture
def case_tree(tmp_path, monkeypatch):
    """A tiny pristine project standing in for cases/r1b_jhipster_boot3/project."""
    base = tmp_path / "pristine"
    (base / "src" / "main" / "java").mkdir(parents=True)
    (base / "src" / "test" / "java").mkdir(parents=True)
    (base / "pom.xml").write_text(POM)
    (base / "README.md").write_text("# app\n```bash\nmvn verify\n```\n")
    (base / "src" / "test" / "java" / "HiddenIT.java").write_text("class HiddenIT {}\n")
    monkeypatch.setattr(repair, "pristine", lambda case_id: (base, "project/"))
    monkeypatch.setattr(repair.sources, "ensure", lambda case_id: None)
    return base


def _fake_scorer(case_id, output_text, model_slug="", base=None):
    """Pass iff the tree (base or pristine, plus this answer) declares the
    missing dependency; fail like the real r1b compile error otherwise."""
    tree = Path(repair.common.RUNS_DIR).parent / f"score-{len(_fake_scorer.calls)}"
    shutil.rmtree(tree, ignore_errors=True)
    shutil.copytree(base or repair.pristine(case_id)[0], tree)
    applied = apply_output(output_text, tree, strip_prefix="project/")
    # `base` is a temp dir repair.py deletes after scoring: keep a snapshot
    _fake_scorer.calls.append({"output": output_text, "base": base, "snapshot": tree})
    res = ScoreResult(case_id=case_id, model_slug=model_slug)
    res.details["edit_failures"] = applied.edit_failures
    if applied.edit_failures:
        res.reason = "failed checks: edits_applied"
        return res
    if "jackson-datatype-problem" in (tree / "pom.xml").read_text():
        res.passed, res.reason = True, "build, unit, integration and e2e tests pass"
    else:
        res.reason = "failed checks: build, unit_tests, integration_tests, e2e"
        res.details["build_errors"] = [COMPILE_ERROR]
        res.details["build_tail"] = COMPILE_ERROR + "\n[ERROR] -> [Help 1]"
    return res


@pytest.fixture
def env(tmp_path, monkeypatch, case_tree):
    runs = tmp_path / "runs"
    monkeypatch.setattr(common, "RUNS_DIR", runs)
    _fake_scorer.calls = []
    monkeypatch.setattr(repair, "score_case", _fake_scorer)
    replies: list[str] = []
    sent: list[dict] = []

    def fake_call_model(model_id, prompt, **kw):
        sent.append({"model": model_id, "prompt": prompt, **kw})
        text = replies.pop(0) if replies else FIX
        usage = {"input_tokens": 100, "output_tokens": 50, "cache_read_tokens": 0,
                 "cache_write_tokens": 0, "total_tokens": 150}
        return runner.CallResult(usage, 1, 12.5, text, "stop", None, provider="claude-code",
                                 cost_estimate_usd=0.42, reasoning_tokens=30,
                                 thinking_time_s=4.0, execution_time_s=7.0)

    monkeypatch.setattr(runner, "call_model", fake_call_model)
    monkeypatch.setattr(runner, "claude_code_preflight", lambda: None)
    cfg = load_config(suite="real")
    return {"cfg": cfg, "runs": runs, "replies": replies, "sent": sent}


def _write_record(runs, *, rep=0, ok=True, error=None, output=FIRST_ANSWER, effort="high",
                  case=CASE):
    d = runs / PAIR
    d.mkdir(parents=True, exist_ok=True)
    rec = {"pair_id": PAIR, "case_id": case, "model_slug": "claude-opus-5-5",
           "model_name": "Claude Opus 5.5 (CC)", "role": "current", "suite": "real", "rep": rep,
           "run_id": RID, "ok": ok, "error": error, "output_text": output if ok else "",
           "latency_s": 600.0, "effort_override": effort,
           "reasoning_requested": {"effort": effort} if effort else None}
    suffix = f".r{rep}" if rep else ""
    (d / f"claude-opus-5-5.{case}.{RID}{suffix}.json").write_text(json.dumps(rec))


# --------------------------------------------------------------------------- #
# trees, feedback, context, prompt                                             #
# --------------------------------------------------------------------------- #
def test_build_tree_applies_answers_in_order(case_tree, tmp_path):
    """A later answer's EDIT applies to the file an earlier answer wrote, and a
    later FILE replaces an earlier answer's EDIT — the order a developer's
    successive commits would have."""
    first = ("### FILE: src/main/java/A.java\n```java\nclass A { int x = 1; }\n```\n"
             "### EDIT: pom.xml\n```xml\n<<<<<<< SEARCH\n<project>\n=======\n<project v='3'>\n"
             ">>>>>>> REPLACE\n```\n")
    second = ("### EDIT: src/main/java/A.java\n```java\n<<<<<<< SEARCH\nint x = 1;\n=======\n"
              "int x = 2;\n>>>>>>> REPLACE\n```\n"
              "### FILE: pom.xml\n```xml\n<project v='final'/>\n```\n")
    dest = tmp_path / "tree"
    applied = repair.build_tree(CASE, [first, second], dest)
    assert all(not a.edit_failures for a in applied)
    assert (dest / "src/main/java/A.java").read_text() == "class A { int x = 2; }\n"
    assert (dest / "pom.xml").read_text() == "<project v='final'/>\n"


def test_feedback_shows_what_ci_would_show():
    sr = ScoreResult(case_id=CASE, reason="failed checks: build, unit_tests")
    sr.checks = {"boot3": True, "build": False, "unit_tests": False}
    sr.details = {"build_errors": [COMPILE_ERROR], "build_tail": "x" * 50_000,
                  "tests_run": {"unit": 0, "integration": 0},
                  "edit_failures": ["pom.xml: SEARCH text not found (starts '<x>')"]}
    fb = repair.feedback_text(sr)
    assert "failed checks: build, unit_tests" in fb
    assert COMPILE_ERROR in fb
    assert "SEARCH text not found" in fb
    assert len(fb) <= repair.MAX_FEEDBACK_CHARS


def test_context_files_follow_the_errors_and_skip_hidden_tests(case_tree, tmp_path):
    tree = tmp_path / "tree"
    repair.build_tree(CASE, [FIRST_ANSWER], tree)
    feedback = (COMPILE_ERROR + "\n[ERROR] /w/src/test/java/HiddenIT.java:[1,1] boom\n")
    files = repair.context_files(tree, feedback)
    assert list(files) == ["src/main/java/Jackson.java", "pom.xml"]   # error file first
    assert files["src/main/java/Jackson.java"] == JACKSON
    assert "src/test/java/HiddenIT.java" not in files                  # hidden suite never shown


def test_repair_prompt_has_task_feedback_files_and_rules(case_tree, tmp_path):
    tree = tmp_path / "tree"
    repair.build_tree(CASE, [FIRST_ANSWER], tree)
    feedback = "failed checks: build\n" + COMPILE_ERROR
    prompt = repair.repair_prompt(CASE, feedback, repair.context_files(tree, feedback), 1)
    assert "Upgrade a real application from Spring Boot 2.7" in prompt     # the task statement
    assert COMPILE_ERROR in prompt
    assert "### src/main/java/Jackson.java" in prompt and JACKSON.strip() in prompt
    assert "already been applied" in prompt and "src/test/" in prompt


# --------------------------------------------------------------------------- #
# the repair loop                                                              #
# --------------------------------------------------------------------------- #
def test_failed_answer_is_repaired_and_scored_on_top_of_its_tree(env):
    _write_record(env["runs"])
    results = repair.repair_run(env["cfg"], PAIR, RID, rounds=1)
    assert len(results) == 1 and results[0]["passed"] is True
    assert results[0]["single_shot_passed"] is False
    # the model got the CI feedback and the file the error points at
    prompt = env["sent"][0]["prompt"]
    assert "org.zalando.problem.jackson does not exist" in prompt
    assert JACKSON.strip() in prompt
    # the same route and effort as the single-shot answer
    assert env["sent"][0]["reasoning"] == {"effort": "high"}
    # the repair answer alone was scored, on top of the first answer's tree
    last = _fake_scorer.calls[-1]
    assert last["output"] == FIX and last["base"] is not None
    assert (last["snapshot"] / "src/main/java/Jackson.java").read_text() == JACKSON


def test_repair_records_live_apart_from_the_scorecard(env):
    _write_record(env["runs"])
    repair.repair_run(env["cfg"], PAIR, RID, rounds=1)
    saved = list((env["runs"] / PAIR / "repair" / RID).glob("*.json"))
    assert len(saved) == 1
    rec = json.loads(saved[0].read_text())
    assert rec["round"] == 1 and rec["passed"] is True and rec["source_run"] == RID
    assert rec["repair_output"] == FIX
    assert rec["latency_s"] == 12.5 and rec["cost_estimate_usd"] == 0.42
    assert rec["thinking_time_s"] == 4.0 and rec["execution_time_s"] == 7.0
    # the scorecard and the effort sweep never see repair records
    assert common.list_runs(PAIR) == [RID]
    assert len(common.load_runs(PAIR, run=RID)) == 1


def test_passing_answers_infra_errors_and_empty_answers_are_not_repaired(env):
    _write_record(env["runs"], rep=0, output=FIRST_ANSWER + FIX)              # already passes
    _write_record(env["runs"], rep=1, ok=False, error="claude -p error: Request timed out")
    _write_record(env["runs"], rep=2, ok=False,
                  error="empty completion (finish_reason=length)")
    results = repair.repair_run(env["cfg"], PAIR, RID, rounds=1)
    by_rep = {r["rep"]: r for r in results}
    assert by_rep[0]["status"] == "passed single-shot"
    assert by_rep[1]["status"].startswith("infra")
    assert by_rep[2]["status"].startswith("no answer")
    assert env["sent"] == []                                            # no model call at all


def test_a_second_round_gets_the_new_feedback_and_stops_on_pass(env):
    _write_record(env["runs"])
    bad = "### FILE: src/main/java/Other.java\n```java\nclass Other {}\n```\n"
    env["replies"].extend([bad, FIX])
    results = repair.repair_run(env["cfg"], PAIR, RID, rounds=3)
    assert results[0]["passed"] is True and results[0]["rounds_used"] == 2
    assert len(env["sent"]) == 2                                        # stopped after the pass
    # round 2 is scored on the tree with BOTH earlier answers applied
    assert (_fake_scorer.calls[-1]["snapshot"] / "src/main/java/Other.java").is_file()
    assert len(list((env["runs"] / PAIR / "repair" / RID).glob("*.json"))) == 2


def test_repair_edits_that_do_not_apply_still_fail(env):
    """The repair's own edits must apply, exactly as in single-shot scoring."""
    _write_record(env["runs"])
    env["replies"].append("### EDIT: pom.xml\n```xml\n<<<<<<< SEARCH\n<nope/>\n=======\n<x/>\n"
                          ">>>>>>> REPLACE\n```\n")
    results = repair.repair_run(env["cfg"], PAIR, RID, rounds=1)
    assert results[0]["passed"] is False


def test_only_project_cases_can_be_repaired():
    with pytest.raises(ValueError, match="r1b_jhipster_boot3"):
        repair.pristine("r3_oracle_to_postgres")
    path, prefix = repair.pristine("r1b_jhipster_boot3")
    assert path.name == "project" and prefix == "project/"


def test_max_repairs_caps_model_calls(env):
    for rep in range(3):
        _write_record(env["runs"], rep=rep)
    repair.repair_run(env["cfg"], PAIR, RID, rounds=1, max_repairs=1)
    assert len(env["sent"]) == 1


# --------------------------------------------------------------------------- #
# report                                                                       #
# --------------------------------------------------------------------------- #
def test_repair_report_separates_single_shot_from_repaired(env):
    _write_record(env["runs"], rep=0)
    _write_record(env["runs"], rep=1)
    env["replies"].extend([FIX, "### FILE: src/main/java/Other.java\n```java\nclass O {}\n```\n"])
    results = repair.repair_run(env["cfg"], PAIR, RID, rounds=1)
    md = repair.render_report(PAIR, RID, results)
    assert "Single-shot" in md and "After repair" in md
    assert "| r1b_jhipster_boot3 | 0/2 | 1/2 |" in md
    assert "never part of REPORT.md" in md


# --------------------------------------------------------------------------- #
# scorers take a base tree; dispatch passes it through                         #
# --------------------------------------------------------------------------- #
def test_r1b_scorer_starts_from_the_given_base(tmp_path, monkeypatch):
    """With docker hidden, r1b runs its static checks only: enough to see that
    the pom it reads came from `base`, not from the pristine project."""
    from scorers import r1b_scorer

    base = tmp_path / "base"
    shutil.copytree(r1b_scorer.PROJECT, base)
    pom = (base / "pom.xml").read_text()
    (base / "pom.xml").write_text(pom.replace("<spring-boot.version>2.7.3<",
                                              "<spring-boot.version>3.1.5<"))
    monkeypatch.setattr(shutil, "which", lambda name: None)
    answer = "### FILE: notes.txt\n```\nrepair\n```\n"
    res = r1b_scorer.score(answer, base=base)
    assert res.details["spring_boot_version"] == "3.1.5"
    res = r1b_scorer.score(answer)
    assert res.details["spring_boot_version"].startswith("2.7")


def test_dispatch_passes_base_through(monkeypatch, tmp_path):
    from scorers import dispatch, r1b_scorer

    seen = {}
    monkeypatch.setattr(r1b_scorer, "score",
                        lambda text, model_slug="", base=None: seen.update(base=base) or
                        ScoreResult(case_id=CASE))
    dispatch.score_case(CASE, "x", "m", base=tmp_path)
    assert seen["base"] == tmp_path


# --------------------------------------------------------------------------- #
# feedback a repair round can act on                                           #
# --------------------------------------------------------------------------- #
STARTUP_FAILURE = """***************************
APPLICATION FAILED TO START
***************************
Description:
Binding to target [Bindable@1 type = tech.jhipster.config.JHipsterProperties] failed:
    Property: jhipster.logging.logstash.queue-size
    Value: "512"
    Origin: class path resource [config/application-dev.yml] - 101:21
    Reason: The elements [jhipster.logging.logstash.queue-size] were left unbound.
"""


def test_r1b_e2e_keeps_the_crash_log_of_an_app_that_dies_at_startup(tmp_path, monkeypatch):
    """`docker run --rm` deleted a crashed app's container before `docker logs`
    could read it, so the feedback said only "No such container". The
    finally block removes the container anyway."""
    from scorers import r1b_scorer

    frontend = tmp_path / "frontend"
    (frontend / "target" / "classes" / "static").mkdir(parents=True)
    (frontend / "target" / "classes" / "static" / "index.html").write_text("<html/>")
    (frontend / "node_modules" / ".bin").mkdir(parents=True)
    (frontend / "node_modules" / ".bin" / "cypress").write_text("")
    monkeypatch.setattr(r1b_scorer, "FRONTEND", frontend)
    project = tmp_path / "project"
    project.mkdir()
    cmds: list[list[str]] = []

    def fake_run(cmd, cwd=None, timeout=900, env=None):
        cmds.append(list(cmd))
        if "package" in cmd:
            (project / "target").mkdir(exist_ok=True)
            (project / "target" / "app.jar").write_text("")
        if cmd[:2] == ["docker", "logs"]:
            return 0, "boot noise\n" * 200 + STARTUP_FAILURE
        return 0, ""

    monkeypatch.setattr(r1b_scorer, "_run", fake_run)
    monkeypatch.setattr(r1b_scorer, "_wait_http", lambda url, timeout_s: False)
    res = ScoreResult(case_id=CASE)
    assert r1b_scorer.run_e2e(project, res) is False
    start = next(c for c in cmds if c[:3] == ["docker", "run", "-d"])
    assert "--rm" not in start
    assert any(c[:3] == ["docker", "rm", "-f"] for c in cmds)       # still cleaned up
    assert "were left unbound" in res.details["e2e_tail"]
    assert "config/application-dev.yml" in res.details["e2e_tail"]


def test_context_files_match_classpath_resource_paths(case_tree, tmp_path):
    """Spring names config files relative to src/main/resources."""
    tree = tmp_path / "tree"
    repair.build_tree(CASE, [], tree)
    cfg_dir = tree / "src" / "main" / "resources" / "config"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "application-dev.yml").write_text("jhipster:\n  logging:\n    logstash:\n"
                                                 "      queue-size: 512\n")
    (cfg_dir / "application-prod.yml").write_text("other: 1\n")
    files = repair.context_files(tree, STARTUP_FAILURE)
    assert "src/main/resources/config/application-dev.yml" in files
    assert "src/main/resources/config/application-prod.yml" not in files


def test_repairing_again_clears_the_answers_old_rounds(env):
    """A re-repair that passes in round 1 must not leave an earlier attempt's
    round 2/3 records behind (they would be read as this attempt's)."""
    _write_record(env["runs"])
    env["replies"].extend(["### FILE: src/main/java/Other.java\n```java\nclass O {}\n```\n", FIX])
    repair.repair_run(env["cfg"], PAIR, RID, rounds=3)            # passes in round 2
    out = env["runs"] / PAIR / "repair" / RID
    assert len(list(out.glob("*.round*.json"))) == 2
    env["replies"].append(FIX)
    repair.repair_run(env["cfg"], PAIR, RID, rounds=3, redo=True)  # passes in round 1
    assert [p.name.split(".")[-2] for p in sorted(out.glob("*.round*.json"))] == ["round1"]


def test_an_answer_already_repaired_is_not_repaired_again(env):
    """Resuming after a usage-limit stop must not spend calls on answers that
    already passed; redo=True forces a fresh attempt."""
    _write_record(env["runs"])
    repair.repair_run(env["cfg"], PAIR, RID, rounds=3)                 # passes in round 1
    assert len(env["sent"]) == 1
    results = repair.repair_run(env["cfg"], PAIR, RID, rounds=3)
    assert len(env["sent"]) == 1                                       # no new call
    assert results[0]["passed"] is True and results[0]["status"].startswith("repaired earlier")
    repair.repair_run(env["cfg"], PAIR, RID, rounds=3, redo=True)
    assert len(env["sent"]) == 2
