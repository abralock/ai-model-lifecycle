"""repair.py — CI-style repair rounds on failed Gate 1 answers.

Gate 1's score is single-shot: one prompt, one answer, no tools. This is a
separate, agentic measurement of how far a model is from a pass. A failed
answer's model sees what CI would show — the failed checks and the build /
test output — plus the current content of the files the errors point at, and
replies with fix-up FILE / EDIT / DELETE blocks. The fix-up is applied on top
of the tree the earlier answers produced and scored by the normal scorer
(`base=`), so the repair's own edits must still apply. Repair records live
under runs/<pair>/repair/<run id>/ and are never part of REPORT.md, the effort
sweep or the overall score.

    python repair.py --pair opus-5.5-cc-vs-kimi-k3 --suite real --run 20261030T150350Z
    python repair.py --pair ... --run ... --case r1b_jhipster_boot3 --rounds 2 --max-repairs 1

Only the project-based real-suite cases (r1b, r2) can be repaired: their
scorers apply an answer onto a project tree. The hidden test suite is never
shown to the model, and the same route and thinking effort as the original
answer are used for the repair call.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import common
import runner
from cases import sources
from common import case_dir, load_config, load_env, load_runs
from report import is_infra_error, reasoning_level
from scorers.base import AppliedOutput, ScoreResult, apply_output
from scorers.dispatch import score_case

# case id -> (scorer module, its pristine-tree constant, the path prefix it strips)
REPAIRABLE = {
    "r1b_jhipster_boot3": ("scorers.r1b_scorer", "PROJECT", "project/"),
    "r2_gwt_to_angular": ("scorers.r2_scorer", "WORKSPACE", "workspace/"),
}
MAX_FEEDBACK_CHARS = 8_000
MAX_TAIL_CHARS = 3_000
MAX_CONTEXT_FILES = 8
MAX_CONTEXT_CHARS = 150_000
BUILD_FILES = ("pom.xml", "package.json")
CLASSPATH_ROOTS = ("src/main/resources/", "src/main/java/")
# Never shown: the hidden test suite (src/test is replaced by the scorer) and
# build output / dependencies.
HIDDEN_PREFIXES = ("src/test/", "target/", "node_modules/", ".git/")
LANG = {".java": "java", ".xml": "xml", ".ts": "typescript", ".js": "javascript",
        ".json": "json", ".yml": "yaml", ".yaml": "yaml", ".html": "html",
        ".scss": "scss", ".css": "css", ".properties": "properties", ".sql": "sql"}


def pristine(case_id: str) -> tuple[Path, str]:
    """(pristine project tree, path prefix its scorer strips) for a case."""
    if case_id not in REPAIRABLE:
        raise ValueError(f"repair rounds support {', '.join(REPAIRABLE)}; not {case_id!r}")
    module, attr, prefix = REPAIRABLE[case_id]
    return getattr(importlib.import_module(module), attr), prefix


def build_tree(case_id: str, answers: list[str], dest: Path) -> list[AppliedOutput]:
    """The project after applying `answers` one after another, as successive
    commits would: each answer sees the files the previous ones produced."""
    sources.ensure(case_id)
    base, prefix = pristine(case_id)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(base, dest)
    return [apply_output(a, dest, strip_prefix=prefix) for a in answers]


def _as_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def feedback_text(sr: ScoreResult) -> str:
    """What CI would show for a failed answer: result, checks, errors, tails."""
    parts = [f"Result: {sr.reason}"]
    if sr.checks:
        ok = [k for k, v in sr.checks.items() if v]
        bad = [k for k, v in sr.checks.items() if not v]
        if bad:
            parts.append("Failed checks: " + ", ".join(bad))
        if ok:
            parts.append("Passed checks: " + ", ".join(ok))
    d = sr.details or {}
    for key, label in (("edit_failures", "Edits that did not apply"),
                       ("javax_hits", "Old javax.* packages still used"),
                       ("build_errors", "Build errors"),
                       ("tests_run", "Tests run"),
                       ("e2e", "End-to-end"),
                       ("e2e_tests", "End-to-end tests"),
                       ("parity", "Parity"),
                       ("parity_tests", "Parity tests")):
        if d.get(key):
            parts.append(f"{label}:\n{_as_text(d[key])}")
    for key in ("build_tail", "e2e_tail", "parity_tail"):
        if d.get(key):
            parts.append(f"Output tail ({key}):\n{str(d[key])[-MAX_TAIL_CHARS:]}")
    text = "\n\n".join(parts)
    if len(text) > MAX_FEEDBACK_CHARS:
        text = text[:MAX_FEEDBACK_CHARS - 30] + "\n... (feedback truncated)"
    return text


def context_files(tree: Path, feedback: str) -> dict[str, str]:
    """Current content of the files the feedback names (in the order it names
    them), then the build files. The hidden test suite is never included."""
    named: list[tuple[int, str]] = []
    for path in tree.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(tree).as_posix()
        if rel.startswith(HIDDEN_PREFIXES) or "/node_modules/" in rel or "/target/" in rel:
            continue
        # Errors name a file by its project path (/w/src/main/java/...) or, for
        # Spring config, by its classpath path ("class path resource
        # [config/application-dev.yml]").
        names = [rel] + [rel[len(root):] for root in CLASSPATH_ROOTS if rel.startswith(root)]
        hits = [at for n in names if (at := feedback.find(n)) >= 0]
        if hits:
            named.append((min(hits), rel))
    order = [rel for _, rel in sorted(named)]
    order += [b for b in BUILD_FILES if (tree / b).is_file() and b not in order]

    files: dict[str, str] = {}
    total = 0
    for rel in order:
        if len(files) >= MAX_CONTEXT_FILES:
            break
        try:
            text = (tree / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if files and total + len(text) > MAX_CONTEXT_CHARS:
            continue
        files[rel] = text
        total += len(text)
    return files


def repair_prompt(case_id: str, feedback: str, files: dict[str, str], round_no: int) -> str:
    """The task statement, what CI reported, and the files involved as they are now."""
    task = (case_dir(case_id) / "prompt.md").read_text(encoding="utf-8").strip()
    lines = [task, "", "---", "",
             f"# Repair round {round_no}: your previous answer did not pass", "",
             "Your previous answer has already been applied to the project"
             + (" (with your earlier fixes)" if round_no > 1 else "")
             + ". CI then reported:", "",
             "````text", feedback, "````", "",
             "## Current content of the files involved", ""]
    for rel, text in files.items():
        lines += [f"### {rel}", f"````{LANG.get(Path(rel).suffix, '')}", text.rstrip("\n"), "````", ""]
    lines += ["## What to do", "",
              "Fix what CI reported. Reply only with `### FILE:`, `### EDIT:` or `### DELETE:` "
              "blocks in the format described above, written against the CURRENT files: your "
              "previous changes are already in place, so do not repeat them. Change only what "
              "the fix needs. Do not write or edit anything under `src/test/`."]
    return "\n".join(lines) + "\n"


def _record_path(pair_id: str, source_run: str, rec: dict, round_no: int) -> Path:
    rep = int(rec.get("rep", 0) or 0)
    name = (f"{rec['model_slug'].replace('/', '__')}.{rec['case_id']}.{source_run}"
            f"{f'.r{rep}' if rep else ''}.round{round_no}.json")
    return Path(common.RUNS_DIR) / pair_id / "repair" / source_run / name


def _earlier_pass(pair_id: str, source_run: str, rec: dict) -> int | None:
    """The round in which an earlier repair of this answer passed, or None."""
    first = _record_path(pair_id, source_run, rec, 1)
    for path in sorted(first.parent.glob(first.name.replace(".round1.", ".round*."))):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("passed") and (data.get("repair_output") or "").strip():
            return int(data.get("round", 0))
    return None


def repair_run(cfg, pair_id: str, source_run: str, *, rounds: int = 1, case: str | None = None,
               max_repairs: int | None = None, redo: bool = False) -> list[dict]:
    """Repair every failed answer of one run (or one case of it), up to
    `rounds` rounds each, stopping at the first pass. Returns one summary dict
    per answer; each round is saved as its own record."""
    pair = cfg.get_pair(pair_id)
    recs = [r for r in load_runs(pair_id, run=source_run)
            if r.get("case_id") in REPAIRABLE and case in (None, r.get("case_id"))]
    recs.sort(key=lambda r: (r.get("case_id", ""), r.get("role", ""), int(r.get("rep", 0) or 0)))
    results: list[dict] = []
    repaired = 0
    preflight_done = False
    for rec in recs:
        cid = rec["case_id"]
        info = {"case_id": cid, "rep": int(rec.get("rep", 0) or 0), "role": rec.get("role"),
                "model_name": rec.get("model_name"), "effort": reasoning_level(rec),
                "source_file": rec.get("_file"), "single_shot_passed": False, "passed": False,
                "rounds_used": 0, "repair_latency_s": 0.0, "repair_cost_usd": 0.0,
                "first_error": "", "final_reason": ""}
        if is_infra_error(rec):
            results.append({**info, "status": "infra error: re-run instead of repairing",
                            "final_reason": rec.get("error") or ""})
            continue
        text0 = rec.get("output_text") or ""
        if not text0.strip():
            results.append({**info, "status": "no answer to repair (empty completion)",
                            "final_reason": rec.get("error") or ""})
            continue
        sr = score_case(cid, text0, rec.get("model_slug", ""))
        if sr.passed:
            results.append({**info, "status": "passed single-shot", "single_shot_passed": True,
                            "passed": True, "final_reason": sr.reason})
            continue
        info["first_error"] = next(iter((sr.details or {}).get("build_errors") or []), sr.reason)
        if not redo and (done := _earlier_pass(pair_id, source_run, rec)):
            results.append({**info, "status": f"repaired earlier (round {done})", "passed": True,
                            "rounds_used": done, "final_reason": "passed in an earlier repair"})
            continue
        if max_repairs is not None and repaired >= max_repairs:
            results.append({**info, "status": "not repaired (--max-repairs)",
                            "final_reason": sr.reason})
            continue
        repaired += 1

        model = pair.current if rec.get("role") == "current" else pair.target
        api = cfg.api_for(model)
        provider_prefs, reasoning_prefs, extra_params = runner.call_prefs(
            cfg, pair_id, model, rec.get("effort_override"))
        # A re-repair replaces the answer's earlier attempt: drop its old round
        # records, or a stale later round would read as part of this attempt.
        for stale in _record_path(pair_id, source_run, rec, 1).parent.glob(
                _record_path(pair_id, source_run, rec, 1).name.replace(".round1.", ".round*.")):
            stale.unlink()
        answers = [text0]
        single_reason = sr.reason
        status = "still failing"
        for round_no in range(1, rounds + 1):
            with tempfile.TemporaryDirectory(prefix="gate1-repair-") as tmp:
                tree = Path(tmp) / "tree"
                build_tree(cid, answers, tree)
                feedback = feedback_text(sr)
                files = context_files(tree, feedback)
                prompt = repair_prompt(cid, feedback, files, round_no)
                if not preflight_done and api is not None and api.family == "claude-code":
                    runner.claude_code_preflight()
                    preflight_done = True
                call = runner.call_model(
                    model.id, prompt, temperature=cfg.temperature,
                    max_tokens=cfg.max_tokens_for(model.id), timeout_s=cfg.timeout_s_for(pair_id),
                    max_retries=cfg.max_retries, backoff_base_s=cfg.backoff_base_s,
                    provider_prefs=provider_prefs, reasoning=reasoning_prefs, api=api,
                    session=f"repair-{source_run}", extra_params=extra_params,
                    measure_thinking=cfg.thinking_time)
                if call.stop_run:
                    raise runner.UsageLimitReached(call.stop_run)
                answer = call.text or ""
                if answer.strip():
                    sr = score_case(cid, answer, rec.get("model_slug", ""), base=tree)
                else:
                    sr = ScoreResult(case_id=cid, reason=f"no repair answer: {call.error}")
            info["rounds_used"] = round_no
            info["repair_latency_s"] += call.latency_s
            info["repair_cost_usd"] += call.cost_estimate_usd or call.billed_cost_usd or 0.0
            record = {
                "pair_id": pair_id, "case_id": cid, "model_slug": rec.get("model_slug"),
                "model_name": rec.get("model_name"), "role": rec.get("role"),
                "suite": cfg.suite, "rep": info["rep"], "source_run": source_run,
                "source_file": rec.get("_file"), "round": round_no,
                "effort_override": rec.get("effort_override"),
                "reasoning_requested": reasoning_prefs,
                "single_shot_reason": single_reason, "feedback": feedback,
                "context_files": list(files), "prompt_chars": len(prompt),
                "repair_output": answer, "finish_reason": call.finish_reason,
                "error": call.error, "latency_s": round(call.latency_s, 4),
                "thinking_time_s": call.thinking_time_s, "execution_time_s": call.execution_time_s,
                "reasoning_tokens": call.reasoning_tokens, **call.usage,
                "cost_estimate_usd": call.cost_estimate_usd, "billed_cost_usd": call.billed_cost_usd,
                "provider": call.provider, "passed": sr.passed, "reason": sr.reason,
                "checks": sr.checks, "edit_failures": (sr.details or {}).get("edit_failures"),
                "created_at": time.time(),
            }
            path = _record_path(pair_id, source_run, rec, round_no)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            if not answer.strip():
                status = f"repair call failed: {call.error}"
                break
            answers.append(answer)
            if sr.passed:
                status = "repaired"
                break
        results.append({**info, "status": status, "passed": sr.passed,
                        "final_reason": sr.reason})
    return results


def render_report(pair_id: str, source_run: str, results: list[dict]) -> str:
    """Single-shot vs after-repair, per case and per answer."""
    lines = [f"# Repair rounds — {pair_id} · run {source_run}", "",
             "A failed answer's model is shown what CI reported (failed checks, build/test "
             "output) and the current files the errors point at, and replies with fix-up "
             "blocks, scored on top of its earlier answer. This is a separate, agentic "
             "measurement: never part of REPORT.md, the effort sweep or the overall score. "
             "Infra errors are left out; an answer with nothing to repair counts as a fail.", "",
             "## Summary", "",
             "| Case | Single-shot | After repair | Repair calls | Repair time (s) | Repair cost (USD) |",
             "|---|---:|---:|---:|---:|---:|"]
    for cid in dict.fromkeys(r["case_id"] for r in results):
        mine = [r for r in results if r["case_id"] == cid and not r["status"].startswith("infra")]
        single = sum(r["single_shot_passed"] for r in mine)
        after = sum(r["passed"] for r in mine)
        calls = sum(r["rounds_used"] for r in mine)
        secs = sum(r["repair_latency_s"] for r in mine)
        cost = sum(r["repair_cost_usd"] for r in mine)
        lines.append(f"| {cid} | {single}/{len(mine)} | {after}/{len(mine)} | {calls} | "
                     f"{secs:.0f} | ${cost:.2f} |")
    lines += ["", "## Per answer", "",
              "| Case | Rep | Model | Effort | Single-shot | Rounds | After repair | Status | "
              "First error fed back | Final result |",
              "|---|---:|---|---|---|---:|---|---|---|---|"]
    for r in results:
        first = (r["first_error"] or "").replace("|", "\\|")[:140]
        final = (r["final_reason"] or "").replace("|", "\\|")[:140]
        lines.append(f"| {r['case_id']} | {r['rep'] + 1} | {r['model_name']} | {r['effort']} | "
                     f"{'✅' if r['single_shot_passed'] else '❌'} | {r['rounds_used']} | "
                     f"{'✅' if r['passed'] else '❌'} | {r['status']} | {first} | {final} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gate 1 CI-style repair rounds (separate from scoring)")
    ap.add_argument("--pair", required=True)
    ap.add_argument("--run", required=True, help="run id whose failed answers to repair")
    ap.add_argument("--suite", default=None)
    ap.add_argument("--case", choices=sorted(REPAIRABLE), help="repair one case only")
    ap.add_argument("--rounds", type=int, default=1, help="repair rounds per answer (default 1)")
    ap.add_argument("--redo", action="store_true",
                    help="repair answers again even if an earlier repair already passed")
    ap.add_argument("--max-repairs", type=int, default=None, metavar="N",
                    help="repair at most N answers (a smoke test)")
    args = ap.parse_args(argv)

    load_env()
    cfg = load_config(suite=args.suite)
    try:
        results = repair_run(cfg, args.pair, args.run, rounds=args.rounds, case=args.case,
                             max_repairs=args.max_repairs, redo=args.redo)
    except runner.UsageLimitReached as exc:
        print(f"stopped: {exc}. Repair records written so far are kept.", file=sys.stderr)
        return 3
    except (ValueError, runner.ClaudeCodeNotReady) as exc:
        print(f"not run: {exc}", file=sys.stderr)
        return 2
    out = Path(common.RUNS_DIR) / args.pair / "repair" / args.run / "REPORT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(args.pair, args.run, results), encoding="utf-8")
    print(f"wrote {out}")
    for r in results:
        print(f"  {r['case_id']} rep {r['rep'] + 1}: {r['status']}"
              f"{' (' + r['final_reason'][:100] + ')' if not r['passed'] else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
