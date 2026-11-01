"""leaderboard.py — rank models, not pairs.

Every pair's runs already record which model answered, so a model's answers
can be pooled across every pair it ran in: Opus 5.5 run against GLM, Qwen and
Kimi is one model with three runs' worth of answers. For each pair and role,
the answers come from the latest run of the suite in which that role answered
every case; a run whose answers were nearly all infra errors gives way to an
older one with real answers. Effort sweeps (runner.py --effort), one-sided
smoke runs and repair rounds are left out, and answers made under different
settings (output limit, thinking request) are never pooled into one row.

Which results count is the team's policy in models.yaml `leaderboard:` (a
start date, measured-thinking runs only, effort sweeps as one row per level,
the Claude Code and OpenCode Go routes); `--all-results` ranks every plain run.

Pass/fail comes from the scorers through the shared score cache
(score_cache.py), so the first build scores every answer once and later builds
are instant. Writes runs/LEADERBOARD.md.

    python leaderboard.py
    python leaderboard.py --no-score     # runner ok-flag, not task correctness
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from typing import Any

import yaml

import common
import report
from common import REPO_ROOT, load_config, load_env, load_runs
from report import (ModelAgg, _timing_value, aggregate, is_effort_run, is_infra_error,
                    reasoning_level)
from score_cache import ScoreCache
from scorers.dispatch import score_case

SUITES = ("sanity", "real")
CASE_TITLES = {
    "r1_springboot2to3": "Spring Boot 2 → 3 (small app)",
    "r3_oracle_to_postgres": "Oracle → PostgreSQL procedures",
    "r4_schema_load_optimize": "Schema load + query optimization",
    "r5_etl_dashboard": "ETL job + dashboard schema",
    "r1b_jhipster_boot3": "JHipster app → Spring Boot 3 / Java 17",
    "r2_gwt_to_angular": "GWT → Angular port",
}
# Routes ranked by default; OpenRouter is out of scope for now (docs/METRICS_PLAN.md).
DEFAULT_ROUTES = ("claude-code", "opencode-go")
ROUTE_NAMES = {"claude-code": "Claude Code", "opencode-go": "OpenCode Go",
               "openrouter": "OpenRouter"}


@dataclass
class Row:
    """One model under one set of settings in one suite."""
    slug: str
    name: str
    settings: str
    route: str
    agg: ModelAgg
    pairs: list[str]
    runs: list[str]
    variant: str | None = None      # effort-sweep level (runner.py --effort), else None
    level: str = "model default"    # thinking level the answers were made at
    limit: str = ""                 # output limit, e.g. "max 128k"
    partial: bool = False           # some task of the suite has no answered call
    by_case: dict[str, ModelAgg] = field(default_factory=dict)   # task -> metrics
    # task -> (passes after repair, scored answers, answers repaired) — repair.py
    # results shown beside the pass rate, never inside it
    repair_by_case: dict[str, tuple[int, int, int]] = field(default_factory=dict)
    # task -> (mean model time s, mean cost USD) to pass, over answers repair
    # got to pass: the first answer plus every round up to the passing one
    repair_to_pass: dict[str, tuple[float, float]] = field(default_factory=dict)


@dataclass
class Entry:
    """One model in the overall ranking (both suites, all its settings)."""
    slug: str
    name: str
    variant: str | None = None
    passes: int = 0
    scored: int = 0
    by_suite: dict[str, tuple[int, int]] = field(default_factory=dict)
    levels: dict[str, str] = field(default_factory=dict)     # suite -> thinking level
    mixed_settings: bool = False
    partial: bool = False

    @property
    def rate(self) -> float:
        return self.passes / self.scored if self.scored else 0.0

    @property
    def complete(self) -> bool:
        """Scored in every suite: only these are ranked against each other."""
        return all(self.by_suite.get(s, (0, 0))[1] for s in SUITES)


@dataclass
class Board:
    rows: dict[str, list[Row]]
    ranking: list[Entry]
    budgets: dict[str, list[float]]
    cases: dict[str, list[str]]
    score: bool
    routes: tuple[str, ...] | None = DEFAULT_ROUTES
    since: str | None = None
    measured_only: bool = False
    include_effort: bool = False
    agentic: list["AgenticRow"] = field(default_factory=list)
    single_shot: bool = True            # False: agentic only (models.yaml leaderboard policy)
    agentic_budgets: dict[str, list[float]] = field(default_factory=dict)


@dataclass
class AgenticTask:
    """One model's agentic attempts on one task (docs/METRICS_PLAN.md §8)."""
    outcomes: list[tuple[float, bool]] = field(default_factory=list)  # (wall s, passed)
    cost_usd: float = 0.0
    turns: float = 0.0
    tool_s: float = 0.0             # tool time over the attempts measuring both
    model_s: float = 0.0            # model (API) time over the same attempts
    timed: int = 0
    runs: set[str] = field(default_factory=set)     # the runs these attempts came from

    @property
    def attempts(self) -> int:
        return len(self.outcomes)

    @property
    def passes(self) -> int:
        return sum(1 for _, ok in self.outcomes if ok)

    @property
    def rate(self) -> float:
        return self.passes / self.attempts if self.attempts else 0.0

    @property
    def mean_time_s(self) -> float:
        return sum(t for t, _ in self.outcomes) / self.attempts

    @property
    def ttfs_s(self) -> float | None:
        """Mean wall time of the passing attempts; None without a pass."""
        times = [t for t, ok in self.outcomes if ok]
        return sum(times) / len(times) if times else None

    def pass_at(self, budget_s: float) -> float:
        """Share of attempts that passed within the budget (inclusive)."""
        return sum(1 for t, ok in self.outcomes if ok and t <= budget_s) / self.attempts

    @property
    def tool_model_ratio(self) -> float | None:
        """Tool time / model time, a ratio of sums over attempts measuring both."""
        return self.tool_s / self.model_s if self.timed and self.model_s > 0 else None


@dataclass
class AgenticRow:
    """One model at one effort level, from its agentic attempts (agentic.py)."""
    slug: str
    name: str
    level: str
    by_case: dict[str, AgenticTask] = field(default_factory=dict)
    infra: int = 0
    runs: list[str] = field(default_factory=list)
    agent: str = "claude-code"          # claude-code | opencode

    @property
    def passes(self) -> int:
        return sum(t.passes for t in self.by_case.values())

    @property
    def attempts(self) -> int:
        return sum(t.attempts for t in self.by_case.values())

    @property
    def rate(self) -> float:
        return self.passes / self.attempts if self.attempts else 0.0

    @property
    def time_s(self) -> float:
        """Sum over tasks of the mean attempt time: one full pass through the tasks."""
        return sum(t.mean_time_s for t in self.by_case.values())

    @property
    def cost_usd(self) -> float:
        """Sum over tasks of the mean attempt cost."""
        return sum(t.cost_usd / t.attempts for t in self.by_case.values())


def agentic_rows(cases: list[str], *, score: bool, scorer=None,
                 since: str | None = None) -> list[AgenticRow]:
    """Every agentic attempt (runs/<pair>/agentic/<run>/), pooled per model and
    effort level across pairs and runs. A session that never ran is an infra
    error and left out; pass/fail comes from the scorer (score cache) so a
    scorer fix reaches old attempts too."""
    pooled: dict[tuple[str, str, str], list[dict]] = {}
    root = Path(common.RUNS_DIR)
    for f in sorted(root.glob("*/agentic/*/*.json")):
        rid = f.parent.name
        if since and rid < since:
            continue
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec.get("mode") != "agentic":
            continue
        level = rec.get("effort_override") or "model default"
        # records from before the opencode backend carry no agent: Claude Code
        agent = rec.get("agent") or "claude-code"
        pooled.setdefault((rec.get("model_slug", "?"), level, agent), []).append({**rec, "_run": rid})
    rows = []
    for (slug, level, agent), recs in pooled.items():
        names = Counter(r.get("model_name") or slug for r in recs)
        name = names.most_common(1)[0][0]
        row = AgenticRow(slug=slug, name=name if agent == "claude-code" else f"{name} · {agent}",
                         level=level, runs=sorted({r["_run"] for r in recs}), agent=agent)
        for case in cases:
            ran = [r for r in recs if r.get("case_id") == case and r.get("ok")]
            row.infra += sum(1 for r in recs if r.get("case_id") == case and not r.get("ok"))
            if not ran:
                continue
            task = row.by_case[case] = AgenticTask()
            for r in ran:
                ok = (bool((scorer or score_case)(case, r.get("output_text") or "", slug).passed)
                      if score else bool(r.get("passed")))
                task.outcomes.append((float(r.get("latency_s") or 0), ok))
                task.runs.add(r["_run"])
                task.cost_usd += float(r.get("cost_estimate_usd") or 0)
                task.turns += float(r.get("num_turns") or 0)
                tool, api_ms = _timing_value(r.get("tool_time_s")), r.get("duration_api_ms")
                if tool is not None and isinstance(api_ms, (int, float)) and api_ms > 0:
                    task.tool_s += tool
                    task.model_s += api_ms / 1000
                    task.timed += 1
        if row.by_case:                 # only infra errors: nothing to rank
            rows.append(row)
    # equal pass rates (e.g. every model at 100%) are decided by time, then
    # cost, never by name
    rows.sort(key=lambda r: (-len(r.by_case), -r.rate, r.time_s, r.cost_usd, r.name))
    return rows


def _cfg(suite: str):
    return load_config(suite=None if suite == "sanity" else suite)


def _complete(cfg, recs: list[dict], role: str, *, answered: bool) -> bool:
    """Every case of the suite has a record for `role` (with `answered`: a
    record that is not an infra error)."""
    have = {r.get("case_id") for r in recs
            if r.get("role") == role and not (answered and is_infra_error(r))}
    return set(cfg.cases) <= have


def _measured(recs: list[dict]) -> bool:
    """Every answered call has measured stream phases (thinking_time: true)."""
    answered = [r for r in recs if not is_infra_error(r)]
    return bool(answered) and all(
        _timing_value(r.get("thinking_time_s")) is not None
        or _timing_value(r.get("execution_time_s")) is not None for r in answered)


def selected_runs(cfg, pair_id: str, *, include_effort: bool = False, since: str | None = None,
                  measured_only: bool = False) -> dict[tuple[str, str | None], tuple[str, list[dict]]]:
    """(role, effort variant) -> (run id, that role's records of the suite's
    cases): the latest run in which the role answered every case, else the
    latest in which it has a record for every case. Docs-assisted runs never
    count; effort sweeps only with `include_effort`, one selection per level."""
    candidates = []
    for rid in reversed(report.suite_run_ids(cfg, pair_id)):       # newest first
        if since and rid < since:
            continue
        recs = load_runs(pair_id, run=rid)
        if any(r.get("docs_tool") for r in recs):
            continue
        if is_effort_run(recs) and not include_effort:
            continue
        candidates.append((rid, recs))
    variants = {r.get("effort_override") for _, recs in candidates for r in recs}
    chosen: dict[tuple[str, str | None], tuple[str, list[dict]]] = {}
    for role in ("current", "target"):
        for variant in variants:
            group = [(rid, [r for r in recs if r.get("role") == role
                            and r.get("effort_override") == variant
                            and r.get("case_id") in cfg.cases])
                     for rid, recs in candidates]
            group = [(rid, rs) for rid, rs in group if rs and (not measured_only or _measured(rs))]
            complete = [g for g in group if _complete(cfg, g[1], role, answered=False)]
            answered = [g for g in complete if _complete(cfg, g[1], role, answered=True)]
            if pick := (answered or complete or [None])[0]:
                chosen[(role, variant)] = pick
    return chosen


def _settings(rec: dict) -> str:
    parts = []
    if isinstance(rec.get("max_tokens"), int):
        parts.append(f"max {rec['max_tokens'] // 1000}k")
    req = rec.get("reasoning_requested")
    if isinstance(req, dict):
        if req.get("effort"):
            parts.append(f"effort {req['effort']}")
        elif req.get("max_tokens"):
            parts.append(f"thinking ≤{int(req['max_tokens']) // 1000}k")
    return " · ".join(parts) or "default"


def _level(recs: list[dict]) -> str:
    """The thinking level a row's answers were made at: the effort sent (or
    budget), "model default" when none was sent."""
    levels = {reasoning_level(r) for r in recs if not is_infra_error(r)} or {"not recorded"}
    if len(levels) > 1:
        return "mixed"
    level = levels.pop()
    return "model default" if level == "not recorded" else level


def _call_cost(rec: dict) -> float:
    """A call's cost on the same basis as report.aggregate: a positive billed
    amount, else the estimate."""
    billed, estimate = rec.get("billed_cost_usd"), rec.get("cost_estimate_usd")
    if isinstance(billed, (int, float)) and billed > 0:
        return float(billed)
    return float(estimate) if isinstance(estimate, (int, float)) else 0.0


def _repaired(rec: dict) -> tuple[bool, float, float] | None:
    """Whether repair.py got a failed answer to pass (any round), with the
    model time and cost from the first answer through the passing round (or
    every round when none passed); None if it was never repaired."""
    rep = int(rec.get("rep", 0) or 0)
    name = (f"{rec.get('model_slug', '?').replace('/', '__')}.{rec.get('case_id')}."
            f"{rec['_run']}{f'.r{rep}' if rep else ''}.round*.json")
    rounds = [json.loads(f.read_text()) for f in
              sorted((Path(common.RUNS_DIR) / rec["_pair"] / "repair" / rec["_run"]).glob(name))]
    # a round whose repair call itself failed (no answer, e.g. a usage limit)
    # is not a repair attempt
    rounds = [r for r in rounds if (r.get("repair_output") or "").strip()]
    if not rounds:
        return None
    rounds.sort(key=lambda r: int(r.get("round", 0) or 0))
    time_s, cost = float(rec.get("latency_s") or 0.0), _call_cost(rec)
    for r in rounds:
        time_s += float(r.get("latency_s") or 0.0)
        cost += _call_cost(r)
        if r.get("passed"):
            return True, time_s, cost
    return False, time_s, cost


def _route_key(provider: str | None) -> str | None:
    if not provider:
        return None
    if provider == "claude-code":
        return "claude-code"
    if provider.startswith("opencode-go"):
        return "opencode-go"
    return "openrouter"


def _selection_route(recs: list[dict]) -> str | None:
    """The route a role's answers came from. Infra-error records carry no
    provider, so they follow the route of the role's answered calls."""
    keys = Counter(k for r in recs if (k := _route_key(r.get("provider"))))
    return keys.most_common(1)[0][0] if keys else None


def _route(provider: str | None) -> str:
    if provider == "claude-code":
        return "Claude Code"
    if (provider or "").startswith("opencode-go"):
        return "OpenCode Go"
    return f"OpenRouter ({provider})" if provider else "not recorded"


def _pair_dirs() -> list[str]:
    root = Path(common.RUNS_DIR)
    return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def suite_rows(cfg, *, score: bool, scorer=None,
               routes: tuple[str, ...] | None = DEFAULT_ROUTES, include_effort: bool = False,
               since: str | None = None, measured_only: bool = False) -> list[Row]:
    """One row per (model, settings) for this suite, best pass rate first.
    `routes` (route keys; None = every route) filters which answers count."""
    pooled: dict[tuple[str, str], list[dict]] = {}
    for pair_id in _pair_dirs():
        for rid, recs in selected_runs(cfg, pair_id, include_effort=include_effort, since=since,
                                       measured_only=measured_only).values():
            if routes is not None and _selection_route(recs) not in routes:
                continue
            for rec in recs:
                key = (rec.get("model_slug", "?"), _settings(rec))
                pooled.setdefault(key, []).append(
                    {**rec, "role": "pooled", "_pair": pair_id, "_run": rid})
    # Each answer is scored once per build, though it feeds both its row and
    # its task's table.
    memo: dict[tuple[str, str, str], Any] = {}

    def once(case_id, output_text, slug):
        key = (case_id, output_text, slug)
        if key not in memo:
            memo[key] = (scorer or score_case)(case_id, output_text, slug)
        return memo[key]

    rows = []
    for (slug, settings), recs in pooled.items():
        agg = next(iter(aggregate(recs, score=score, scorer=once).values()))
        by_case, repair_by_case, repair_to_pass = {}, {}, {}
        for case in cfg.cases:
            mine = [r for r in recs if r.get("case_id") == case]
            if mine:
                by_case[case] = next(iter(aggregate(mine, score=score, scorer=once).values()))
            after = tried = scored = 0
            to_pass: list[tuple[float, float]] = []
            for rec in mine:
                if is_infra_error(rec):
                    continue
                scored += 1
                single = (bool(once(case, rec.get("output_text", "") or "", slug).passed)
                          if score else bool(rec.get("ok")))
                if single:
                    after += 1
                elif (repair := _repaired(rec)) is not None:
                    tried += 1
                    if repair[0]:
                        after += 1
                        to_pass.append(repair[1:])
            if tried:
                repair_by_case[case] = (after, scored, tried)
            if to_pass:
                repair_to_pass[case] = (sum(t for t, _ in to_pass) / len(to_pass),
                                        sum(c for _, c in to_pass) / len(to_pass))
        names = Counter(r.get("model_name") or slug for r in recs)
        routes = sorted({_route(r.get("provider")) for r in recs if not is_infra_error(r)}
                        or {_route(None)})
        rows.append(Row(slug=slug, name=names.most_common(1)[0][0], settings=settings,
                        route=", ".join(routes), agg=agg,
                        pairs=sorted({r["_pair"] for r in recs}),
                        runs=sorted({r["_run"] for r in recs}),
                        variant=recs[0].get("effort_override"), level=_level(recs),
                        limit=(f"max {recs[0]['max_tokens'] // 1000}k"
                               if isinstance(recs[0].get("max_tokens"), int) else "—"),
                        partial=not set(cfg.cases) <= {r.get("case_id") for r in recs
                                                       if not is_infra_error(r)},
                        by_case=by_case, repair_by_case=repair_by_case,
                        repair_to_pass=repair_to_pass))
    rows.sort(key=lambda r: (-r.agg.pass_rate, -r.agg.passes, r.name))
    return rows


def build(*, score: bool = True, scorer=None, routes: tuple[str, ...] | None = DEFAULT_ROUTES,
          include_effort: bool = False, since: str | None = None,
          measured_only: bool = False, single_shot: bool = True) -> Board:
    rows, budgets, cases, agentic_budgets = {}, {}, {}, {}
    for suite in SUITES:
        cfg = _cfg(suite)
        budgets[suite], cases[suite] = cfg.time_budgets_s, list(cfg.cases)
        agentic_budgets[suite] = cfg.agentic_time_budgets_s
        if not single_shot:
            rows[suite] = []
            continue
        rows[suite] = suite_rows(cfg, score=score, scorer=scorer, routes=routes,
                                 include_effort=include_effort, since=since,
                                 measured_only=measured_only)
        budgets[suite], cases[suite] = cfg.time_budgets_s, list(cfg.cases)
    # one ranking entry per model and effort-sweep level; plain runs pool
    # across suites (their suite settings differ by design)
    entries: dict[tuple[str, str | None], Entry] = {}
    for suite, suite_list in rows.items():
        for row in suite_list:
            name = f"{row.name} · effort {row.variant}" if row.variant else row.name
            e = entries.setdefault((row.slug, row.variant),
                                   Entry(slug=row.slug, name=name, variant=row.variant))
            p, n = e.by_suite.get(suite, (0, 0))
            if n:
                e.mixed_settings = True
            e.levels[suite] = row.level if suite not in e.levels else "mixed"
            e.partial = e.partial or row.partial
            e.by_suite[suite] = (p + row.agg.passes, n + row.agg.runs)
            e.passes += row.agg.passes
            e.scored += row.agg.runs

    def real_rate(e: Entry) -> float:
        p, n = e.by_suite.get("real", (0, 0))
        return p / n if n else -1.0

    # A sanity-only 100% must not outrank a model that also faced the much
    # harder real suite: models scored in every suite rank first.
    # Then a model that did not answer every task (e.g. the rest hit a quota)
    # ranks last: 2/2 answered is not 100% of the suite.
    ranking = sorted(entries.values(),
                     key=lambda e: (e.partial, not e.complete, -e.rate, -real_rate(e), e.name))
    all_cases = [c for suite in SUITES for c in cases[suite]]
    return Board(rows=rows, ranking=ranking, budgets=budgets, cases=cases, score=score,
                 routes=routes, since=since, measured_only=measured_only,
                 include_effort=include_effort,
                 agentic=agentic_rows(all_cases, score=score, scorer=scorer, since=since),
                 single_shot=single_shot, agentic_budgets=agentic_budgets)


def _num(v: float | None, spec: str = ".0f") -> str:
    return "n/a" if v is None else format(v, spec)


def _date(rid: str) -> str:
    try:
        return datetime.strptime(rid[:8], "%Y%m%d").strftime("%b %d")
    except ValueError:
        return rid


def render_agentic(board: Board) -> list[str]:
    """The primary result: migration the way it is done on a real project."""
    cases = [c for suite in SUITES for c in board.cases[suite]]
    lines = ["# Agentic migration (primary result)", "",
             "The model works on a copy of the project in a sandbox with a coding agent, the way "
             "a developer would: it changes code, builds, runs the tests and fixes what fails, "
             "until its goal is met or the time limit is hit (agentic.py). What it delivered is "
             "then checked by the same acceptance test as single-shot, including hidden tests it "
             "never saw. Infra errors (sessions that never ran) are excluded.", "",
             "Claude models run in Claude Code; open-weight models run in opencode (rows marked "
             "\"· opencode\"), so an opencode row differs from a Claude row in both the model "
             "and the agent.", "",
             "## Ranking", ""]
    if not board.agentic:
        return lines + ["_No agentic runs yet (`python agentic.py --pair <pair> --role current`)._", ""]
    lines += ["Models that tried every task rank first, then by pass rate; equal pass rates "
              "are ranked by time, then cost. Time is the agent's wall-clock time. Cost is "
              "Claude Code's estimate at API list prices, or for opencode rows the OpenCode Go "
              "list price of the tokens used (quota, not a bill); the ranking adds up each "
              "task's mean attempt, i.e. one pass through the tasks tried.", "",
              "| # | Model | Thinking level | Sanity passed | Real passed | Overall pass rate | "
              "Tasks tried | Time, all tasks (min) | Cost, all tasks |",
              "|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    for i, row in enumerate(board.agentic, 1):
        suites = []
        for suite in SUITES:
            got = [row.by_case[c] for c in board.cases[suite] if c in row.by_case]
            suites.append(f"{sum(t.passes for t in got)}/{sum(t.attempts for t in got)}"
                          if got else "—")
        tried = f"{len(row.by_case)}/{len(cases)}"
        lines.append(f"| {i} | {row.name} | {row.level} | {suites[0]} | {suites[1]} | "
                     f"{row.rate * 100:.0f}% ({row.passes}/{row.attempts}) | {tried} | "
                     f"{row.time_s / 60:.1f} | ${row.cost_usd:.2f} |")
    lines.append("")
    for suite in SUITES:
        budgets = board.agentic_budgets.get(suite, [])
        for case in board.cases[suite]:
            title = CASE_TITLES.get(case)
            lines += [f"### {case}" + (f" — {title}" if title else ""), ""]
            ranked = sorted(((r, r.by_case[case]) for r in board.agentic if case in r.by_case),
                            key=lambda t: (-t[1].rate, t[1].mean_time_s,
                                           t[1].cost_usd / t[1].attempts, t[0].name))
            if not ranked:
                lines += ["_No agentic results for this task yet._", ""]
                continue
            header = ["#", "Model", "Thinking level", "Passed", "Pass rate", "Mean time (min)",
                      "TTFS (min)", *[f"Pass@{b:g}s" for b in budgets], "Tool / model time",
                      "Mean cost", "Cost / pass", "Mean turns", "Runs"]
            lines += ["| " + " | ".join(header) + " |",
                      "|---:|---|---|" + "---:|" * (len(header) - 4) + "---|"]
            for i, (row, t) in enumerate(ranked, 1):
                ttfs, ratio = t.ttfs_s, t.tool_model_ratio
                cells = [str(i), row.name, row.level, f"{t.passes}/{t.attempts}",
                         f"{t.rate * 100:.0f}%", f"{t.mean_time_s / 60:.1f}",
                         "n/a" if ttfs is None else f"{ttfs / 60:.1f}",
                         *[f"{t.pass_at(b) * 100:.0f}%" for b in budgets],
                         "n/a" if ratio is None else f"{ratio:.2f}",
                         f"${t.cost_usd / t.attempts:.2f}",
                         f"${t.cost_usd / t.passes:.2f}" if t.passes else "n/a",
                         f"{t.turns / t.attempts:.0f}", ", ".join(sorted(t.runs))]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
    lines += ["TTFS is the mean wall time of passing attempts; Pass@T the share of attempts "
              "that passed within T seconds (agentic budgets: models.yaml "
              "`agentic_time_budgets_s`). Tool / model time divides the time tools ran "
              "(builds, tests, servers; parallel calls merged) by the time the model spent in "
              "API requests (opencode reports none: there it is the model steps' wall time "
              "minus the tool time inside them), summed over attempts that measured both; "
              "above 1 means the "
              "attempt was mostly waiting on builds and tests (docs/METRICS_PLAN.md §8).", ""]
    return lines


def render(board: Board) -> str:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# Gate 1 leaderboard", "",
        f"> Generated: {generated} · live scoring: "
        f"{'on (score cache)' if board.score else 'off (--no-score: runner ok-flag, not correctness)'}  ",
        "> Routes: " + ("all" if board.routes is None else
                        ", ".join(ROUTE_NAMES.get(r, r) for r in board.routes)
                        + " (OpenRouter left out; `--routes all` includes it)") + "  ",
        "> Results: " + (f"from run {board.since} on" if board.since else "all dates")
        + ("" if board.single_shot else " · agentic runs only (single-shot screening is in "
           "each pair's REPORT.md; `--all-results` shows it here)")
        + (" · measured thinking only (`thinking_time: true`)"
           if board.measured_only and board.single_shot else "")
        + (" · effort sweeps ranked one row per level"
           if board.include_effort and board.single_shot else "")
        + (" · docs-assisted runs never count" if board.single_shot else ""),
        "",
        *render_agentic(board),
    ]
    if not board.single_shot:
        return "\n".join(lines) + "\n"
    lines += [
        "# Single-shot screening", "",
        "The model gets the sources as text and must write every change in one reply, without "
        "building or testing anything. It is a quick, cheap screen, not a migration: on real "
        "projects every model fails this way.", "",
        "Models, not pairs: every row is one model's own answers, from the latest run in which "
        "it answered every case of the suite (Run names it). Effort sweeps, one-sided "
        "smoke runs and repair rounds are left out, and different settings (output limit, "
        "thinking request) are never pooled into one row. Infra errors are excluded. Quality is "
        "like-for-like. Latency and cost come from each model's own route and from runs made on "
        "different days, and API speed drifts between days, so compare time loosely.", "",
        "## Single-shot ranking", "",
        "Models scored in both suites rank first; a model missing a suite is listed after "
        "them, marked, since sanity tasks are much easier than real ones, and a model that "
        "did not answer every task (the rest were infra errors) comes last. Thinking level "
        "is the effort the answers were made at (\"model default\" when none was sent).", "",
        "| # | Model | Thinking level | Sanity passed | Real passed | Overall pass rate |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for i, e in enumerate(board.ranking, 1):
        cells = []
        for suite in SUITES:
            p, n = e.by_suite.get(suite, (0, 0))
            cells.append(f"{p}/{n}" if n else "—")
        flag = " ⚠ mixed settings" if e.mixed_settings else ""
        if not e.complete:
            missing = [s for s in SUITES if not e.by_suite.get(s, (0, 0))[1]]
            flag += f" ({' and '.join(s for s in SUITES if s not in missing)} only)"
        if e.partial:
            flag += " (partial: not every task answered)"
        levels = [e.levels[s] for s in SUITES if s in e.levels]
        level = (levels[0] if len(set(levels)) == 1
                 else " · ".join(f"{s}: {e.levels[s]}" for s in SUITES if s in e.levels))
        lines.append(f"| {i} | {e.name}{flag} | {level} | {cells[0]} | {cells[1]} | "
                     f"{e.rate * 100:.0f}% ({e.passes}/{e.scored}) |")
    lines.append("")

    for suite in SUITES:
        budgets = board.budgets[suite]
        lines += [f"## Single-shot: {suite} suite", ""]
        header = ["#", "Model", "Route", "Output limit", "Thinking level", "Passed",
                  "Pass rate", "After repair", "Time to pass after repair (s)",
                  "Cost to pass after repair", "Mean latency (s)", "Thinking (s)", "Answer (s)", "TTFS (s)",
                  *[f"Pass@{b:g}s" for b in budgets], "Thinking tokens / answer",
                  "Cost / answer", "Cost / pass", "Run"]
        for case in board.cases[suite]:
            title = CASE_TITLES.get(case)
            lines += [f"### {case}" + (f" — {title}" if title else ""), "",
                      "| " + " | ".join(header) + " |",
                      "|---:|---|---|---|---|" + "---:|" * (len(header) - 5)]
            ranked = sorted(((row, row.by_case[case]) for row in board.rows[suite]
                             if case in row.by_case),
                            key=lambda t: (-t[1].pass_rate, t[1].mean_latency, t[0].name))
            if not ranked:
                lines[-2:] = ["_No results for this task yet._"]
            for i, (row, a) in enumerate(ranked, 1):
                infra = f" (+{a.infra_errors} infra)" if a.infra_errors else ""
                span = (_date(row.runs[0]) if len(row.runs) == 1
                        else f"{_date(row.runs[0])}–{_date(row.runs[-1])}")
                # the run, never the pair folder it is stored in: a row is
                # one model's own answers, not a comparison
                source = f"{span} · run{'s' if len(row.runs) > 1 else ''} " + ", ".join(row.runs)
                cells = [str(i), row.name, row.route, row.limit, row.level,
                         f"{a.passes}/{a.runs}{infra}",
                         f"{a.pass_rate * 100:.0f}%" if a.runs else "n/a",
                         (f"{row.repair_by_case[case][0]}/{row.repair_by_case[case][1]} pass "
                          f"({row.repair_by_case[case][2]} tried)"
                          if case in row.repair_by_case else "—"),
                         _num(row.repair_to_pass[case][0]) if case in row.repair_to_pass else "—",
                         (f"${row.repair_to_pass[case][1]:.3f}"
                          if case in row.repair_to_pass else "—"),
                         _num(a.mean_latency if a.runs else None),
                         _num(a.mean_thinking_time if a.thinking_time_runs else None),
                         _num(a.mean_execution_time),
                         _num(a.mean_ttfs),
                         *[f"{a.pass_at(b) * 100:.0f}%" if a.runs else "n/a" for b in budgets],
                         _num(a.reasoning_tokens / a.runs if a.runs else None, ",.0f"),
                         f"${a.mean_cost:.3f}" if a.runs else "n/a",
                         f"${a.cost_per_success:.3f}" if a.passes else "n/a",
                         source]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
    lines += ["Cost is each route's own basis: Claude Code's estimate at API list prices, "
              "OpenCode Go list prices (a quota, not a bill), or OpenRouter's billed cost. "
              "TTFS is the mean latency of passing answers; Pass@T the share of scored answers "
              "that passed within T seconds (docs/LATENCY.md). After repair counts answers that "
              "pass single-shot or after CI-style repair rounds (repair.py: the model sees the "
              "build/test output and fixes its answer); it is agentic, shown beside the pass "
              "rate and never part of it or of the ranking. — means no answer was repaired. "
              "Time and cost to pass after repair average the answers repair got to pass: the "
              "model time and cost of the first answer plus every repair round up to the "
              "passing one (CI time between rounds is not included)."]
    return "\n".join(lines) + "\n"


def policy() -> dict:
    """The team's leaderboard policy from models.yaml `leaderboard:`."""
    raw = yaml.safe_load((REPO_ROOT / "models.yaml").read_text(encoding="utf-8")) or {}
    lb = raw.get("leaderboard") or {}
    return {"since": str(lb["since"]) if lb.get("since") else None,
            "measured_only": bool(lb.get("measured_only", False)),
            "include_effort": bool(lb.get("include_effort_sweeps", False)),
            "routes": tuple(lb["routes"]) if lb.get("routes") else DEFAULT_ROUTES,
            "single_shot": bool(lb.get("single_shot", True))}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gate 1 leaderboard: models ranked across all pairs")
    ap.add_argument("--no-score", action="store_true",
                    help="use the runner ok-flag instead of the scorers (fast; not correctness)")
    ap.add_argument("--routes", default=None,
                    help="comma-separated routes to rank (claude-code, opencode-go, openrouter) "
                         "or 'all'; default: models.yaml `leaderboard.routes`")
    ap.add_argument("--all-results", action="store_true",
                    help="ignore the models.yaml leaderboard policy (start run, measured-only, "
                         "effort sweeps, agentic only): every run, single-shot screening included")
    args = ap.parse_args(argv)
    pol = policy()
    if args.all_results:
        pol.update(since=None, measured_only=False, include_effort=False, single_shot=True)
    route_arg = args.routes or ",".join(pol["routes"])
    routes = None if route_arg == "all" else tuple(
        r.strip() for r in route_arg.split(",") if r.strip())
    if routes is not None and (bad := [r for r in routes if r not in ROUTE_NAMES]):
        ap.error(f"unknown route(s) {bad}; choose from {', '.join(ROUTE_NAMES)} or 'all'")
    load_env()
    score = not args.no_score
    board = build(score=score, scorer=ScoreCache() if score else None, routes=routes,
                  include_effort=pol["include_effort"], since=pol["since"],
                  measured_only=pol["measured_only"], single_shot=pol["single_shot"])
    out = Path(common.RUNS_DIR) / "LEADERBOARD.md"
    out.write_text(render(board), encoding="utf-8")
    print(f"wrote {out}")
    for i, row in enumerate(board.agentic, 1):
        print(f"  agentic {i:2d}. {row.name} ({row.level}): {row.rate * 100:.0f}% "
              f"({row.passes}/{row.attempts})")
    for i, e in enumerate(board.ranking, 1):
        print(f"  single-shot {i:2d}. {e.name}: {e.rate * 100:.0f}% ({e.passes}/{e.scored})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
