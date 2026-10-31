#!/usr/bin/env python3
"""report.py — Gate 1 scorecard generator.

Reads runs/<pair>/*.json (raw per-run records), scores each via scorers.dispatch,
and writes runs/<pair>/REPORT.md comparing current vs target vs Δ on:

  * Quality   — pass/fail per run; pass rate with a 95% Wilson interval, per-case
                passes/runs, and a Fisher exact test for the current-vs-target gap
  * Time      — mean latency per scored run
  * Cost      — tokens x price (pricing.py), raw token buckets + normalized views

Infrastructure errors (provider/API failures, as opposed to a model answer that
fails its checks) are reported separately and excluded from quality, time and
cost. Only one run is scored: by default the latest COMPLETE run (every
configured case, for both models), or --run <run id> (a runner invocation's id
such as 20261009T143005Z; a legacy run's id is its date). A newer partial run
(e.g. `runner.py --case r4_...`) is named in the header but not scored.

Normalized views (locked in per TEST_CASES.md):
  * tokens per successful task
  * cache hit-rate %   = cache_read / (cache_read + cache_write)
  * cost per successful task

Runs with no data (empty runs/) produce a valid, empty scorecard — never crashes.

Usage:
    python report.py --pair opus-4.8-vs-5.5
    python report.py --all-pairs
    python report.py --pair opus-4.8-vs-5.5 --no-score   # skip live scorers (fast)
    python report.py --pair opus-4.8-vs-5.5 --run 20261009T143005Z
    python report.py --pair opus-4.8-vs-5.5 --list-runs
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from common import EFFORT_LEVELS, RUNS_DIR, Config, list_runs, load_config, load_env, load_runs
from pricing import DEFAULT_PRICE, cost_usd, get_price
from scorers.dispatch import score_case

# Weights from GATE1_BUILD_PLAN.md §7 (Quality 0.5 / Cost 0.3 / Time 0.2).
W_QUALITY, W_COST, W_TIME = 0.5, 0.3, 0.2

# Cost and time components are ratios (current / target x 100) and unbounded:
# a target 4x cheaper would score 400 on cost and outweigh a quality drop.
# Clamp them so efficiency can move the overall score by at most
# W_COST*50 + W_TIME*50 = 25 points either way.
COMPONENT_MIN, COMPONENT_MAX = 50.0, 150.0


def component(cur: float, tgt: float) -> float:
    """Lower-is-better metric as a 0..150 score, current = 100, clamped."""
    if not cur or not tgt:
        return 100.0
    return max(COMPONENT_MIN, min(COMPONENT_MAX, cur / tgt * 100.0))


# --------------------------------------------------------------------------- #
# aggregation                                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class ModelAgg:
    model_slug: str
    model_name: str
    role: str
    runs: int = 0                   # scored runs (infra errors excluded)
    passes: int = 0
    infra_errors: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0       # part of output_tokens spent thinking (when reported)
    cost_usd: float = 0.0
    billed_runs: int = 0            # runs whose cost is OpenRouter's billed cost
    estimate_runs: int = 0          # runs whose cost is Claude Code's estimate (not billed)
    providers: dict[str, int] = field(default_factory=dict)  # provider -> runs
    latency_sum: float = 0.0
    thinking_time_sum: float = 0.0
    thinking_time_runs: int = 0       # calls with streaming measurements (legacy runs have none)
    # Descriptive timing metrics (docs/METRICS_PLAN.md) — they never feed the
    # weighted overall score.
    ttfs_sum: float = 0.0             # latency over passing attempts only
    outcomes: list[tuple[float, bool]] = field(default_factory=list)  # (latency_s, passed)
    paired_thinking_sum: float = 0.0  # calls where BOTH phases were measured
    paired_execution_sum: float = 0.0
    paired_timing_runs: int = 0
    execution_time_sum: float = 0.0   # visible-answer phase, over measured calls
    execution_time_runs: int = 0
    case_results: dict[str, list[int]] = field(default_factory=dict)  # case -> [passes, runs]
    failures: list[tuple[str, str]] = field(default_factory=list)      # (file, reason)

    @property
    def pass_rate(self) -> float:
        return (self.passes / self.runs) if self.runs else 0.0

    @property
    def mean_latency(self) -> float:
        return (self.latency_sum / self.runs) if self.runs else 0.0

    @property
    def mean_thinking_time(self) -> float:
        return (self.thinking_time_sum / self.thinking_time_runs) if self.thinking_time_runs else 0.0

    @property
    def mean_execution_time(self) -> float | None:
        return (self.execution_time_sum / self.execution_time_runs
                if self.execution_time_runs else None)

    @property
    def mean_ttfs(self) -> float | None:
        """Mean latency of passing attempts; None (n/a) without a pass."""
        return (self.ttfs_sum / self.passes) if self.passes else None

    def pass_at(self, budget_s: float) -> float:
        """Share of scored attempts that passed within the budget (inclusive).
        Failures and slow passes stay in the denominator; infra errors are
        excluded upstream (they never enter `outcomes`)."""
        if not self.outcomes:
            return 0.0
        hits = sum(1 for latency, passed in self.outcomes if passed and latency <= budget_s)
        return hits / len(self.outcomes)

    @property
    def execution_thinking_ratio(self) -> float | None:
        """sum(execution) / sum(thinking) over calls measuring both phases;
        None without pairs or with zero total thinking (never inferred)."""
        if not self.paired_timing_runs or self.paired_thinking_sum <= 0:
            return None
        return self.paired_execution_sum / self.paired_thinking_sum

    @property
    def pass_ci(self) -> tuple[float, float]:
        return wilson_ci(self.passes, self.runs)

    @property
    def mean_cost(self) -> float:
        return (self.cost_usd / self.runs) if self.runs else 0.0

    @property
    def cache_hit_rate(self) -> float:
        denom = self.cache_read + self.cache_write
        return (self.cache_read / denom * 100.0) if denom else 0.0

    @property
    def tokens_per_success(self) -> float:
        return (self.total_tokens / self.passes) if self.passes else 0.0

    @property
    def cost_per_success(self) -> float:
        return (self.cost_usd / self.passes) if self.passes else 0.0


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion k/n."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def fisher_exact_p(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for the 2x2 table [[a, b], [c, d]]."""
    r1, c1, n = a + b, a + c, a + b + c + d

    def prob(x: int) -> float:
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)

    p0 = prob(a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= p0 * (1 + 1e-9)))


def is_infra_error(rec: dict) -> bool:
    """A provider/API failure, not a model answer. An empty completion is the
    model's own behavior (e.g. it ran out of tokens) and is scored as a FAIL."""
    err = rec.get("error") or ""
    return not rec.get("ok", False) and not err.startswith("empty completion")


def reasoning_level(rec: dict) -> str:
    """Effective reasoning request recorded on a call, for MLflow filtering.
    OpenRouter suites request thinking as a budget ({max_tokens: N}) rather
    than an effort level — that is still a recorded request."""
    requested = rec.get("reasoning_requested")
    if not isinstance(requested, dict):
        return "not recorded"
    if requested.get("effort"):
        return str(requested["effort"])
    if requested.get("max_tokens"):
        return f"max_tokens={requested['max_tokens']}"
    return "not recorded"


def _timing_value(v: Any) -> float | None:
    """A stream-phase measurement, or None. A missing measurement is never
    zero, and bool is not a number here."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return max(0.0, float(v))
    return None


def aggregate(runs: list[dict], score: bool,
              scorer=None) -> dict[tuple[str, str], ModelAgg]:
    """Aggregate run records into {(model_slug, role): ModelAgg}.

    `scorer` (default: the live scorers) lets callers pass a cached one
    (score_cache.ScoreCache); it is only used when `score` is on."""
    aggs: dict[tuple[str, str], ModelAgg] = {}
    for rec in runs:
        slug = rec.get("model_slug", "?")
        role = rec.get("role", "?")
        key = (slug, role)
        a = aggs.get(key)
        if a is None:
            a = ModelAgg(model_slug=slug, model_name=rec.get("model_name", slug), role=role)
            aggs[key] = a

        if is_infra_error(rec):
            a.infra_errors += 1
            a.failures.append((rec.get("_file", "?"), f"INFRA ERROR: {rec.get('error')}"))
            continue

        a.runs += 1
        a.input_tokens += int(rec.get("input_tokens", 0) or 0)
        a.output_tokens += int(rec.get("output_tokens", 0) or 0)
        a.cache_read += int(rec.get("cache_read_tokens", 0) or 0)
        a.cache_write += int(rec.get("cache_write_tokens", 0) or 0)
        a.total_tokens += int(rec.get("total_tokens", 0) or 0)
        a.reasoning_tokens += int(rec.get("reasoning_tokens", 0) or 0)
        a.latency_sum += float(rec.get("latency_s", 0.0) or 0.0)
        thinking_time = _timing_value(rec.get("thinking_time_s"))
        execution_time = _timing_value(rec.get("execution_time_s"))
        if thinking_time is not None:
            a.thinking_time_sum += thinking_time
            a.thinking_time_runs += 1
        if execution_time is not None:
            a.execution_time_sum += execution_time
            a.execution_time_runs += 1
        if thinking_time is not None and execution_time is not None:
            a.paired_thinking_sum += thinking_time
            a.paired_execution_sum += execution_time
            a.paired_timing_runs += 1
        # cost: what OpenRouter billed when recorded, else Claude Code's
        # estimate at API list prices, else the price table
        billed = rec.get("billed_cost_usd")
        estimate = rec.get("cost_estimate_usd")
        # OpenCode Go returns usage.cost = 0 for some models (first seen with
        # Kimi K3): on a quota subscription zero means "no billing info", not
        # a free call, so only a positive amount counts as billed.
        if isinstance(billed, (int, float)) and billed > 0:
            a.cost_usd += float(billed)
            a.billed_runs += 1
        elif isinstance(estimate, (int, float)):
            a.cost_usd += float(estimate)
            a.estimate_runs += 1
        else:
            a.cost_usd += cost_usd(
                slug,
                int(rec.get("input_tokens", 0) or 0),
                int(rec.get("output_tokens", 0) or 0),
                int(rec.get("cache_read_tokens", 0) or 0),
                int(rec.get("cache_write_tokens", 0) or 0),
            )
        prov = rec.get("provider") or "not recorded"
        a.providers[prov] = a.providers.get(prov, 0) + 1

        # quality
        passed, reason = bool(rec.get("ok", False)), rec.get("error") or "runner not ok"
        if score:
            sr = (scorer or score_case)(rec.get("case_id", ""), rec.get("output_text", "") or "", slug)
            passed, reason = sr.passed, sr.reason
        cr = a.case_results.setdefault(rec.get("case_id", "?"), [0, 0])
        cr[1] += 1
        latency = float(rec.get("latency_s", 0.0) or 0.0)
        a.outcomes.append((latency, bool(passed)))
        if passed:
            a.passes += 1
            cr[0] += 1
            a.ttfs_sum += latency
        else:
            a.failures.append((rec.get("_file", "?"), reason))
    return aggs


# --------------------------------------------------------------------------- #
# markdown rendering                                                           #
# --------------------------------------------------------------------------- #
def _pct(x: float) -> str:
    return f"{x:.1f}%"


def _delta(cur: float, tgt: float, *, higher_better: bool = True) -> str:
    d = tgt - cur
    if cur == 0:
        return "n/a"
    sign = "+" if d >= 0 else ""
    good = (d >= 0) if higher_better else (d <= 0)
    arrow = "🟢" if good else "🔴"
    pct = (d / cur * 100.0) if cur else 0.0
    return f"{sign}{pct:.1f}% {arrow}"


def missing_cases(cfg: Config, runs: list[dict]) -> list[str]:
    """Configured cases this run lacks for the current or the target model."""
    have = {(r.get("case_id"), r.get("role")) for r in runs}
    return sorted(c for c in cfg.cases if not {(c, "current"), (c, "target")} <= have)


def suite_run_ids(cfg: Config, pair_id: str) -> list[str]:
    """Run ids holding at least one case of cfg's suite, oldest first.

    Each runner invocation runs one suite, so a run of another suite (e.g. a
    `--suite real` run, seen from the sanity report) is not a partial run of
    this one and is left out entirely.
    """
    wanted = set(cfg.cases)
    return [rid for rid in list_runs(pair_id)
            if any(r.get("case_id") in wanted for r in load_runs(pair_id, run=rid))]


def is_effort_run(runs: list[dict]) -> bool:
    """A thinking-effort sweep run (runner.py --effort): it overrides the
    configured effort, so it is reported by --by-effort, never as the scorecard."""
    return any(r.get("effort_override") for r in runs)


def is_variant_run(runs: list[dict]) -> bool:
    """A run that is not plain single-shot Gate 1: an effort sweep or a
    docs-assisted run (runner.py --docs). Reported on its own (--by-effort,
    --run <id>), never as the scorecard or on the leaderboard."""
    return is_effort_run(runs) or any(r.get("docs_tool") for r in runs)


def pick_run(cfg: Config, pair_id: str) -> tuple[str | None, list[str]]:
    """The latest complete run id, plus the newer partial run ids skipped for it.

    Effort-sweep and docs-assisted runs are left out entirely (see
    is_variant_run). No complete
    run at all -> the latest run (its header then flags it partial).
    """
    loaded = {rid: load_runs(pair_id, run=rid) for rid in suite_run_ids(cfg, pair_id)}
    ids = [rid for rid, recs in loaded.items() if not is_variant_run(recs)]
    skipped: list[str] = []
    for rid in reversed(ids):
        if not missing_cases(cfg, loaded[rid]):
            return rid, skipped
        skipped.append(rid)
    return (ids[-1] if ids else None), []


def effort_runs(cfg: Config, pair_id: str) -> dict[tuple[str, str], tuple[str, list[dict]]]:
    """(role, effort level) -> (run id, that role's records), from the LATEST
    run holding that role at that level. One-sided runs (runner.py --role)
    count: each side of a sweep is read on its own."""
    wanted = set(cfg.cases)
    found: dict[tuple[str, str], tuple[str, list[dict]]] = {}
    for rid in suite_run_ids(cfg, pair_id):             # oldest first: later runs win
        groups: dict[tuple[str, str], list[dict]] = {}
        for rec in load_runs(pair_id, run=rid):
            level = rec.get("effort_override")
            if level and rec.get("case_id") in wanted:
                groups.setdefault((rec.get("role", "?"), level), []).append(rec)
        found.update({key: (rid, recs) for key, recs in groups.items()})
    return found


def _providers(a: ModelAgg) -> str:
    return ", ".join(f"{p} ×{n}" for p, n in sorted(a.providers.items())) or "—"


def _table_runs(a: ModelAgg) -> int:
    """Runs priced from the pricing.py table (no billed cost, no estimate)."""
    return a.runs - a.billed_runs - a.estimate_runs


def _cost_source(a: ModelAgg) -> str:
    if a.runs and a.billed_runs == a.runs:
        return f"billed by OpenRouter ({a.billed_runs}/{a.runs})"
    if a.runs and a.estimate_runs == a.runs:
        return f"Claude Code estimate at API prices ({a.estimate_runs}/{a.runs})"
    if not a.billed_runs and not a.estimate_runs:
        return "price table (pricing.py)"
    parts = [f"billed {a.billed_runs}/{a.runs}"] if a.billed_runs else []
    if a.estimate_runs:
        parts.append(f"Claude Code estimate {a.estimate_runs}/{a.runs}")
    if _table_runs(a):
        parts.append("rest price table")
    return ", ".join(parts)


def render_pair(cfg: Config, pair_id: str, aggs: dict[tuple[str, str], ModelAgg],
                runs: list[dict], score: bool, skipped: list[str] | None = None,
                time_budgets: list[float] | None = None) -> str:
    pair = cfg.get_pair(pair_id)
    cur = aggs.get((pair.current.id, "current"))
    tgt = aggs.get((pair.target.id, "target"))

    lines: list[str] = []
    title = pair.id if cfg.suite == "sanity" else f"{pair.id} · {cfg.suite} suite"
    lines.append(f"# Gate 1 Scorecard — {title}\n")
    lines.append(f"> Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}  ")
    lines.append(f"> Current: **{pair.current.name}** (`{pair.current.id}`)  ")
    lines.append(f"> Target: **{pair.target.name}** (`{pair.target.id}`)  ")
    run_ids = sorted({r.get("_run") for r in runs if r.get("_run")})
    lines.append(f"> Run: {', '.join(run_ids) or '—'}  ·  runs loaded: {len(runs)}  ·  "
                 f"live scoring: {'on' if score else 'off (--no-score)'}  ")
    missing = missing_cases(cfg, runs) if runs else []
    if missing:
        lines.append(f"> ⚠️ **Partial run** — missing cases: {', '.join(missing)}. "
                     f"Not a full Gate 1 scorecard.  ")
    limits = {role: sorted({r.get("max_tokens") for r in runs if r.get("role") == role and r.get("max_tokens")})
              for role in ("current", "target")}
    if runs and any(limits.values()):
        fmt = lambda v: "/".join(f"{x:,}" for x in v) or "—"
        lines.append(f"> Output limit (max_tokens): current {fmt(limits['current'])} · "
                     f"target {fmt(limits['target'])}  ")
    thinking = {json.dumps(r.get("reasoning_requested"), sort_keys=True) for r in runs}
    if thinking != {"null"} and runs:
        lines.append(f"> Thinking budget sent: {', '.join(sorted(thinking))} (recorded per call)  ")
    if docs := sorted({r["docs_tool"] for r in runs if r.get("docs_tool")}):
        looked = {role: sum(len(r.get("docs_calls") or []) for r in runs if r.get("role") == role)
                  for role in ("current", "target")}
        lines.append(f"> Docs tool: {', '.join(docs)} — docs-assisted, not single-shot "
                     f"(current {looked['current']} lookups, target {looked['target']} lookups)  ")
    if skipped:
        lines.append(f"> Newer partial run(s) not scored here: {', '.join(skipped)} "
                     f"(see `report.py --run <id>`).  ")
    lines.append("")

    if not cur or not tgt or not runs:
        lines.append("_No run data yet._ Populate `runs/` via "
                     f"`python runner.py --pair {pair_id}` and re-run the report.\n")
        return "\n".join(lines)

    # ---- headline comparison table ---------------------------------------- #
    lines.append("## Summary — Current vs Target\n")
    lines.append("| Metric | Current | Target | Δ |")
    lines.append("|---|---:|---:|---:|")
    def ci(a: ModelAgg) -> str:
        lo, hi = a.pass_ci
        return f"{lo*100:.0f}–{hi*100:.0f}%"

    p_val = fisher_exact_p(cur.passes, cur.runs - cur.passes, tgt.passes, tgt.runs - tgt.passes)
    lines.append(f"| Quality (pass rate) | {_pct(cur.pass_rate*100)} | {_pct(tgt.pass_rate*100)} | "
                 f"{_delta(cur.pass_rate, tgt.pass_rate)} |")
    lines.append(f"| Pass rate 95% CI (Wilson) | {ci(cur)} | {ci(tgt)} | — |")
    lines.append(f"| Passes / scored runs | {cur.passes}/{cur.runs} | {tgt.passes}/{tgt.runs} | "
                 f"Fisher p = {p_val:.3f} |")
    lines.append(f"| Infra errors (excluded) | {cur.infra_errors} | {tgt.infra_errors} | — |")
    lines.append(f"| Provider (runs) | {_providers(cur)} | {_providers(tgt)} | — |")
    lines.append(f"| Cost source | {_cost_source(cur)} | {_cost_source(tgt)} | — |")
    lines.append(f"| Time (mean latency, s) | {cur.mean_latency:.2f} | {tgt.mean_latency:.2f} | "
                 f"{_delta(cur.mean_latency, tgt.mean_latency, higher_better=False)} |")
    if cur.thinking_time_runs or tgt.thinking_time_runs:
        def thinking_cell(a: ModelAgg) -> str:
            return (f"{a.mean_thinking_time:.2f} ({a.thinking_time_runs}/{a.runs} measured)"
                    if a.thinking_time_runs else "n/a")
        thinking_delta = (_delta(cur.mean_thinking_time, tgt.mean_thinking_time, higher_better=False)
                          if cur.thinking_time_runs and tgt.thinking_time_runs else "n/a")
        lines.append(f"| Thinking stream time (mean, s) | {thinking_cell(cur)} | {thinking_cell(tgt)} | "
                     f"{thinking_delta} |")
    # Descriptive timing metrics (docs/METRICS_PLAN.md): they never feed the
    # Quality/Cost/Time components or the verdict.
    budgets = time_budgets if time_budgets is not None else cfg.time_budgets_s

    def ttfs_cell(a: ModelAgg) -> str:
        return (f"{a.mean_ttfs:.2f} ({a.passes}/{a.runs} passed)"
                if a.mean_ttfs is not None else "n/a")

    ttfs_delta = (_delta(cur.mean_ttfs, tgt.mean_ttfs, higher_better=False)
                  if cur.mean_ttfs is not None and tgt.mean_ttfs is not None else "n/a")
    lines.append(f"| TTFS (mean successful-attempt latency, s) | {ttfs_cell(cur)} | "
                 f"{ttfs_cell(tgt)} | {ttfs_delta} |")
    for budget in budgets:
        c, t = cur.pass_at(budget), tgt.pass_at(budget)
        lines.append(f"| Pass@{budget:g}s | {_pct(c * 100)} | {_pct(t * 100)} | "
                     f"{_delta(c, t)} |")

    def ratio_cell(a: ModelAgg) -> str:
        r = a.execution_thinking_ratio
        return (f"{r:.2f} ({a.paired_timing_runs}/{a.runs} measured)"
                if r is not None else "n/a")

    ratio_delta = (_delta(cur.execution_thinking_ratio, tgt.execution_thinking_ratio)
                   if cur.execution_thinking_ratio is not None
                   and tgt.execution_thinking_ratio is not None else "n/a")
    lines.append(f"| Execution / thinking time ratio | {ratio_cell(cur)} | "
                 f"{ratio_cell(tgt)} | {ratio_delta} |")
    lines.append(f"| Cost (total USD) | ${cur.cost_usd:.4f} | ${tgt.cost_usd:.4f} | "
                 f"{_delta(cur.cost_usd, tgt.cost_usd, higher_better=False)} |")
    lines.append(f"| Cost / run (USD) | ${cur.mean_cost:.4f} | ${tgt.mean_cost:.4f} | "
                 f"{_delta(cur.mean_cost, tgt.mean_cost, higher_better=False)} |")
    lines.append("")
    # A pair whose models are CONFIGURED on different gateways (closed-weight
    # via Claude Code vs open-weight via OpenCode Go) compares routes by
    # design: explain that instead of advising to pin one provider. A mix of
    # providers *within* one model's runs still warns either way.
    if not score:
        lines.append("> TTFS and Pass@T reflect the runner completion flag (--no-score), "
                     "not verified task correctness.\n")
    cross_gateway = (pair.current.api or "") != (pair.target.api or "")
    mixed_within = len(cur.providers) > 1 or len(tgt.providers) > 1
    if cross_gateway:
        lines.append(f"> Cross-gateway pair (by design): current runs via "
                     f"**{pair.current.api or 'OpenRouter'}**, target via "
                     f"**{pair.target.api or 'OpenRouter'}**. Quality is like-for-like (same "
                     "tasks, same scorers). Time and Cost compare each model **on its own "
                     "route** — two services with different cost bases — not two models on "
                     "shared infrastructure.\n")
    if mixed_within or (not cross_gateway and set(cur.providers) != set(tgt.providers)):
        lines.append("> ⚠️ Current and target ran on **different providers** (or a mix). The Time "
                     "comparison partly measures provider speed, not model speed. Pin one provider "
                     "in `models.yaml` (`defaults.provider`) and re-run.\n")
    if _table_runs(cur) or _table_runs(tgt):
        lines.append("> Cost uses the `pricing.py` table for runs without an OpenRouter billed "
                     "cost (runs made before billed cost was recorded). Table prices may be out of date.\n")
    if cur.estimate_runs or tgt.estimate_runs:
        lines.append("> Cost is Claude Code's estimate at API list prices (`total_cost_usd`). The "
                     "subscription does not bill per call, so this is not a bill, and it is not "
                     "comparable with OpenRouter billed cost.\n")
    if p_val >= 0.05:
        lines.append(f"> ⚠️ The quality difference is **not statistically significant** "
                     f"(Fisher p = {p_val:.2f}, n = {cur.runs} vs {tgt.runs}). Add cases or "
                     f"repeats before treating it as a real difference.\n")

    # ---- raw tokens -------------------------------------------------------- #
    lines.append("## Raw token counts\n")
    lines.append("| Bucket | Current | Target | Δ |")
    lines.append("|---|---:|---:|---:|")
    for label, c, t in (
        ("input tokens", cur.input_tokens, tgt.input_tokens),
        ("output tokens", cur.output_tokens, tgt.output_tokens),
        ("· of which thinking", cur.reasoning_tokens, tgt.reasoning_tokens),
        ("cache-read tokens", cur.cache_read, tgt.cache_read),
        ("cache-write tokens", cur.cache_write, tgt.cache_write),
        ("**total token spend**", cur.total_tokens, tgt.total_tokens),
    ):
        lines.append(f"| {label} | {c:,} | {t:,} | {_delta(float(c), float(t), higher_better=False)} |")
    lines.append("")

    # ---- normalized views -------------------------------------------------- #
    lines.append("## Normalized views\n")
    lines.append("| Metric | Current | Target | Δ |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| Tokens / successful task | {cur.tokens_per_success:,.0f} | "
                 f"{tgt.tokens_per_success:,.0f} | "
                 f"{_delta(cur.tokens_per_success, tgt.tokens_per_success, higher_better=False)} |")
    lines.append(f"| Cache hit-rate % | {_pct(cur.cache_hit_rate)} | {_pct(tgt.cache_hit_rate)} | "
                 f"{_delta(cur.cache_hit_rate, tgt.cache_hit_rate)} |")
    lines.append(f"| Cost / successful task (USD) | ${cur.cost_per_success:.4f} | "
                 f"${tgt.cost_per_success:.4f} | "
                 f"{_delta(cur.cost_per_success, tgt.cost_per_success, higher_better=False)} |")
    lines.append("")

    # ---- per-case quality -------------------------------------------------- #
    cases = sorted(set(cur.case_results) | set(tgt.case_results))
    def cell(a: ModelAgg, case: str) -> str:
        if case not in a.case_results:
            return "—"
        k, n = a.case_results[case]
        return f"{k}/{n} {'✅' if k == n else ('❌' if k == 0 else '⚠️')}"

    lines.append("## Per-case quality (passes / runs)\n")
    lines.append("| Case | Current | Target |")
    lines.append("|---|---|---|")
    for c in cases:
        lines.append(f"| {c} | {cell(cur, c)} | {cell(tgt, c)} |")
    lines.append("")

    fails = [(a.model_name, f, why) for a in (cur, tgt) for f, why in a.failures]
    if fails:
        lines.append("## Failing runs\n")
        lines.append("| Model | Run file | Reason |")
        lines.append("|---|---|---|")
        for name, f, why in fails:
            why = (why or "").replace("|", "\\|").replace("\n", " ")[:200]
            lines.append(f"| {name} | `{f}` | {why} |")
        lines.append("")

    # ---- price reference --------------------------------------------------- #
    # Skipped when no run used it and neither model has a pricing.py row (e.g.
    # Claude Code pairs, priced by their estimate): the fallback is no reference.
    pc, pt = get_price(pair.current.id), get_price(pair.target.id)
    if _table_runs(cur) or _table_runs(tgt) or pc is not DEFAULT_PRICE or pt is not DEFAULT_PRICE:
        lines.append("### Price reference (USD / 1M tokens, `pricing.py`; used only when no billed cost)\n")
        lines.append("| Model | input | output | cache-read | cache-write |")
        lines.append("|---|---:|---:|---:|---:|")
        for mref, price, agg in ((pair.current, pc, cur), (pair.target, pt, tgt)):
            if price is DEFAULT_PRICE and not _table_runs(agg):
                # No pricing row and no run priced from the table (e.g. the
                # Claude Code side of a cross-gateway pair, costed by the
                # CLI's estimate): a DEFAULT_PRICE row would be misleading.
                continue
            lines.append(f"| {mref.name} | {price.input} | {price.output} | "
                         f"{price.cache_read} | {price.cache_write} |")
        lines.append("")

    # ---- weighted overall (normalized to current = 100) ------------------- #
    ov = overall_score(cur, tgt)
    if ov:
        lines.append("## Overall score (current = 100 baseline)\n")
        lines.append(f"- Quality component: {ov.quality:.1f}  (w={W_QUALITY})")
        lines.append(f"- Cost component:    {ov.cost:.1f}  (w={W_COST}, clamped to "
                     f"{COMPONENT_MIN:.0f}–{COMPONENT_MAX:.0f})")
        lines.append(f"- Time component:    {ov.time:.1f}  (w={W_TIME}, clamped to "
                     f"{COMPONENT_MIN:.0f}–{COMPONENT_MAX:.0f})")
        lines.append(f"- **Overall: {ov.overall:.1f}**  → {ov.verdict}")
        lines.append("")

    return "\n".join(lines)


@dataclass(frozen=True)
class Overall:
    quality: float
    cost: float
    time: float
    overall: float
    verdict: str


def overall_score(cur: ModelAgg, tgt: ModelAgg) -> Overall | None:
    """Weighted overall score (current = 100) and verdict; None if either model has no pass."""
    if not (cur.passes and tgt.passes):
        return None
    q = (tgt.pass_rate / cur.pass_rate * 100.0) if cur.pass_rate else 100.0
    # cost per run, not per success: quality is already weighted above, so
    # dividing by passes would penalise a failure twice
    c = component(cur.mean_cost, tgt.mean_cost)
    t = component(cur.mean_latency, tgt.mean_latency)
    overall = W_QUALITY * q + W_COST * c + W_TIME * t
    lower_quality = tgt.pass_rate < cur.pass_rate
    if overall >= 100 and not lower_quality:
        verdict = "target ≥ baseline ✅"
    elif lower_quality:
        verdict = ("target < baseline ⚠️ (lower pass rate than current: "
                   "cheaper or faster does not make up for it)")
    else:
        verdict = "target < baseline ⚠️"
    return Overall(q, c, t, overall, verdict)


def _level_key(level: str) -> tuple[int, str]:
    """Sweep levels in EFFORT_LEVELS order (low -> high), unknown ones after."""
    if level in EFFORT_LEVELS:
        return EFFORT_LEVELS.index(level), level
    return len(EFFORT_LEVELS), level


def _num(v: float | None, spec: str = ".2f") -> str:
    return "n/a" if v is None else format(v, spec)


def render_effort_report(cfg: Config, pair_id: str, score: bool,
                         time_budgets: list[float] | None = None) -> str:
    """One table row per model x thinking effort (runner.py --effort), plus the
    main scorecard's run as a "default" baseline, and thinking time by task.
    Descriptive only: nothing here feeds the overall score or the verdict."""
    pair = cfg.get_pair(pair_id)
    budgets = time_budgets if time_budgets is not None else cfg.time_budgets_s
    sweeps = effort_runs(cfg, pair_id)
    default_rid, _ = pick_run(cfg, pair_id)
    default_recs = load_runs(pair_id, run=default_rid) if default_rid else []

    # (role, label, run id, records, aggregate), low -> high, then default
    rows: list[tuple[str, str, str, list[dict], ModelAgg]] = []
    for role in ("current", "target"):
        for _, level in sorted((k for k in sweeps if k[0] == role),
                               key=lambda k: _level_key(k[1])):
            rid, recs = sweeps[(role, level)]
            rows.append((role, level, rid, recs, next(iter(aggregate(recs, score).values()))))
        base = [r for r in default_recs if r.get("role") == role]
        if base:
            levels = {reasoning_level(r) for r in base}
            level = levels.pop() if len(levels) == 1 else "mixed"
            label = "default (model default)" if level == "not recorded" else f"default ({level})"
            rows.append((role, label, default_rid, base,
                         next(iter(aggregate(base, score).values()))))

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        f"# Gate 1 effort sweep — {pair_id} · {cfg.suite} suite",
        "",
        f"> Generated: {generated}  ",
        f"> Current: **{pair.current.name}** (`{pair.current.id}`) · "
        f"Target: **{pair.target.name}** (`{pair.target.id}`)  ",
        f"> Live scoring: {'on' if score else 'off (--no-score)'}  ",
        "",
        "One row per model × thinking effort. Each level is its own run "
        "(`runner.py --effort low,medium,high`); **default** is the main scorecard's run, "
        "at the effort `models.yaml` sends. Thinking and answer times are client-observed "
        "stream phases (docs/LATENCY.md) and need `thinking_time: true`; `n/a` means the "
        "run was not instrumented. Descriptive only: these rows feed no score or verdict.",
        "",
    ]
    if not rows:
        lines.append("_No runs yet. Sweep with "
                     f"`python runner.py --pair {pair_id} --effort low,medium,high`._")
        return "\n".join(lines) + "\n"

    header = ["Model", "Effort", "Run", "Passed", "Mean latency (s)", "Thinking (s)",
              "Answer (s)", "Answer ÷ thinking", "Thinking tokens / call", "TTFS (s)",
              *[f"Pass@{b:g}s" for b in budgets], "Cost / run (USD)"]
    lines += ["## Summary", "",
              "| " + " | ".join(header) + " |",
              "|---|---|---|" + "---:|" * (len(header) - 3)]
    notes: list[str] = []
    for role, label, rid, recs, a in rows:
        name = recs[0].get("model_name") or recs[0].get("model_slug", role)
        passed = f"{a.passes}/{a.runs}" + (f" (+{a.infra_errors} infra)" if a.infra_errors else "")
        thinking = _num(a.mean_thinking_time if a.thinking_time_runs else None)
        if a.thinking_time_runs and a.thinking_time_runs < a.runs:
            thinking += f" ({a.thinking_time_runs}/{a.runs})"
        cells = [
            name, label, f"`{rid}`", passed,
            _num(a.mean_latency if a.runs else None),
            thinking,
            _num(a.mean_execution_time),
            _num(a.execution_thinking_ratio),
            _num(a.reasoning_tokens / a.runs if a.runs else None, ",.0f"),
            _num(a.mean_ttfs),
            *[_pct(a.pass_at(b) * 100) if a.runs else "n/a" for b in budgets],
            f"${a.mean_cost:.4f}" if a.runs else "n/a",
        ]
        lines.append("| " + " | ".join(cells) + " |")
        missing = sorted(set(cfg.cases) - {r.get("case_id") for r in recs})
        if missing:
            notes.append(f"> {name} · {label}: partial run — no {', '.join(missing)}.")
    lines.append("")
    if notes:
        lines += notes + [""]

    lines += ["## Thinking time by task", "",
              "Mean thinking seconds per call · passes / scored runs.", ""]
    for role in ("current", "target"):
        mine = [row for row in rows if row[0] == role]
        if not mine:
            continue
        name = mine[0][3][0].get("model_name") or role
        labels = [row[1].split(" (")[0] for row in mine]
        lines += [f"### {name}", "",
                  "| Task | " + " | ".join(labels) + " |",
                  "|---|" + "---:|" * len(labels)]
        for case in cfg.cases:
            cells = []
            for _, _, _, recs, a in mine:
                timed = [t for r in recs if r.get("case_id") == case and not is_infra_error(r)
                         and (t := _timing_value(r.get("thinking_time_s"))) is not None]
                k, n = a.case_results.get(case, [0, 0])
                think = f"{sum(timed) / len(timed):.1f} s" if timed else "n/a"
                cells.append(f"{think} · {k}/{n}" if n else "—")
            lines.append(f"| {case} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gate 1 scorecard generator")
    ap.add_argument("--pair", help="pair id (e.g. opus-4.8-vs-5.5)")
    ap.add_argument("--all-pairs", action="store_true")
    ap.add_argument("--run", "--date", dest="run",
                    help="run id to score (e.g. 20261009T143005Z, or a legacy run's YYYYMMDD); "
                         "default: the latest complete run")
    ap.add_argument("--suite", default=None,
                    help="case suite from models.yaml: sanity (default; writes REPORT.md) or a "
                         "name under `suites:` (writes REPORT.<suite>.md)")
    ap.add_argument("--list-runs", action="store_true", help="list the run ids per pair and exit")
    ap.add_argument("--no-score", action="store_true",
                    help="use runner ok-flag instead of live scorers (fast/offline)")
    ap.add_argument("--time-budget", action="append", type=float, dest="time_budgets",
                    metavar="SECONDS",
                    help="Pass@T budget in seconds; repeatable. Default: the active "
                         "suite's time_budgets_s from models.yaml")
    ap.add_argument("--by-effort", action="store_true",
                    help="write the thinking-effort sweep table (runs made with "
                         "runner.py --effort) to REPORT[.<suite>].effort.md instead of "
                         "the scorecard")
    args = ap.parse_args(argv)

    load_env()
    cfg = load_config(suite=args.suite)

    if args.all_pairs:
        pair_ids = [p.id for p in cfg.pairs]
    elif args.pair:
        pair_ids = [args.pair]
    else:
        pair_ids = [p.id for p in cfg.pairs]

    if args.list_runs:
        for pid in pair_ids:
            print(f"{pid}:  (suite: {cfg.suite})")
            for rid in suite_run_ids(cfg, pid):
                recs = load_runs(pid, run=rid)
                miss = missing_cases(cfg, recs)
                note = f"partial, missing {', '.join(miss)}" if miss else "complete"
                if is_effort_run(recs):
                    levels = sorted({r["effort_override"] for r in recs if r.get("effort_override")})
                    roles = sorted({r.get("role", "?") for r in recs})
                    note = f"effort sweep: {', '.join(levels)} ({', '.join(roles)})"
                if docs := sorted({r["docs_tool"] for r in recs if r.get("docs_tool")}):
                    note += f" · docs-assisted: {', '.join(docs)}"
                print(f"  {rid}  {len(recs):3d} files  {note}")
        return 0

    score = not args.no_score
    if args.by_effort:
        for pid in pair_ids:
            md = render_effort_report(cfg, pid, score, time_budgets=args.time_budgets)
            out = RUNS_DIR / pid / cfg.effort_report_name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md, encoding="utf-8")
            print(f"wrote {out}")
        return 0
    for pid in pair_ids:
        run, skipped = (args.run, []) if args.run else pick_run(cfg, pid)
        runs = load_runs(pid, run=run) if run else []
        aggs = aggregate(runs, score=score)
        md = render_pair(cfg, pid, aggs, runs, score, skipped,
                         time_budgets=args.time_budgets)
        out = RUNS_DIR / pid / cfg.report_name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"wrote {out}  ({len(runs)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
