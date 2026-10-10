"""mlflow_export.py — copy Gate 1 results into an MLflow tracking server.

Optional and read-only towards the repo: run files in runs/ stay the source of
truth (reviewed via PRs); MLflow is a browsable copy with history, filters and
side-by-side compare.

Layout in MLflow:

  experiment   "Gate1 / <pair>"
    run          one per harness run id, e.g. "20261009T154316Z (local)"
        tags       level=run, harness_run_id, source, models, verdict, providers, cost_source
        metrics    overall_score, fisher_p, and current_<m> / target_<m> pairs for every
                   model metric below (e.g. current_cost_component vs target_cost_component)
        artifacts  comparison.png (current blue vs target orange: pass rate overall
                   and per task, time, cost, cost per pass, output tokens),
                   REPORT.md (rendered by report.py), calls.json (one row per call)
      model run    one per model, "<model> (current|target)", tag level=model,
                   mlflow.runColor blue (current) / orange (target)
        metrics    pass_rate, passes, scored_runs, cost_usd, cost_per_task_usd,
                   cost_per_passed_task_usd, mean_latency_s, output_tokens,
                   infra_errors, pass_rate_r1/r3/r4/r5, quality/cost/time_component
                   and overall_score (current = 100)
                   (same names for both models, so each MLflow chart compares them)
        call run   one per model call (task x repeat), tag level=call
          params     model, role, case, rep, provider
          metrics    passed, latency_s, input_tokens, output_tokens, cost_usd
          tags       result (PASS/FAIL/INFRA), failure_reason
          artifact   output.txt (the model's answer)

Pass/fail comes from the same scorers report.py uses (Postgres + Docker Maven
needed). Results are cached in .mlflow_score_cache.json, keyed by the answer and
the scorer source, so re-exports are fast and a scorer change re-scores.
A run already exported for the same source is skipped.

Usage:
    docker compose -f docker/docker-compose.yml --profile mlflow up -d
    pip install -r requirements-mlflow.txt
    python mlflow_export.py --all-pairs                 # latest complete run per pair
    python mlflow_export.py --all-pairs --all-runs      # every complete run
    python mlflow_export.py --pair haiku-4.5-vs-5.5 --run 20261009T154316Z
    open http://127.0.0.1:5050

The server is MLFLOW_TRACKING_URI (default http://127.0.0.1:5050).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

import common
import report
from common import load_config, load_env
from scorers.dispatch import score_case as _score_case

DEFAULT_TRACKING_URI = "http://127.0.0.1:5050"
HARNESS_DIR = Path(__file__).resolve().parent
CACHE_FILE = HARNESS_DIR / ".mlflow_score_cache.json"


def _scorer_fingerprint() -> str:
    h = hashlib.sha256()
    for f in sorted((HARNESS_DIR / "scorers").rglob("*.py")):
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


class ScoreCache:
    """Memoizes scorer results by (scorer source, case, answer)."""

    def __init__(self, path: Path | None = CACHE_FILE, scorer=_score_case):
        self.path, self.scorer = path, scorer
        self.fp = _scorer_fingerprint()
        self.data: dict = {}
        if path and path.exists():
            self.data = json.loads(path.read_text())

    def __call__(self, case_id: str, output_text: str, slug: str):
        key = hashlib.sha256(f"{self.fp}\0{case_id}\0{output_text}".encode()).hexdigest()
        if key not in self.data:
            sr = self.scorer(case_id, output_text, slug)
            self.data[key] = {"passed": bool(sr.passed), "reason": sr.reason or ""}
            if self.path:
                self.path.write_text(json.dumps(self.data))
        return SimpleNamespace(**self.data[key])


def _short(slug: str) -> str:
    return slug.split("/")[-1].replace("claude-", "")


def _rep(rec: dict) -> int:
    """1-based repeat number; older run files have no `rep` field, only a .rN file suffix."""
    if isinstance(rec.get("rep"), int):
        return rec["rep"] + 1
    m = re.search(r"\.r(\d+)\.json$", rec.get("_file", ""))
    return int(m.group(1)) + 1 if m else 1


def _call_cost(rec: dict) -> float:
    billed = rec.get("billed_cost_usd")
    if isinstance(billed, (int, float)):
        return float(billed)
    return report.cost_usd(rec["model_slug"], rec.get("input_tokens", 0), rec.get("output_tokens", 0),
                           rec.get("cache_read_tokens", 0), rec.get("cache_write_tokens", 0))


CURRENT_COLOR, TARGET_COLOR = "#1f77b4", "#ff7f0e"     # blue / orange, as in MLflow's own charts


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _bars(ax, pair, label, vals, fmt):
    names = (f"{pair.current.name}\n(current)", f"{pair.target.name}\n(target)")
    bars = ax.bar(names, vals, color=[CURRENT_COLOR, TARGET_COLOR], width=0.55)
    for b, v in zip(bars, vals):
        ax.annotate(fmt(v), (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_title(label, fontsize=12)
    ax.set_ylim(0, max(vals + [1e-9]) * 1.2)
    ax.tick_params(axis="x", labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)


def _panel_pass_rate(ax, pair, cur, tgt):
    _bars(ax, pair, "Pass rate", [cur.pass_rate, tgt.pass_rate], lambda v: f"{v:.0%}")
    for b, agg in zip(ax.patches, (cur, tgt)):
        ax.annotate(f"{agg.passes}/{agg.runs}", (b.get_x() + b.get_width() / 2, b.get_height() / 2),
                    ha="center", va="center", color="white", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.15)


def _panel_per_task(ax, pair, cur, tgt):
    cases = sorted(set(cur.case_results) | set(tgt.case_results))
    x, w = range(len(cases)), 0.38
    for off, agg, color, name in ((-w / 2, cur, CURRENT_COLOR, f"{pair.current.name} (current)"),
                                  (w / 2, tgt, TARGET_COLOR, f"{pair.target.name} (target)")):
        vals = [(lambda k, n: k / n if n else 0)(*agg.case_results.get(c, (0, 0))) for c in cases]
        bars = ax.bar([i + off for i in x], vals, w, color=color, label=name)
        for b, c in zip(bars, cases):
            k, n = agg.case_results.get(c, (0, 0))
            ax.annotate(f"{k}/{n}", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=9)
    ax.set_xticks(list(x), [c.split("_")[0].upper() for c in cases])
    ax.set_ylim(0, 1.2)
    ax.set_title("Pass rate per task", fontsize=12)
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)


# (panel name, drawer): the six panels of comparison.png
PANELS = [
    ("compare_pass_rate", _panel_pass_rate),
    ("compare_pass_rate_per_task", _panel_per_task),
    ("compare_mean_time_s", lambda ax, p, c, t: _bars(
        ax, p, "Mean time per task (s)", [c.mean_latency, t.mean_latency], lambda v: f"{v:.1f}s")),
    ("compare_cost_per_task_usd", lambda ax, p, c, t: _bars(
        ax, p, "Cost per task (USD)", [c.mean_cost, t.mean_cost], lambda v: f"${v:.4f}")),
    ("compare_cost_per_passed_task_usd", lambda ax, p, c, t: _bars(
        ax, p, "Cost per passed task (USD)",
        [c.cost_per_success if c.passes else 0.0, t.cost_per_success if t.passes else 0.0],
        lambda v: f"${v:.4f}")),
    ("compare_output_tokens", lambda ax, p, c, t: _bars(
        ax, p, "Output tokens (total)", [float(c.output_tokens), float(t.output_tokens)],
        lambda v: f"{v:,.0f}")),
]


def comparison_figure(pair, rid: str, cur, tgt, ov):
    """All panels in one figure: current (blue) vs target (orange) for one harness run."""
    plt = _plt()
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
    title = f"{pair.current.name} vs {pair.target.name}  ·  run {rid}"
    if ov:
        title += f"  ·  overall {ov.overall:.1f} ({'target ≥ baseline' if '≥' in ov.verdict else 'target < baseline'})"
    fig.suptitle(title, fontsize=14, fontweight="bold")
    for ax, (_, draw) in zip(axes.flat, PANELS):
        draw(ax, pair, cur, tgt)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def model_metrics(a, components: dict[str, float] | None) -> dict[str, float]:
    """One model's metrics. Names are shared by both models (model runs) and
    prefixed current_/target_ on the pair run, so they line up in MLflow charts."""
    m = {"pass_rate": a.pass_rate, "passes": a.passes, "scored_runs": a.runs,
         "cost_usd": a.cost_usd, "cost_per_task_usd": a.mean_cost,
         "mean_latency_s": a.mean_latency, "output_tokens": a.output_tokens,
         "infra_errors": a.infra_errors}
    if a.passes:
        m["cost_per_passed_task_usd"] = a.cost_per_success
    for case, (k, n) in a.case_results.items():
        m[f"pass_rate_{case.split('_')[0]}"] = k / n if n else 0.0
    m.update(components or {})
    return m


def score_components(ov) -> dict[str, dict[str, float]]:
    """Overall-score components per role; the current model is the 100 baseline."""
    if not ov:
        return {"current": {}, "target": {}}
    return {"current": {"quality_component": 100.0, "cost_component": 100.0,
                        "time_component": 100.0, "overall_score": 100.0},
            "target": {"quality_component": ov.quality, "cost_component": ov.cost,
                       "time_component": ov.time, "overall_score": ov.overall}}


def export_run(mlflow, cfg, pair_id: str, rid: str, source: str, score) -> str:
    """Export one harness run; returns 'loaded', 'exists' or 'incomplete'."""
    runs = common.load_runs(pair_id, run=rid)
    if not runs or report.missing_cases(cfg, runs):
        return "incomplete"

    exp_name = f"Gate1 / {pair_id}"
    mlflow.set_experiment(exp_name)
    exp = mlflow.get_experiment_by_name(exp_name)
    hit = mlflow.search_runs([exp.experiment_id], output_format="list",
                             filter_string=f"tags.harness_run_id = '{rid}' and tags.source = '{source}' "
                                           f"and tags.level = 'run'")
    if hit:
        return "exists"

    report.score_case = score                       # aggregate() looks it up by this name
    aggs = report.aggregate(runs, score=True)
    md = report.render_pair(cfg, pair_id, aggs, runs, True)
    pair = cfg.get_pair(pair_id)
    cur = aggs[(pair.current.id, "current")]
    tgt = aggs[(pair.target.id, "target")]
    ov = report.overall_score(cur, tgt)

    common_tags = {"harness_run_id": rid, "pair": pair_id, "source": source}
    with mlflow.start_run(run_name=f"{rid} ({source})"):
        mlflow.set_tags({
            **common_tags, "level": "run",
            "current_model": pair.current.name, "target_model": pair.target.name,
            "verdict": ov.verdict if ov else "n/a (a model passed nothing)",
            "provider_pinned": str(all(r.get("provider") for r in runs)),
            "providers": ", ".join(sorted({r.get("provider") or "not recorded" for r in runs})),
            "cost_source": "billed" if all(isinstance(r.get("billed_cost_usd"), (int, float)) for r in runs)
                           else "price table",
            "repeats": str(max(_rep(r) for r in runs)),
        })
        comps = score_components(ov)
        mlflow.log_metric("fisher_p", report.fisher_exact_p(
            cur.passes, cur.runs - cur.passes, tgt.passes, tgt.runs - tgt.passes))
        if ov:
            mlflow.log_metric("overall_score", ov.overall)
        # current_X / target_X pairs, e.g. current_cost_component vs target_cost_component
        for role, a in (("current", cur), ("target", tgt)):
            mlflow.log_metrics({f"{role}_{k}": v for k, v in model_metrics(a, comps[role]).items()})
        mlflow.log_text(md, "REPORT.md")
        fig = comparison_figure(pair, rid, cur, tgt, ov)
        mlflow.log_figure(fig, "comparison.png")
        _plt().close(fig)

        table: dict[str, list] = {k: [] for k in ("model", "role", "case", "rep", "result", "reason",
                                                  "latency_s", "output_tokens", "cost_usd", "provider")}
        # one run per model with the SAME metric names, so every MLflow chart
        # shows the two models (and earlier runs) side by side; mlflow.runColor
        # makes MLflow draw current in blue and target in orange
        for role, model, a, color in (("current", pair.current, cur, CURRENT_COLOR),
                                      ("target", pair.target, tgt, TARGET_COLOR)):
            with mlflow.start_run(run_name=f"{model.name} ({role})", nested=True):
                mlflow.set_tags({**common_tags, "level": "model", "role": role, "mlflow.runColor": color})
                mlflow.log_params({"model": model.name, "model_id": model.id, "role": role})
                mlflow.log_metrics(model_metrics(a, comps[role]))

                for rec in sorted((r for r in runs if r["role"] == role), key=lambda r: (r["case_id"], _rep(r))):
                    rep = _rep(rec)
                    infra = report.is_infra_error(rec)
                    sr = (SimpleNamespace(passed=False, reason=f"INFRA ERROR: {rec.get('error')}") if infra
                          else score(rec["case_id"], rec.get("output_text") or "", rec["model_slug"]))
                    result = "INFRA" if infra else ("PASS" if sr.passed else "FAIL")
                    cost, provider = _call_cost(rec), rec.get("provider") or "not recorded"
                    case = rec["case_id"].split("_")[0].upper()
                    with mlflow.start_run(run_name=f"{_short(rec['model_slug'])} · {case} · rep {rep}", nested=True):
                        mlflow.log_params({"model": rec["model_name"], "role": rec["role"], "case": rec["case_id"],
                                           "rep": rep, "provider": provider})
                        call_metrics = {"latency_s": rec.get("latency_s", 0),
                                        "input_tokens": rec.get("input_tokens", 0),
                                        "output_tokens": rec.get("output_tokens", 0), "cost_usd": cost}
                        if not infra:
                            call_metrics["passed"] = int(sr.passed)
                        mlflow.log_metrics(call_metrics)
                        mlflow.set_tags({**common_tags, "level": "call", "result": result,
                                         "failure_reason": "" if sr.passed else sr.reason[:5000]})
                        mlflow.log_text(rec.get("output_text") or "", "output.txt")
                    for k, v in (("model", rec["model_name"]), ("role", rec["role"]), ("case", rec["case_id"]),
                                 ("rep", rep), ("result", result), ("reason", "" if sr.passed else sr.reason),
                                 ("latency_s", rec.get("latency_s", 0)),
                                 ("output_tokens", rec.get("output_tokens", 0)),
                                 ("cost_usd", cost), ("provider", provider)):
                        table[k].append(v)
        mlflow.log_table(table, "calls.json")
    return "loaded"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Copy Gate 1 results into MLflow")
    ap.add_argument("--pair", help="pair id (e.g. haiku-4.5-vs-5.5)")
    ap.add_argument("--all-pairs", action="store_true")
    ap.add_argument("--run", help="one run id; default: the latest complete run")
    ap.add_argument("--all-runs", action="store_true", help="export every complete run")
    ap.add_argument("--runs-dir", help="read runs from another runs/ folder (e.g. a teammate's checkout)")
    ap.add_argument("--source", default="local",
                    help="label for where the runs came from, shown as tag 'source' (default: local)")
    args = ap.parse_args(argv)

    try:
        import mlflow
    except ImportError:
        print("mlflow is not installed: pip install -r requirements-mlflow.txt")
        return 2

    load_env()
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    os.environ.setdefault("MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT", "1")   # one line per run, not per call
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI))
    if args.runs_dir:
        common.RUNS_DIR = Path(args.runs_dir).resolve()

    cfg = load_config()
    pair_ids = [args.pair] if args.pair and not args.all_pairs else [p.id for p in cfg.pairs]
    score = ScoreCache()
    for pid in pair_ids:
        if args.run:
            rids = [args.run]
        elif args.all_runs:
            rids = common.list_runs(pid)
        else:
            rid, _ = report.pick_run(cfg, pid)
            rids = [rid] if rid else []
        for rid in rids:
            status = export_run(mlflow, cfg, pid, rid, args.source, score)
            print(f"{pid} {rid}: {status}")
    print(f"open {mlflow.get_tracking_uri()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
