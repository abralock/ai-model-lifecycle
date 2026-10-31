"""tests/test_leaderboard.py — one leaderboard from every pair's runs.

leaderboard.py ranks models, not pairs: each model's answers are pooled across
every pair it ran in, from that pair's latest complete run for the model
(effort sweeps, one-sided smokes and infra-only runs left out). Answers made
under different settings (output limit, thinking request) are never pooled
into one row. Pass/fail comes from the shared score cache. Offline: run files
are written to a tmp RUNS_DIR and the scorer is faked.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import common
import leaderboard
import report
from common import load_config

SANITY = load_config()
REAL = load_config(suite="real")


def _write(pair, rid, slug, role, case, *, rep=0, ok=True, error=None, passed=True,
           latency=10.0, max_tokens=32000, reasoning=None, effort=None, name=None,
           provider="claude-code", cost=0.01, thinking=None):
    d = common.RUNS_DIR / pair
    d.mkdir(parents=True, exist_ok=True)
    rec = {"pair_id": pair, "case_id": case, "model_slug": slug, "model_name": name or slug,
           "role": role, "rep": rep, "run_id": rid, "ok": ok, "error": error,
           "output_text": ("PASS" if passed else "FAIL") if ok else "",
           "latency_s": latency, "max_tokens": max_tokens, "reasoning_requested": reasoning,
           "effort_override": effort, "provider": provider, "cost_estimate_usd": cost,
           "input_tokens": 10, "output_tokens": 10, "cache_read_tokens": 0,
           "cache_write_tokens": 0, "total_tokens": 20, "reasoning_tokens": 5}
    if thinking is not None and ok:
        rec["thinking_time_s"], rec["execution_time_s"] = thinking, 1.0
    suffix = f".r{rep}" if rep else ""
    (d / f"{slug.replace('/', '__')}.{case}.{rid}{suffix}.json").write_text(json.dumps(rec))


def _full_run(pair, rid, cur, tgt, cfg=SANITY, *, cur_passes=None, tgt_passes=None,
              tgt_infra=(), **kw):
    """Every case of the suite for both roles; *_passes = cases that pass."""
    for case in cfg.cases:
        _write(pair, rid, cur, "current", case,
               passed=cur_passes is None or case in cur_passes, **kw)
        if case in tgt_infra:
            _write(pair, rid, tgt, "target", case, ok=False, error="RateLimitError: 429", **kw)
        else:
            _write(pair, rid, tgt, "target", case,
                   passed=tgt_passes is None or case in tgt_passes, **kw)


@pytest.fixture
def runs(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(leaderboard.common, "RUNS_DIR", tmp_path)
    return tmp_path


def fake_scorer(case_id, output_text, slug):
    fake_scorer.calls += 1
    return SimpleNamespace(passed=output_text == "PASS", reason="" if output_text == "PASS" else "nope")


@pytest.fixture(autouse=True)
def _reset():
    fake_scorer.calls = 0


def _rows(cfg=SANITY):
    return {r.slug: r for r in leaderboard.suite_rows(cfg, score=True, scorer=fake_scorer)}


# --------------------------------------------------------------------------- #
# which answers count                                                          #
# --------------------------------------------------------------------------- #
def test_a_model_is_pooled_across_every_pair_it_ran_in(runs):
    _full_run("a-vs-opus", "20261020T000000Z", "a", "opus")      # opus as target
    _full_run("opus-vs-b", "20261021T000000Z", "opus", "b")      # opus as current
    rows = _rows()
    n = len(SANITY.cases)
    assert rows["opus"].agg.runs == 2 * n and rows["opus"].agg.passes == 2 * n
    assert rows["opus"].pairs == ["a-vs-opus", "opus-vs-b"]
    assert rows["a"].agg.runs == n


def test_effort_sweeps_and_one_sided_runs_are_left_out(runs):
    _full_run("opus-vs-b", "20261021T000000Z", "opus", "b")
    _full_run("opus-vs-b", "20261022T000000Z", "opus", "b", effort="high")       # sweep
    _write("opus-vs-b", "20261023T000000Z", "opus", "current", SANITY.cases[0])  # smoke
    rows = _rows()
    assert rows["opus"].runs == ["20261021T000000Z"]


def test_a_role_falls_back_to_its_last_run_with_real_answers(runs):
    """The Kimi case: a newer run is complete on paper, but the target's calls
    were nearly all infra errors — its older full run is the one that counts."""
    first = SANITY.cases[0]
    _full_run("opus-vs-kimi", "20261026T000000Z", "opus", "kimi",
              tgt_passes=set(SANITY.cases[:2]))
    _full_run("opus-vs-kimi", "20261030T000000Z", "opus", "kimi",
              tgt_infra=set(SANITY.cases) - {first})
    rows = _rows()
    assert rows["opus"].runs == ["20261030T000000Z"]      # current: newest full run
    assert rows["kimi"].runs == ["20261026T000000Z"]      # target: falls back
    assert rows["kimi"].agg.passes == 2 and rows["kimi"].agg.infra_errors == 0


def test_different_settings_are_never_pooled(runs):
    _full_run("opus-vs-b", "20261021T000000Z", "opus", "b", max_tokens=64000)
    _full_run("c-vs-opus", "20261022T000000Z", "c", "opus", max_tokens=128000)
    opus = [r for r in leaderboard.suite_rows(SANITY, score=True, scorer=fake_scorer)
            if r.slug == "opus"]
    assert len(opus) == 2
    assert {r.settings for r in opus} == {"max 64k", "max 128k"}


def test_infra_errors_are_excluded_and_not_scored(runs):
    _full_run("opus-vs-b", "20261021T000000Z", "opus", "b", tgt_infra={SANITY.cases[0]},
              tgt_passes=set(SANITY.cases))
    rows = _rows()
    n = len(SANITY.cases)
    assert rows["b"].agg.runs == n - 1 and rows["b"].agg.infra_errors == 1
    assert fake_scorer.calls == 2 * n - 1


def test_suites_are_kept_apart(runs):
    _full_run("opus-vs-b", "20261021T000000Z", "opus", "b")
    _full_run("opus-vs-b", "20261022T000000Z", "opus", "b", cfg=REAL, cur_passes=set())
    assert _rows(SANITY)["opus"].agg.passes == len(SANITY.cases)
    assert _rows(REAL)["opus"].agg.passes == 0


# --------------------------------------------------------------------------- #
# ranking and rendering                                                        #
# --------------------------------------------------------------------------- #
def test_ranking_uses_both_suites(runs):
    _full_run("x-vs-y", "20261021T000000Z", "x", "y", tgt_passes=set(SANITY.cases[:1]))
    _full_run("x-vs-y", "20261022T000000Z", "x", "y", cfg=REAL,
              cur_passes=set(), tgt_passes=set(REAL.cases))
    board = leaderboard.build(score=True, scorer=fake_scorer)
    order = [entry.slug for entry in board.ranking]
    # x: all sanity, no real; y: one sanity, all real. Pooled pass rate decides.
    total = {e.slug: (e.passes, e.scored) for e in board.ranking}
    assert total["x"] == (len(SANITY.cases), len(SANITY.cases) + len(REAL.cases))
    rate = {s: p / n for s, (p, n) in total.items()}
    assert order == sorted(rate, key=lambda s: -rate[s])


def test_render_has_ranking_suite_tables_and_caveats(runs):
    _full_run("opus-vs-b", "20261021T000000Z", "opus", "b", name="Claude Opus 5.5 (CC)")
    _full_run("opus-vs-b", "20261022T000000Z", "opus", "b", cfg=REAL,
              name="Claude Opus 5.5 (CC)", provider="opencode-go")
    md = leaderboard.render(leaderboard.build(score=True, scorer=fake_scorer))
    assert "# Gate 1 leaderboard" in md
    assert "## Single-shot ranking" in md and "## Single-shot: sanity suite" in md and "## Single-shot: real suite" in md
    assert "Claude Opus 5.5 (CC)" in md
    assert "| r1b_jhipster_boot3 |" not in md                 # cases are columns, not rows
    assert "r1b" in md and "Pass@300s" in md and "Pass@30s" in md
    assert "different days" in md                             # latency caveat
    assert "run 20261021T000000Z" in md and "run 20261022T000000Z" in md  # provenance


def test_cli_writes_one_file_and_touches_no_scorecard(runs, monkeypatch):
    _full_run("opus-vs-b", "20261021T000000Z", "opus", "b")
    monkeypatch.setattr(leaderboard, "ScoreCache", lambda: fake_scorer)
    assert leaderboard.main([]) == 0
    assert (runs / "LEADERBOARD.md").exists()
    assert not (runs / "opus-vs-b" / "REPORT.md").exists()


def test_aggregate_accepts_a_scorer():
    rec = {"case_id": "r3_oracle_to_postgres", "role": "x", "model_slug": "m", "ok": True,
           "output_text": "PASS", "latency_s": 1.0}
    a = report.aggregate([rec], score=True, scorer=fake_scorer)[("m", "x")]
    assert a.passes == 1 and fake_scorer.calls == 1


def test_models_missing_a_suite_rank_after_models_with_both(runs):
    """A sanity-only 100% must not outrank a model that also faced the much
    harder real suite (first live build: two sanity-only rows ranked #1-2)."""
    _full_run("easy-vs-x", "20261021T000000Z", "easy", "x")              # easy: sanity only
    _full_run("hard-vs-y", "20261021T000000Z", "hard", "y", tgt_passes=set())
    _full_run("hard-vs-y", "20261022T000000Z", "hard", "y", cfg=REAL,
              cur_passes=set(REAL.cases[:1]), tgt_passes=set())
    board = leaderboard.build(score=True, scorer=fake_scorer)
    order = [e.slug for e in board.ranking]
    assert order.index("hard") < order.index("easy")
    md = leaderboard.render(board)
    assert "sanity only" in md


def test_default_routes_are_claude_code_and_opencode_go(runs):
    _full_run("cc-vs-go", "20261021T000000Z", "cc-model", "go-model", provider="claude-code")
    for case in SANITY.cases:                       # the target answered on Go
        _write("cc-vs-go", "20261021T000000Z", "go-model", "target", case, provider="opencode-go")
    _full_run("or-pair", "20261021T000000Z", "or-a", "or-b", provider="Amazon Bedrock")
    default = {r.slug for r in leaderboard.build(score=True, scorer=fake_scorer).ranking}
    assert default == {"cc-model", "go-model"}
    everything = {r.slug for r in leaderboard.build(score=True, scorer=fake_scorer,
                                                    routes=None).ranking}
    assert everything == {"cc-model", "go-model", "or-a", "or-b"}


def test_a_role_keeps_its_route_through_infra_errors(runs):
    """Infra-error records carry no provider; they stay with their model."""
    _full_run("cc-vs-x", "20261021T000000Z", "cc-model", "x", provider="claude-code")
    _write("cc-vs-x", "20261021T000000Z", "cc-model", "current", SANITY.cases[0], rep=1,
           ok=False, error="claude -p error: Request timed out", provider=None)
    row = next(r for r in leaderboard.build(score=True, scorer=fake_scorer).rows["sanity"]
               if r.slug == "cc-model")
    assert row.agg.infra_errors == 1


def test_cli_routes_flag(runs, monkeypatch):
    _full_run("or-pair", "20261021T000000Z", "or-a", "or-b", provider="Amazon Bedrock")
    monkeypatch.setattr(leaderboard, "ScoreCache", lambda: fake_scorer)
    leaderboard.main([])
    assert "or-a" not in (runs / "LEADERBOARD.md").read_text()
    leaderboard.main(["--routes", "all", "--all-results"])
    assert "or-a" in (runs / "LEADERBOARD.md").read_text()



# --------------------------------------------------------------------------- #
# the team's policy: only results from the thinking-time harness on            #
# --------------------------------------------------------------------------- #
def test_since_and_measured_only_keep_just_the_new_harness_runs(runs):
    _full_run("old-pair", "20261021T000000Z", "old", "x")                       # before
    _full_run("new-pair", "20261030T000000Z", "plain", "y")                     # unmeasured
    _full_run("timed-pair", "20261030T120000Z", "timed", "z", thinking=5.0)     # measured
    board = leaderboard.build(score=True, scorer=fake_scorer,
                              since="20261030", measured_only=True)
    assert {e.slug for e in board.ranking} == {"timed", "z"}


def test_effort_sweeps_become_one_row_per_level(runs):
    for i, level in enumerate(["low", "medium", "high"]):
        for case in REAL.cases:
            _write("opus-vs-k", f"2026103{i}T000000Z", "opus", "current", case, effort=level,
                   max_tokens=128000, reasoning={"effort": level}, thinking=float(i + 1))
    rows = leaderboard.suite_rows(REAL, score=True, scorer=fake_scorer, include_effort=True,
                                  measured_only=True)
    assert sorted(r.settings for r in rows) == ["max 128k · effort high",
                                                "max 128k · effort low",
                                                "max 128k · effort medium"]
    board = leaderboard.build(score=True, scorer=fake_scorer, include_effort=True,
                              measured_only=True)
    names = {e.name for e in board.ranking}
    assert names == {"opus · effort low", "opus · effort medium", "opus · effort high"}


def test_effort_sweeps_stay_out_unless_asked(runs):
    for case in REAL.cases:
        _write("opus-vs-k", "20261031T000000Z", "opus", "current", case, effort="low")
    assert leaderboard.suite_rows(REAL, score=True, scorer=fake_scorer) == []


def test_docs_assisted_runs_never_count(runs):
    for case in REAL.cases:
        _write("opus-vs-k", "20261031T000000Z", "opus", "current", case, effort="low",
               thinking=1.0)
    d = common.RUNS_DIR / "opus-vs-k"
    for f in d.glob("*.json"):
        rec = json.loads(f.read_text())
        rec["docs_tool"] = "context7"
        f.write_text(json.dumps(rec))
    assert leaderboard.suite_rows(REAL, score=True, scorer=fake_scorer,
                                  include_effort=True) == []


def test_the_policy_lives_in_models_yaml_and_the_page_states_it(runs, monkeypatch):
    policy = leaderboard.policy()
    assert policy["since"] == "20261031T114732Z" and policy["single_shot"] is False
    assert policy["routes"] == ("claude-code", "opencode-go")
    _full_run("timed-pair", "20261030T120000Z", "timed", "z", thinking=5.0)
    _agentic("a-vs-b", "20261101T000000Z", "sonnet", REAL.cases[0])
    monkeypatch.setattr(leaderboard, "ScoreCache", lambda: fake_scorer)
    leaderboard.main([])
    md = (runs / "LEADERBOARD.md").read_text()
    assert "from run 20261031T114732Z on" in md and "agentic runs only" in md
    assert "| sonnet |" in md and "| timed |" not in md
    leaderboard.main(["--all-results"])                       # everything, single-shot too
    md = (runs / "LEADERBOARD.md").read_text()
    assert "# Single-shot screening" in md and "| timed |" in md


# --------------------------------------------------------------------------- #
# thinking level and measured thinking time on every result                    #
# --------------------------------------------------------------------------- #
def test_every_row_shows_its_thinking_level_and_time(runs):
    _full_run("p", "20261030T000000Z", "plain", "y", thinking=4.0)               # no effort sent
    for case in REAL.cases:
        _write("p", "20261031T000000Z", "plain", "current", case, max_tokens=128000,
               reasoning={"effort": "medium"}, thinking=20.0)
        _write("p", "20261031T000000Z", "y", "target", case, max_tokens=128000,
               reasoning={"effort": "medium"}, thinking=30.0)
    board = leaderboard.build(score=True, scorer=fake_scorer, measured_only=True)
    sanity = {r.slug: r for r in board.rows["sanity"]}
    real = {r.slug: r for r in board.rows["real"]}
    assert sanity["plain"].level == "model default"
    assert real["plain"].level == "medium"
    md = leaderboard.render(board)
    assert "Thinking level" in md and "Thinking (s)" in md
    ranking = next(line for line in md.splitlines() if line.startswith("| 1 | plain"))
    assert "sanity: model default · real: medium" in ranking
    sanity_row = next(line for line in md.split("## Single-shot: sanity suite")[1].splitlines()
                      if line.startswith("| 1 | plain"))
    assert "| model default |" in sanity_row and "| 4 |" in sanity_row


def test_a_model_that_did_not_answer_every_task_ranks_after_complete_ones(runs):
    """Kimi on Oct 30: r1 answered, r3-r5 hit the Go quota — 2/2 is not 100%."""
    first = SANITY.cases[0]
    _full_run("good", "20261030T000000Z", "solid", "x", cur_passes=set(SANITY.cases[:2]))
    _full_run("quota", "20261030T000000Z", "a", "kimi", tgt_infra=set(SANITY.cases) - {first})
    board = leaderboard.build(score=True, scorer=fake_scorer)
    order = [e.slug for e in board.ranking]
    assert order.index("solid") < order.index("kimi")
    md = leaderboard.render(board)
    assert "partial" in next(line for line in md.splitlines() if "| kimi" in line)


# --------------------------------------------------------------------------- #
# one table per task, sanity and real                                          #
# --------------------------------------------------------------------------- #
def test_every_task_gets_its_own_table_with_its_own_numbers(runs):
    r1, r3 = SANITY.cases[0], SANITY.cases[1]
    for case in SANITY.cases:
        _write("p", "20261030T000000Z", "opus", "current", case,
               passed=case != r3, latency=10.0 if case == r1 else 50.0,
               thinking=2.0 if case == r1 else 30.0)
        _write("p", "20261030T000000Z", "kimi", "target", case, thinking=9.0)
    board = leaderboard.build(score=True, scorer=fake_scorer, measured_only=True)
    md = leaderboard.render(board)
    for case in SANITY.cases + REAL.cases:
        assert f"### {case}" in md                       # a section per task, both suites
    r1_table = md.split(f"### {r1}")[1].split("### ")[0]
    r3_table = md.split(f"### {r3}")[1].split("### ")[0]
    opus_r1 = next(line for line in r1_table.splitlines() if "| opus |" in line)
    opus_r3 = next(line for line in r3_table.splitlines() if "| opus |" in line)
    assert "| 1/1 |" in opus_r1 and "| 10 |" in opus_r1 and "| 2 |" in opus_r1
    assert "| 0/1 |" in opus_r3 and "| 50 |" in opus_r3 and "| 30 |" in opus_r3
    # on r3 kimi passed and opus did not: per-task order follows that task's results
    assert r3_table.index("| kimi |") < r3_table.index("| opus |")


def test_per_task_tables_do_not_score_any_answer_twice(runs):
    _full_run("p", "20261030T000000Z", "opus", "kimi")
    leaderboard.build(score=True, scorer=fake_scorer)
    assert fake_scorer.calls == 2 * len(SANITY.cases)


# --------------------------------------------------------------------------- #
# "After repair": repair.py results beside — never inside — the pass rate      #
# --------------------------------------------------------------------------- #
def _repair(pair, rid, slug, case, rep, rounds_passed, *, failed_call=False,
            latency=5.0, cost=0.2):
    """Write repair.py round records; rounds_passed like [False, True].
    failed_call: the repair call itself errored (e.g. a usage limit)."""
    d = common.RUNS_DIR / pair / "repair" / rid
    d.mkdir(parents=True, exist_ok=True)
    suffix = f".r{rep}" if rep else ""
    for i, ok in enumerate(rounds_passed, 1):
        (d / f"{slug}.{case}.{rid}{suffix}.round{i}.json").write_text(json.dumps(
            {"case_id": case, "model_slug": slug, "rep": rep, "round": i, "passed": ok,
             "repair_output": "" if failed_call else "### EDIT: x",
             "latency_s": latency, "cost_estimate_usd": cost,
             "error": "claude -p error (api_error_status=429): limit" if failed_call else None}))


def test_after_repair_counts_single_shot_passes_plus_repaired_answers(runs):
    case = REAL.cases[0]
    for rep in range(3):
        for c in REAL.cases:
            _write("p", "20261030T000000Z", "opus", "current", c, rep=rep,
                   passed=(c != case), max_tokens=128000, thinking=5.0)
    _repair("p", "20261030T000000Z", "opus", case, 0, [False, True])      # repaired
    _repair("p", "20261030T000000Z", "opus", case, 1, [False, False, False])  # still fails
    # rep 2: never repaired
    rows = leaderboard.suite_rows(REAL, score=True, scorer=fake_scorer, measured_only=True)
    opus = rows[0]
    assert opus.agg.passes == 3                                   # single-shot untouched
    assert opus.repair_by_case[case] == (1, 3, 2)                 # 1/3 after 2 repaired
    md = leaderboard.render(leaderboard.build(score=True, scorer=fake_scorer,
                                              measured_only=True))
    table = md.split(f"### {case}")[1].split("### ")[0]
    assert "After repair" in table
    row = next(line for line in table.splitlines() if "| opus |" in line)
    assert "| 0/3 |" in row and "1/3 pass (2 tried)" in row
    other = md.split(f"### {REAL.cases[1]}")[1].split("##")[0]
    assert "— |" in next(line for line in other.splitlines() if "| opus |" in line)


def test_task_tables_name_the_run_not_the_pair_folder(runs):
    """A leaderboard row is one model's own answers; the pair folder they are
    stored in is not a comparison and is not shown."""
    for c in REAL.cases:
        _write("haiku-vs-glm", "20261031T040335Z", "haiku", "current", c, thinking=5.0)
    md = leaderboard.render(leaderboard.build(score=True, scorer=fake_scorer,
                                              measured_only=True))
    row = next(line for line in md.split("## Single-shot: real suite")[1].splitlines() if "| haiku |" in line)
    assert row.endswith("| Oct 31 · run 20261031T040335Z |")
    assert "haiku-vs-glm" not in md.split("## Single-shot ranking")[1]


def test_time_and_cost_to_pass_after_repair(runs):
    """For answers that repair got to pass: the model time and cost of the
    first answer plus every repair round up to the passing one."""
    case = REAL.cases[0]
    for rep in range(3):
        for c in REAL.cases:
            _write("p", "20261030T000000Z", "opus", "current", c, rep=rep, passed=False,
                   max_tokens=128000, thinking=5.0, latency=100.0, cost=1.0)
    _repair("p", "20261030T000000Z", "opus", case, 0, [False, True])             # 110 s, $1.40
    _repair("p", "20261030T000000Z", "opus", case, 1, [False, False, True],
            latency=10.0, cost=0.1)                                              # 130 s, $1.30
    _repair("p", "20261030T000000Z", "opus", case, 2, [False, False])            # never passes
    rows = leaderboard.suite_rows(REAL, score=True, scorer=fake_scorer, measured_only=True)
    time_s, cost = rows[0].repair_to_pass[case]
    assert time_s == pytest.approx(120.0) and cost == pytest.approx(1.35)
    md = leaderboard.render(leaderboard.build(score=True, scorer=fake_scorer,
                                              measured_only=True))
    table = md.split(f"### {case}")[1].split("### ")[0]
    assert "Time to pass after repair (s)" in table and "Cost to pass after repair" in table
    row = next(line for line in table.splitlines() if "| opus |" in line)
    assert "| 120 |" in row and "| $1.350 |" in row
    other = md.split(f"### {REAL.cases[1]}")[1].split("##")[0]
    assert "| — | — | — |" in next(line for line in other.splitlines() if "| opus |" in line)


def test_repair_rounds_never_change_the_ranking(runs):
    case = REAL.cases[0]
    for c in REAL.cases:
        _write("p", "20261030T000000Z", "opus", "current", c, passed=False, thinking=5.0)
    _repair("p", "20261030T000000Z", "opus", case, 0, [True])
    board = leaderboard.build(score=True, scorer=fake_scorer, measured_only=True)
    assert board.ranking[0].passes == 0



def test_a_repair_call_that_failed_is_not_a_repair_attempt(runs):
    """A repair call that hit a usage limit produced no answer: it says nothing
    about whether the model can repair, so it is not counted as tried."""
    case = REAL.cases[0]
    for c in REAL.cases:
        _write("p", "20261030T000000Z", "opus", "current", c, passed=False, thinking=5.0)
    _repair("p", "20261030T000000Z", "opus", case, 0, [False], failed_call=True)
    rows = leaderboard.suite_rows(REAL, score=True, scorer=fake_scorer, measured_only=True)
    assert case not in rows[0].repair_by_case


# --------------------------------------------------------------------------- #
# Agentic migration: the primary result                                        #
# --------------------------------------------------------------------------- #
def _agentic(pair, rid, slug, case, rep=0, *, passed=True, ok=True, minutes=20.0, cost=2.0,
             effort="medium", name=None, tool_s=None, api_s=None):
    d = common.RUNS_DIR / pair / "agentic" / rid
    d.mkdir(parents=True, exist_ok=True)
    rec = {"mode": "agentic", "pair_id": pair, "case_id": case, "model_slug": slug,
           "model_name": name or slug, "rep": rep, "run_id": rid, "ok": ok,
           "passed": passed if ok else None, "output_text": "PASS" if passed else "FAIL",
           "latency_s": minutes * 60, "cost_estimate_usd": cost, "num_turns": 30,
           "effort_override": effort, "tool_time_s": tool_s,
           "duration_api_ms": None if api_s is None else api_s * 1000}
    (d / f"{slug}.{case}.{rid}{f'.r{rep}' if rep else ''}.json").write_text(json.dumps(rec))
    (d / f"{slug}.{case}.{rid}.stream.jsonl").write_text("{}\n")      # never read as a record


def test_agentic_results_come_first_and_rank_by_tasks_tried_then_pass_rate(runs):
    r1b = REAL.cases[0]
    for case in [*SANITY.cases, *REAL.cases]:
        _agentic("a-vs-b", "20261101T000000Z", "sonnet", case, passed=True)
    _agentic("c-vs-d", "20261101T000000Z", "opus", r1b, passed=True)
    _agentic("c-vs-d", "20261101T000000Z", "opus", r1b, rep=1, passed=False)
    _agentic("c-vs-d", "20261101T000000Z", "opus", r1b, rep=2, ok=False)    # infra: excluded
    board = leaderboard.build(score=True, scorer=fake_scorer)
    assert [r.slug for r in board.agentic] == ["sonnet", "opus"]
    opus = board.agentic[1]
    assert (opus.by_case[r1b].passes, opus.by_case[r1b].attempts) == (1, 2) and opus.infra == 1
    md = leaderboard.render(board)
    assert md.index("# Agentic migration (primary result)") < md.index("# Single-shot screening")
    ranking = md.split("# Agentic migration")[1].split("### ")[0]
    sonnet = next(line for line in ranking.splitlines() if "| sonnet |" in line)
    n_sanity, n_real = len(SANITY.cases), len(REAL.cases)
    assert (f"| {n_sanity}/{n_sanity} | {n_real}/{n_real} | 100% "
            f"({n_sanity + n_real}/{n_sanity + n_real}) |") in sonnet
    opus = next(line for line in ranking.splitlines() if "| opus |" in line)
    assert "| — | 1/2 |" in opus
    table = md.split(f"### {r1b}")[1].split("### ")[0]
    row = next(line for line in table.splitlines() if "| opus |" in line)
    assert "| 1/2 | 50% | 20.0 | 20.0 |" in row and "| $2.00 | $4.00 | 30 |" in row


def test_agentic_pass_fail_comes_from_the_scorer_not_the_record(runs):
    """A scorer fix (e.g. a too-strict hidden test) reaches old attempts too."""
    _agentic("a-vs-b", "20261101T000000Z", "sonnet", REAL.cases[0], passed=False)
    rows = leaderboard.agentic_rows(REAL.cases, score=True,
                                    scorer=lambda c, t, s: SimpleNamespace(passed=True))
    assert rows[0].by_case[REAL.cases[0]].passes == 1


def test_no_agentic_runs_says_how_to_start_one(runs):
    _full_run("p", "20261030T000000Z", "opus", "kimi")
    md = leaderboard.render(leaderboard.build(score=True, scorer=fake_scorer))
    assert "_No agentic runs yet" in md and "agentic.py" in md


def test_policy_agentic_only_from_a_run_id_on(runs, monkeypatch):
    """models.yaml leaderboard: single_shot false + since <run id>: the board
    starts over with agentic runs; older runs stay on disk."""
    _full_run("p", "20261031T000000Z", "opus", "kimi")                    # single-shot
    _agentic("a-vs-b", "20261031T100000Z", "sonnet", REAL.cases[0])        # before the start
    _agentic("a-vs-b", "20261031T114732Z", "haiku", REAL.cases[0])
    board = leaderboard.build(score=True, scorer=fake_scorer, since="20261031T114732Z",
                              single_shot=False)
    assert [r.slug for r in board.agentic] == ["haiku"] and board.ranking == []
    md = leaderboard.render(board)
    assert "# Single-shot screening" not in md and "agentic runs only" in md
    assert "from run 20261031T114732Z on" in md


def test_agentic_ttfs_pass_at_t_and_tool_model_ratio(runs):
    """docs/METRICS_PLAN.md §8: the plan's metrics for agentic attempts, with
    agentic budgets (real: 900/1800/3600 s)."""
    r1b = REAL.cases[0]
    _agentic("p", "20261101T000000Z", "sonnet", r1b, 0, passed=True, minutes=15,
             tool_s=600, api_s=200)
    _agentic("p", "20261101T000000Z", "sonnet", r1b, 1, passed=True, minutes=30,   # 1800 s: inclusive
             tool_s=1200, api_s=400)
    _agentic("p", "20261101T000000Z", "sonnet", r1b, 2, passed=False, minutes=50)  # unmeasured
    board = leaderboard.build(score=True, scorer=fake_scorer)
    t = board.agentic[0].by_case[r1b]
    assert t.ttfs_s == 22.5 * 60                                   # passing attempts only
    assert [t.pass_at(b) for b in (900, 1800, 3600)] == [1 / 3, 2 / 3, 2 / 3]
    assert t.tool_model_ratio == 3.0                               # (600+1200)/(200+400)
    md = leaderboard.render(board)
    table = md.split(f"### {r1b}")[1].split("### ")[0]
    assert "Pass@900s | Pass@1800s | Pass@3600s | Tool / model time" in table
    row = next(line for line in table.splitlines() if "| sonnet |" in line)
    assert "| 2/3 | 67% | 31.7 | 22.5 | 33% | 67% | 67% | 3.00 |" in row
    _agentic("p", "20261102T000000Z", "sonnet", SANITY.cases[0])          # another run, task
    md = leaderboard.render(leaderboard.build(score=True, scorer=fake_scorer))
    row = next(line for line in md.split(f"### {r1b}")[1].splitlines() if "| sonnet |" in line)
    assert row.endswith("| 20261101T000000Z |")                      # only this task's run


def test_agentic_metrics_are_na_without_a_pass_or_a_measurement(runs):
    _agentic("p", "20261101T000000Z", "haiku", SANITY.cases[0], passed=False, minutes=2)
    md = leaderboard.render(leaderboard.build(score=True, scorer=fake_scorer))
    row = next(line for line in md.split(f"### {SANITY.cases[0]}")[1].splitlines()
               if "| haiku |" in line)
    assert "| 0/1 | 0% | 2.0 | n/a | 0% | 0% | 0% | n/a |" in row


def test_equal_pass_rates_rank_by_time_then_cost_not_name(runs):
    """2026-11-01: with every model at 100%, the ranking fell back to the
    alphabet. Time decides, then cost."""
    for case in [*SANITY.cases, *REAL.cases]:
        _agentic("p", "20261101T000000Z", "aaa-slow", case, minutes=30, cost=1.0)
        _agentic("p", "20261101T000000Z", "bbb-fast-dear", case, minutes=10, cost=5.0)
        _agentic("p", "20261101T000000Z", "ccc-fast-cheap", case, minutes=10, cost=2.0)
    board = leaderboard.build(score=True, scorer=fake_scorer)
    assert [r.slug for r in board.agentic] == ["ccc-fast-cheap", "bbb-fast-dear", "aaa-slow"]
    n = len(SANITY.cases) + len(REAL.cases)
    md = leaderboard.render(board)
    row = next(line for line in md.split("## Ranking")[1].splitlines() if "| ccc-fast-cheap |" in line)
    assert row.endswith(f"| {10 * n:.1f} | ${2.0 * n:.2f} |")
    table = md.split(f"### {REAL.cases[0]}")[1].split("### ")[0]
    order = [s for s in ("ccc-fast-cheap", "bbb-fast-dear", "aaa-slow") if f"| {s} |" in table]
    assert [line.split("|")[2].strip() for line in table.splitlines()
            if line.startswith("| ") and line.split("|")[2].strip() in order] == order
