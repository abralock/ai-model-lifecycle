#!/usr/bin/env python3
"""report.py — Gate 1 scorecard generator.

Reads runs/<pair>/*.json (raw per-run records), scores each via scorers.dispatch,
and writes runs/<pair>/REPORT.md comparing current vs target vs Δ on:

  * Quality   — pass/fail -> 0/1 per case, plus pass count / rate
  * Time      — mean latency per successful task
  * Cost      — tokens x price (pricing.py), raw token buckets + normalized views

Normalized views (locked in per TEST_CASES.md):
  * tokens per successful task
  * cache hit-rate %   = cache_read / (cache_read + cache_write)
  * cost per successful task

Runs with no data (empty runs/) produce a valid, empty scorecard — never crashes.

Usage:
    python report.py --pair opus-4.8-vs-5.5
    python report.py --all-pairs
    python report.py --pair opus-4.8-vs-5.5 --no-score   # skip live scorers (fast)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone

from common import RUNS_DIR, Config, load_config, load_env, load_runs
from pricing import cost_usd, get_price
from scorers.dispatch import score_case

# Weights from GATE1_BUILD_PLAN.md §7 (Quality 0.5 / Cost 0.3 / Time 0.2).
W_QUALITY, W_COST, W_TIME = 0.5, 0.3, 0.2


# --------------------------------------------------------------------------- #
# aggregation                                                                  #
# --------------------------------------------------------------------------- #
@dataclass
class ModelAgg:
    model_slug: str
    model_name: str
    role: str
    runs: int = 0
    passes: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_sum: float = 0.0
    case_results: dict[str, str] = field(default_factory=dict)  # case -> PASS/FAIL

    @property
    def pass_rate(self) -> float:
        return (self.passes / self.runs) if self.runs else 0.0

    @property
    def mean_latency(self) -> float:
        return (self.latency_sum / self.runs) if self.runs else 0.0

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


def aggregate(runs: list[dict], score: bool) -> dict[tuple[str, str], ModelAgg]:
    """Aggregate run records into {（model_slug, role): ModelAgg}."""
    aggs: dict[tuple[str, str], ModelAgg] = {}
    for rec in runs:
        slug = rec.get("model_slug", "?")
        role = rec.get("role", "?")
        key = (slug, role)
        a = aggs.get(key)
        if a is None:
            a = ModelAgg(model_slug=slug, model_name=rec.get("model_name", slug), role=role)
            aggs[key] = a

        a.runs += 1
        a.input_tokens += int(rec.get("input_tokens", 0) or 0)
        a.output_tokens += int(rec.get("output_tokens", 0) or 0)
        a.cache_read += int(rec.get("cache_read_tokens", 0) or 0)
        a.cache_write += int(rec.get("cache_write_tokens", 0) or 0)
        a.total_tokens += int(rec.get("total_tokens", 0) or 0)
        a.latency_sum += float(rec.get("latency_s", 0.0) or 0.0)
        a.cost_usd += cost_usd(
            slug,
            int(rec.get("input_tokens", 0) or 0),
            int(rec.get("output_tokens", 0) or 0),
            int(rec.get("cache_read_tokens", 0) or 0),
            int(rec.get("cache_write_tokens", 0) or 0),
        )

        # quality
        passed = bool(rec.get("ok", False))
        if score:
            sr = score_case(rec.get("case_id", ""), rec.get("output_text", "") or "", slug)
            passed = sr.passed
        if passed:
            a.passes += 1
        a.case_results[rec.get("case_id", "?")] = "PASS" if passed else "FAIL"
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


def render_pair(cfg: Config, pair_id: str, aggs: dict[tuple[str, str], ModelAgg],
                runs: list[dict], score: bool) -> str:
    pair = cfg.get_pair(pair_id)
    cur = aggs.get((pair.current.id, "current"))
    tgt = aggs.get((pair.target.id, "target"))

    lines: list[str] = []
    lines.append(f"# Gate 1 Scorecard — {pair.id}\n")
    lines.append(f"> Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}  ")
    lines.append(f"> Current: **{pair.current.name}** (`{pair.current.id}`)  ")
    lines.append(f"> Target: **{pair.target.name}** (`{pair.target.id}`)  ")
    lines.append(f"> Runs loaded: {len(runs)}  ·  live scoring: {'on' if score else 'off (--no-score)'}\n")

    if not cur or not tgt or not runs:
        lines.append("_No run data yet._ Populate `runs/` via "
                     f"`python runner.py --pair {pair_id}` and re-run the report.\n")
        return "\n".join(lines)

    # ---- headline comparison table ---------------------------------------- #
    lines.append("## Summary — Current vs Target\n")
    lines.append("| Metric | Current | Target | Δ |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| Quality (pass rate) | {_pct(cur.pass_rate*100)} | {_pct(tgt.pass_rate*100)} | "
                 f"{_delta(cur.pass_rate, tgt.pass_rate)} |")
    lines.append(f"| Passes / runs | {cur.passes}/{cur.runs} | {tgt.passes}/{tgt.runs} | — |")
    lines.append(f"| Time (mean latency, s) | {cur.mean_latency:.2f} | {tgt.mean_latency:.2f} | "
                 f"{_delta(cur.mean_latency, tgt.mean_latency, higher_better=False)} |")
    lines.append(f"| Cost (total USD) | ${cur.cost_usd:.4f} | ${tgt.cost_usd:.4f} | "
                 f"{_delta(cur.cost_usd, tgt.cost_usd, higher_better=False)} |")
    lines.append("")

    # ---- raw tokens -------------------------------------------------------- #
    lines.append("## Raw token counts\n")
    lines.append("| Bucket | Current | Target | Δ |")
    lines.append("|---|---:|---:|---:|")
    for label, c, t in (
        ("input tokens", cur.input_tokens, tgt.input_tokens),
        ("output tokens", cur.output_tokens, tgt.output_tokens),
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
    lines.append("## Per-case quality\n")
    lines.append("| Case | Current | Target |")
    lines.append("|---|---|---|")
    for c in cases:
        lines.append(f"| {c} | {cur.case_results.get(c, '—')} | {tgt.case_results.get(c, '—')} |")
    lines.append("")

    # ---- price reference --------------------------------------------------- #
    pc, pt = get_price(pair.current.id), get_price(pair.target.id)
    lines.append("### Price reference (USD / 1M tokens)\n")
    lines.append("| Model | input | output | cache-read | cache-write |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(f"| {pair.current.name} | {pc.input} | {pc.output} | {pc.cache_read} | {pc.cache_write} |")
    lines.append(f"| {pair.target.name} | {pt.input} | {pt.output} | {pt.cache_read} | {pt.cache_write} |")
    lines.append("")

    # ---- weighted overall (normalized to current = 100) ------------------- #
    if cur.passes and tgt.passes:
        q = (tgt.pass_rate / cur.pass_rate * 100.0) if cur.pass_rate else 100.0
        c = (cur.cost_per_success / tgt.cost_per_success * 100.0) if tgt.cost_per_success else 100.0
        t = (cur.mean_latency / tgt.mean_latency * 100.0) if tgt.mean_latency else 100.0
        overall = W_QUALITY * q + W_COST * c + W_TIME * t
        lines.append("## Overall score (current = 100 baseline)\n")
        lines.append(f"- Quality component: {q:.1f}  (w={W_QUALITY})")
        lines.append(f"- Cost component:    {c:.1f}  (w={W_COST})")
        lines.append(f"- Time component:    {t:.1f}  (w={W_TIME})")
        lines.append(f"- **Overall: {overall:.1f}**  → "
                     f"{'target ≥ baseline ✅' if overall >= 100 else 'target < baseline ⚠️'}")
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gate 1 scorecard generator")
    ap.add_argument("--pair", help="pair id (e.g. opus-4.8-vs-5.5)")
    ap.add_argument("--all-pairs", action="store_true")
    ap.add_argument("--no-score", action="store_true",
                    help="use runner ok-flag instead of live scorers (fast/offline)")
    args = ap.parse_args(argv)

    load_env()
    cfg = load_config()

    if args.all_pairs:
        pair_ids = [p.id for p in cfg.pairs]
    elif args.pair:
        pair_ids = [args.pair]
    else:
        pair_ids = [p.id for p in cfg.pairs]

    score = not args.no_score
    for pid in pair_ids:
        runs = load_runs(pid)
        aggs = aggregate(runs, score=score)
        md = render_pair(cfg, pid, aggs, runs, score)
        out = RUNS_DIR / pid / "REPORT.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"wrote {out}  ({len(runs)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
