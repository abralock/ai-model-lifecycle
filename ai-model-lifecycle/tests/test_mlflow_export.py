"""tests/test_mlflow_export.py — optional MLflow export of Gate 1 results.

Offline: a throwaway SQLite MLflow store in tmp_path and a fake scorer, so no
server, Postgres or Maven is needed. Skipped when mlflow isn't installed
(it is optional: requirements-mlflow.txt).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

mlflow = pytest.importorskip("mlflow")      # conftest already leaves this file out without mlflow

import common  # noqa: E402
import mlflow_export  # noqa: E402
import report  # noqa: E402
from common import load_config  # noqa: E402

PAIR = "haiku-4.5-vs-5.5"
RID = "20261010T000000Z"


def _write_run(runs_dir, cfg, *, cases=None, rid=RID):
    pair = cfg.get_pair(PAIR)
    d = runs_dir / PAIR
    d.mkdir(parents=True, exist_ok=True)
    for role, m in (("current", pair.current), ("target", pair.target)):
        for case in cases or cfg.cases:
            rec = {"pair_id": PAIR, "case_id": case, "model_slug": m.id, "model_name": m.name,
                   "role": role, "rep": 0, "run_id": rid, "input_tokens": 100, "output_tokens": 50,
                   "cache_read_tokens": 0, "cache_write_tokens": 0, "total_tokens": 150,
                   "provider": "Amazon Bedrock", "billed_cost_usd": 0.01 if role == "current" else 0.002,
                   "latency_s": 10.0 if role == "current" else 20.0,
                   "output_text": f"answer {role} {case}", "ok": True, "error": None}
            (d / f"{m.id.replace('/', '__')}.{case}.{rid}.json").write_text(json.dumps(rec))


def _fake_scorer(calls):
    def score(case_id, output_text, slug):
        calls.append((case_id, output_text))
        bad = output_text.startswith("answer target") and case_id.startswith("r4")
        return SimpleNamespace(passed=not bad, reason="failed checks: index_scan" if bad else "ok")
    return score


@pytest.fixture
def env(tmp_path, monkeypatch):
    cfg = load_config()
    monkeypatch.chdir(tmp_path)                    # MLflow writes artifacts to ./mlruns
    monkeypatch.setattr(common, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(report, "score_case", report.score_case)       # restored after the test
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'mlflow.db'}")
    calls: list = []
    score = mlflow_export.ScoreCache(path=tmp_path / "cache.json", scorer=_fake_scorer(calls))
    yield SimpleNamespace(cfg=cfg, runs=tmp_path / "runs", score=score, calls=calls)
    mlflow.set_tracking_uri(None)


def _runs(level):
    exp = mlflow.get_experiment_by_name(f"Gate1 / {PAIR}")
    return mlflow.search_runs([exp.experiment_id], output_format="list",
                              filter_string=f"tags.level = '{level}'")


def test_export_logs_parent_and_one_child_per_call(env):
    _write_run(env.runs, env.cfg)
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "loaded"

    (parent,) = _runs("run")
    n_cases = len(env.cfg.cases)
    assert parent.data.tags["harness_run_id"] == RID
    assert parent.data.tags["cost_source"] == "billed"
    assert parent.data.tags["providers"] == "Amazon Bedrock"
    m = parent.data.metrics

    # one run per model, with the SAME metric names so MLflow charts compare them
    models = {r.data.tags["role"]: r for r in _runs("model")}
    assert set(models) == {"current", "target"}
    assert all(r.data.tags["mlflow.parentRunId"] == parent.info.run_id for r in models.values())
    cm, tm = models["current"].data.metrics, models["target"].data.metrics
    assert set(cm) == set(tm)
    assert cm["passes"] == n_cases and tm["passes"] == n_cases - 1
    assert cm["cost_usd"] == pytest.approx(0.01 * n_cases)
    assert tm["pass_rate_r4"] == 0.0 and cm["pass_rate_r4"] == 1.0
    assert models["current"].data.tags["mlflow.runColor"] == mlflow_export.CURRENT_COLOR
    assert models["target"].data.tags["mlflow.runColor"] == mlflow_export.TARGET_COLOR

    # the pair run carries current_X / target_X pairs for side-by-side charts
    assert m["current_passes"] == n_cases and m["target_passes"] == n_cases - 1
    assert m["current_cost_component"] == 100.0 and m["current_quality_component"] == 100.0
    assert {f"current_{k}" for k in cm} == {k for k in m if k.startswith("current_")}
    assert {f"target_{k}" for k in tm} == {k for k in m if k.startswith("target_")}

    # overall score is the same number report.py prints
    runs = common.load_runs(PAIR, run=RID)
    aggs = report.aggregate(runs, score=True)
    pair = env.cfg.get_pair(PAIR)
    ov = report.overall_score(aggs[(pair.current.id, "current")], aggs[(pair.target.id, "target")])
    assert m["overall_score"] == pytest.approx(ov.overall)
    assert parent.data.tags["verdict"] == ov.verdict
    assert m["target_cost_component"] == pytest.approx(ov.cost)
    assert tm["cost_component"] == pytest.approx(ov.cost) and cm["cost_component"] == 100.0

    children = _runs("call")
    assert len(children) == 2 * n_cases
    for c in children:                          # calls sit under their model's run
        assert c.data.tags["mlflow.parentRunId"] == models[c.data.params["role"]].info.run_id
    fails = [c for c in children if c.data.tags["result"] == "FAIL"]
    assert len(fails) == 1 and fails[0].data.params["case"].startswith("r4")
    assert fails[0].data.tags["failure_reason"] == "failed checks: index_scan"

    arts = {a.path for a in mlflow.MlflowClient().list_artifacts(parent.info.run_id)}
    assert {"REPORT.md", "calls.json", "comparison.png"} <= arts



def test_export_is_idempotent_and_scores_each_answer_once(env):
    _write_run(env.runs, env.cfg)
    mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score)
    n = len(env.calls)
    assert n == 2 * len(env.cfg.cases)                     # cached across aggregate + children
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "exists"
    assert len(env.calls) == n
    assert len(_runs("run")) == 1
    # the same run from another source (e.g. a teammate) is a separate entry
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "teammate", env.score) == "loaded"
    assert len(env.calls) == n


def test_partial_run_is_not_exported(env):
    _write_run(env.runs, env.cfg, cases=env.cfg.cases[:1])
    assert mlflow_export.export_run(mlflow, env.cfg, PAIR, RID, "local", env.score) == "incomplete"
    assert mlflow.get_experiment_by_name(f"Gate1 / {PAIR}") is None


def test_repeat_number_from_field_or_legacy_filename():
    assert mlflow_export._rep({"rep": 2}) == 3
    assert mlflow_export._rep({"_file": "x.r1_springboot2to3.20261008.r2.json"}) == 3   # legacy: no rep field
    assert mlflow_export._rep({"_file": "x.r1_springboot2to3.20261008.json"}) == 1


def test_overall_score_none_when_a_model_passes_nothing():
    a = report.ModelAgg(model_slug="x", model_name="x", role="current")
    b = report.ModelAgg(model_slug="y", model_name="y", role="target", runs=4, passes=2)
    assert report.overall_score(a, b) is None
