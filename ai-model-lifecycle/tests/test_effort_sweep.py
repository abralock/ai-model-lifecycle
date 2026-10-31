"""tests/test_effort_sweep.py — thinking-effort sweeps (low / medium / high).

`runner.py --effort low,medium,high` runs a pair once per level, each level in
its own run id, every call recording `effort_override`. `report.py --by-effort`
turns those runs into one table row per model x level. Effort runs never
become the main scorecard. Supported routes: Claude Code (`--effort`) and
OpenCode Go chat (`reasoning_effort`); OpenRouter is out of scope
(docs/METRICS_PLAN.md) and Go's responses/messages routes have no verified
effort control, so those are refused rather than silently ignored.

All offline: call_model is faked and run files go to a tmp RUNS_DIR.
"""

from __future__ import annotations

import json

import pytest

import common
import report
import runner
from common import load_config

CC_PAIR = "opus-5.5-cc-vs-kimi-k3"     # current: claude-code, target: opencode-go chat
GO_PAIR = "glm-5.2-vs-5.3"             # both opencode-go chat, params reasoning_effort: low
OR_PAIR = "opus-4.8-vs-5.5"            # OpenRouter
RESPONSES_PAIR = "gpt-5.6-luna-vs-6-luna"
CASE = "r3_oracle_to_postgres"

FAKE_USAGE = {"input_tokens": 1, "output_tokens": 1, "cache_read_tokens": 0,
              "cache_write_tokens": 0, "total_tokens": 2}


@pytest.fixture
def calls(monkeypatch, tmp_path):
    """Fake every model call; record what the runner would have sent."""
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    seen: list[dict] = []

    def fake_call_model(model_id, prompt, **kw):
        seen.append({"model": model_id, **kw})
        return runner.CallResult(FAKE_USAGE, 1, 0.1, "out", "stop", None)

    monkeypatch.setattr(runner, "call_model", fake_call_model)
    monkeypatch.setattr(runner, "claude_code_preflight", lambda: None)
    return seen


# --------------------------------------------------------------------------- #
# runner: the override reaches each route and is recorded                     #
# --------------------------------------------------------------------------- #
def test_cc_effort_override_is_sent_and_recorded(calls, tmp_path):
    cfg = load_config()
    pair = cfg.get_pair(CC_PAIR)
    res = runner.run_case(cfg, CC_PAIR, CASE, pair.current, "current",
                          run_id="20261031T000000Z", effort_override="low")
    # call_model turns reasoning={"effort": ...} into `claude -p --effort low`
    assert calls[0]["reasoning"] == {"effort": "low"}
    assert res.reasoning_requested == {"effort": "low"}
    assert res.effort_override == "low"
    saved = json.loads(next(tmp_path.rglob("*.json")).read_text())
    assert saved["effort_override"] == "low"


def test_override_beats_the_suite_effort(calls):
    cfg = load_config(suite="real")                 # real suite sends effort: medium
    pair = cfg.get_pair(CC_PAIR)
    runner.run_case(cfg, CC_PAIR, "r2_gwt_to_angular", pair.current, "current",
                    run_id="20261031T000000Z", effort_override="high")
    assert calls[0]["reasoning"] == {"effort": "high"}


def test_no_override_keeps_todays_behavior(calls):
    cfg = load_config(suite="real")
    pair = cfg.get_pair(CC_PAIR)
    res = runner.run_case(cfg, CC_PAIR, "r2_gwt_to_angular", pair.current, "current",
                          run_id="20261031T000000Z")
    assert calls[0]["reasoning"] == {"effort": "medium"}
    assert res.effort_override is None


def test_go_override_replaces_the_model_param_without_mutating_config(calls):
    cfg = load_config()
    pair = cfg.get_pair(GO_PAIR)
    res = runner.run_case(cfg, GO_PAIR, CASE, pair.target, "target",
                          run_id="20261031T000000Z", effort_override="high")
    assert calls[0]["extra_params"]["reasoning_effort"] == "high"
    assert res.reasoning_requested == {"effort": "high"}
    assert pair.target.params["reasoning_effort"] == "low"     # models.yaml untouched


def test_go_override_added_when_the_model_has_no_params(calls):
    cfg = load_config()
    pair = cfg.get_pair(CC_PAIR)                    # Kimi K3: no params
    runner.run_case(cfg, CC_PAIR, CASE, pair.target, "target",
                    run_id="20261031T000000Z", effort_override="medium")
    assert calls[0]["extra_params"] == {"reasoning_effort": "medium"}


@pytest.mark.parametrize("pair_id, why", [(OR_PAIR, "OpenRouter"),
                                          (RESPONSES_PAIR, "responses")])
def test_unsupported_routes_refuse_before_any_call(calls, pair_id, why):
    cfg = load_config()
    with pytest.raises(ValueError, match=why):
        runner.run_pair(cfg, pair_id, case=CASE, effort_override="low")
    assert calls == []


# --------------------------------------------------------------------------- #
# runner: one side only, and one run id per level                              #
# --------------------------------------------------------------------------- #
def test_role_runs_one_side_only(calls, tmp_path):
    cfg = load_config()
    pair = cfg.get_pair(CC_PAIR)
    runner.run_pair(cfg, CC_PAIR, case=CASE, role="current", repeats=2,
                    run_id="20261031T000000Z", effort_override="low")
    assert {c["model"] for c in calls} == {pair.current.id}
    recs = [json.loads(f.read_text()) for f in tmp_path.rglob("*.json")]
    assert len(recs) == 2 and {r["role"] for r in recs} == {"current"}


def test_role_lets_a_cc_side_run_while_the_other_route_is_refused(calls):
    """--role current on the Opus/Kimi pair only validates the side it runs."""
    cfg = load_config()
    runner.run_pair(cfg, CC_PAIR, case=CASE, role="current", effort_override="low")
    assert len(calls) == 1


def test_main_sweeps_each_level_in_its_own_run_id(monkeypatch):
    ids = iter(["20261031T000000Z", "20261031T000000Z", "20261031T000001Z",
                "20261031T000002Z"])
    monkeypatch.setattr(runner, "new_run_id", lambda: next(ids))
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    swept: list[tuple] = []
    monkeypatch.setattr(runner, "run_pair",
                        lambda cfg, pid, **kw: swept.append((kw["run_id"], kw["effort_override"],
                                                             kw["role"])) or [])
    rc = runner.main(["--pair", CC_PAIR, "--effort", "low,medium,high", "--role", "current"])
    assert rc == 0
    assert [s[1] for s in swept] == ["low", "medium", "high"]
    assert len({s[0] for s in swept}) == 3                   # never two levels in one run
    assert {s[2] for s in swept} == {"current"}


@pytest.mark.parametrize("level", ["xhigh", "max"])
def test_cc_takes_the_extended_levels(calls, level):
    """Claude Code's --effort accepts low, medium, high, xhigh and max
    (claude --help, CLI 2.1.314)."""
    cfg = load_config()
    pair = cfg.get_pair(CC_PAIR)
    res = runner.run_case(cfg, CC_PAIR, CASE, pair.current, "current",
                          run_id="20261031T000000Z", effort_override=level)
    assert calls[0]["reasoning"] == {"effort": level}
    assert res.effort_override == level


@pytest.mark.parametrize("level", ["xhigh", "max"])
def test_go_refuses_levels_beyond_high(calls, level):
    """Go's chat route takes OpenAI-style reasoning_effort, whose standard
    levels stop at high: refuse rather than send a value it may ignore."""
    cfg = load_config()
    with pytest.raises(ValueError, match="Claude Code only"):
        runner.run_pair(cfg, GO_PAIR, case=CASE, effort_override=level)
    assert calls == []


def test_main_sweeps_all_five_levels_in_order(monkeypatch):
    ids = iter(f"20261031T00000{i}Z" for i in range(5))
    monkeypatch.setattr(runner, "new_run_id", lambda: next(ids))
    swept: list[str] = []
    monkeypatch.setattr(runner, "run_pair",
                        lambda cfg, pid, **kw: swept.append(kw["effort_override"]) or [])
    rc = runner.main(["--pair", CC_PAIR, "--role", "current",
                      "--effort", "low,medium,high,xhigh,max"])
    assert rc == 0 and swept == ["low", "medium", "high", "xhigh", "max"]


def test_effort_report_orders_all_five_levels(tmp_path, monkeypatch):
    cfg = load_config()
    d = tmp_path / CC_PAIR
    for i, level in enumerate(["max", "low", "xhigh", "high", "medium"]):
        _write(d, "current", CASE, f"20261031T00000{i}Z", effort=level, thinking=1.0,
               execution=1.0, name="Opus")
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    md = report.render_effort_report(cfg, CC_PAIR, score=False)
    order = [line.split(" | ")[1] for line in md.splitlines() if line.startswith("| Opus | ")]
    assert order == ["low", "medium", "high", "xhigh", "max"]


def test_main_rejects_an_unknown_level(monkeypatch):
    monkeypatch.setattr(runner, "run_pair", lambda *a, **k: pytest.fail("must not run"))
    with pytest.raises(SystemExit):
        runner.main(["--pair", CC_PAIR, "--effort", "ultra"])


def test_main_reports_an_unsupported_route_cleanly(monkeypatch, capsys):
    rc = runner.main(["--pair", OR_PAIR, "--effort", "low", "--dry-run"])
    assert rc == 2
    assert "OpenRouter" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# report: effort runs stay out of the main scorecard                           #
# --------------------------------------------------------------------------- #
def _write(d, role, case, rid, *, effort=None, thinking=None, execution=None,
           latency=10.0, ok=True, rep=0, slug=None, name=None, reasoning=None):
    d.mkdir(parents=True, exist_ok=True)
    slug = slug or f"m-{role}"
    rec = {"case_id": case, "role": role, "model_slug": slug, "model_name": name or slug,
           "ok": ok, "error": None if ok else "empty completion", "latency_s": latency,
           "input_tokens": 10, "output_tokens": 10, "cache_read_tokens": 0,
           "cache_write_tokens": 0, "total_tokens": 20, "reasoning_tokens": 5,
           "output_text": "x", "billed_cost_usd": None, "cost_estimate_usd": 0.01,
           "provider": "claude-code", "effort_override": effort,
           "reasoning_requested": reasoning or ({"effort": effort} if effort else None),
           "thinking_time_s": thinking, "execution_time_s": execution}
    suffix = f".r{rep}" if rep else ""
    (d / f"{slug}.{case}.{rid}{suffix}.json").write_text(json.dumps(rec))


def test_pick_run_never_picks_an_effort_run(tmp_path, monkeypatch):
    cfg = load_config()
    d = tmp_path / CC_PAIR
    for case in cfg.cases:
        for role in ("current", "target"):
            _write(d, role, case, "20261030T000000Z")                    # normal, older
            _write(d, role, case, "20261031T000000Z", effort="high")     # effort, newer
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    run, skipped = report.pick_run(cfg, CC_PAIR)
    assert run == "20261030T000000Z"
    assert skipped == []            # an effort run is not a "newer partial run"


def test_effort_runs_keeps_the_latest_run_per_role_and_level(tmp_path, monkeypatch):
    cfg = load_config()
    d = tmp_path / CC_PAIR
    _write(d, "current", CASE, "20261031T000000Z", effort="low", thinking=1.0)
    _write(d, "current", CASE, "20261031T010000Z", effort="low", thinking=2.0)   # newer low
    _write(d, "current", CASE, "20261031T020000Z", effort="high", thinking=9.0)
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    found = report.effort_runs(cfg, CC_PAIR)
    assert set(found) == {("current", "low"), ("current", "high")}
    assert found[("current", "low")][0] == "20261031T010000Z"
    assert [r["thinking_time_s"] for r in found[("current", "low")][1]] == [2.0]


# --------------------------------------------------------------------------- #
# report: the by-effort table                                                  #
# --------------------------------------------------------------------------- #
@pytest.fixture
def sweep(tmp_path, monkeypatch):
    cfg = load_config()
    d = tmp_path / CC_PAIR
    for case in cfg.cases:
        _write(d, "current", case, "20261031T000000Z", effort="low",
               thinking=2.0, execution=8.0, latency=12.0, name="Opus")
        _write(d, "current", case, "20261031T010000Z", effort="high",
               thinking=20.0, execution=10.0, latency=33.0, name="Opus")
    # the main scorecard run, uninstrumented: thinking must render n/a, not 0
    for case in cfg.cases:
        for role in ("current", "target"):
            _write(d, role, case, "20261030T000000Z", latency=25.0,
                   name="Opus" if role == "current" else "Kimi")
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    return cfg


def test_effort_report_has_one_row_per_model_and_level(sweep):
    md = report.render_effort_report(sweep, CC_PAIR, score=False)
    low = next(line for line in md.splitlines() if line.startswith("| Opus | low |"))
    high = next(line for line in md.splitlines() if line.startswith("| Opus | high |"))
    assert "20261031T000000Z" in low and "2.00" in low and "8.00" in low
    assert "20261031T010000Z" in high and "20.00" in high and "0.50" in high   # 10 / 20
    assert md.index("| Opus | low |") < md.index("| Opus | high |")            # low → high


def test_effort_report_includes_the_default_run_as_baseline(sweep):
    md = report.render_effort_report(sweep, CC_PAIR, score=False)
    default = next(line for line in md.splitlines() if line.startswith("| Opus | default"))
    assert "20261030T000000Z" in default and "n/a" in default
    assert any(line.startswith("| Kimi | default") for line in md.splitlines())


def test_effort_report_breaks_thinking_down_by_task(sweep):
    md = report.render_effort_report(sweep, CC_PAIR, score=False)
    assert "Thinking time by task" in md
    row = next(line for line in md.splitlines() if line.startswith(f"| {CASE} |"))
    assert "2.0 s" in row and "20.0 s" in row


def test_effort_report_states_it_is_descriptive(sweep):
    md = report.render_effort_report(sweep, CC_PAIR, score=False)
    assert "no score or verdict" in md


def test_effort_report_file_name_per_suite():
    assert load_config().effort_report_name == "REPORT.effort.md"
    assert load_config(suite="real").effort_report_name == "REPORT.real.effort.md"


def test_report_main_by_effort_writes_its_own_file(sweep, tmp_path, monkeypatch):
    monkeypatch.setattr(report, "RUNS_DIR", tmp_path)      # report binds its own copy
    rc = report.main(["--pair", CC_PAIR, "--by-effort", "--no-score"])
    assert rc == 0
    assert (tmp_path / CC_PAIR / "REPORT.effort.md").exists()
    assert not (tmp_path / CC_PAIR / "REPORT.md").exists()       # main scorecard untouched


def test_measure_thinking_flag_turns_timing_on_for_this_run(monkeypatch):
    """No more editing models.yaml for an instrumented run."""
    seen = []
    monkeypatch.setattr(runner, "run_pair", lambda cfg, pid, **kw: seen.append(cfg.thinking_time) or [])
    runner.main(["--pair", CC_PAIR, "--role", "current", "--measure-thinking"])
    runner.main(["--pair", CC_PAIR, "--role", "current"])
    assert seen == [True, load_config().thinking_time]
