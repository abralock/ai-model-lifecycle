"""scorers/r2_scorer.py — real-project GWT → Angular migration (GWTP carstore).

The input is three screens of the GWTP "carstore" sample (ArcBees/GWTP-Samples
@ 7dce06a, GWT 2.7): Manufacturers (list + editor popup), Ratings (list +
create form) and Reports (average rating per manufacturer), frozen under
cases/r2_gwt_to_angular/gwt/. The model writes an Angular 18 app into the
fixed workspace (cases/r2_gwt_to_angular/workspace/), as FILE / EDIT blocks
under src/app/. Then:

  * build: the workspace's fixed config files are restored (package.json,
    angular.json, tsconfig*, src/main.ts, src/index.html), and `ng build` runs
    in a network-less Node 20 container against cached node_modules;
  * parity: the build is served at /ng/ by the original app's own server (the
    App Engine dev server running the GWT war, which also serves the REST API
    at /api), seeded fresh, and the hidden Playwright parity suite
    (scorers/fixtures/r2_parity/, 8 tests ported from the app's Cucumber
    features) runs against it. All 8 must pass.

`python -m scorers.r2_scorer --baseline` runs the same suite against the GWT
original instead, which is how the suite itself was validated.

Everything large lives in the cache built by cases/r2_gwt_to_angular/setup.sh.
Without Docker or the cache the checks FAIL as unverified.

Usage:
    python -m scorers.r2_scorer --output-file <model-output.txt>
    python -m scorers.r2_scorer --baseline
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

from .base import ScoreResult, apply_output, cache_dir, cli, parse_edits, parse_files

CASE_ID = "r2_gwt_to_angular"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID
WORKSPACE = CASE_DIR / "workspace"
PARITY = Path(__file__).resolve().parent / "fixtures" / "r2_parity"
CACHE = cache_dir() / CASE_ID
NODE_IMAGE = os.environ.get("R2_NODE_IMAGE", "node:20.18.0-bookworm-slim")
JAVA8_IMAGE = os.environ.get("R2_JAVA8_IMAGE", "maven:3.8-openjdk-8")
FIXED_FILES = ("package.json", "package-lock.json", "angular.json", "tsconfig.json",
               "tsconfig.app.json", "src/main.ts", "src/index.html")
MIN_PARITY = 8
BUILD_TIMEOUT_S, PARITY_TIMEOUT_S = 900, 900


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 900,
         env: dict[str, str] | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s: {' '.join(cmd[:6])} ..."


def cache_problem() -> str | None:
    need = {
        "carstore-war/CarStore.html": "GWT app war",
        "gae-sdk/appengine-java-sdk-1.9.17/bin/dev_appserver.sh": "App Engine SDK",
        "deps/node_modules/@angular/cli/package.json": "Angular node_modules",
        "e2e/node_modules/@playwright/test/package.json": "Playwright",
    }
    missing = [what for rel, what in need.items() if not (CACHE / rel).exists()]
    if not shutil.which("docker"):
        missing.append("docker")
    if missing:
        return f"missing {', '.join(missing)}; run cases/{CASE_ID}/setup.sh (UNVERIFIED)"
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_http(url: str, timeout_s: int) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:  # noqa: S310 - local probe
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False


def build_angular(ws: Path, res: ScoreResult) -> Path | None:
    """`ng build` the workspace in a network-less container; return the browser dist dir."""
    rc, out = _run(["docker", "run", "--rm", "--network", "none", "-u", f"{os.getuid()}:{os.getgid()}",
                    "-e", "HOME=/tmp", "-e", "NG_CLI_ANALYTICS=false",
                    "-v", f"{ws}:/w", "-v", f"{CACHE / 'deps' / 'node_modules'}:/w/node_modules:ro",
                    "-w", "/w", NODE_IMAGE, "node_modules/.bin/ng", "build"], timeout=BUILD_TIMEOUT_S)
    res.details["build_tail"] = out[-2500:]
    dist = ws / "dist" / "carstore" / "browser"
    if rc != 0 or not (dist / "index.html").is_file():
        return None
    return dist


def run_parity(base_path: str, angular_dist: Path | None, res: ScoreResult) -> bool:
    """Serve the GWT war (+ the Angular build at /ng/) fresh, run the parity suite."""
    work = Path(tempfile.mkdtemp(prefix="r2_serve_"))
    name = f"r2-gae-{uuid.uuid4().hex[:8]}"
    run_dir = CACHE / "e2e" / f"run-{uuid.uuid4().hex[:8]}"   # under e2e/ so @playwright/test resolves
    try:
        war = work / "war"
        shutil.copytree(CACHE / "carstore-war", war)           # fresh copy = fresh, re-seeded datastore
        if angular_dist is not None:
            shutil.copytree(angular_dist, war / "ng")
        port = _free_port()
        rc, out = _run(["docker", "run", "-d", "--rm", "--name", name, "-p", f"127.0.0.1:{port}:8888",
                        "-u", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
                        "-v", f"{CACHE / 'gae-sdk'}:/sdk:ro", "-v", f"{war}:/war", JAVA8_IMAGE,
                        "bash", "/sdk/appengine-java-sdk-1.9.17/bin/dev_appserver.sh",
                        "--address=0.0.0.0", "--port=8888", "/war"])
        if rc != 0:
            res.details["parity"] = f"could not start the app server: {out[-300:]}"
            return False
        base_url = f"http://127.0.0.1:{port}{base_path}"
        if not _wait_http(f"http://127.0.0.1:{port}/api/manufacturers", 120) or not _wait_http(base_url, 30):
            res.details["parity"] = f"app server not ready at {base_url}"
            return False

        shutil.copytree(PARITY, run_dir)
        report = run_dir / "report.json"
        env = dict(os.environ, BASE_URL=base_url, PARITY_REPORT=str(report))
        rc, out = _run(["npx", "playwright", "test", "--config", str(run_dir / "playwright.config.ts")],
                       cwd=CACHE / "e2e", timeout=PARITY_TIMEOUT_S, env=env)
        res.details["parity_tail"] = out[-2500:]
        passed, failed = parity_counts(report)
        res.details["parity_tests"] = {"passed": passed, "failed": failed, "expected": MIN_PARITY}
        return rc == 0 and failed == 0 and passed >= MIN_PARITY
    finally:
        _run(["docker", "rm", "-f", name])
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(work, ignore_errors=True)


def parity_counts(report: Path) -> tuple[int, int]:
    """(passed, failed) from Playwright's JSON reporter output; (0, 0) if unreadable."""
    try:
        stats = json.loads(report.read_text(encoding="utf-8")).get("stats", {})
    except (OSError, json.JSONDecodeError):
        return 0, 0
    return int(stats.get("expected", 0)), int(stats.get("unexpected", 0)) + int(stats.get("flaky", 0))


def score(output_text: str, *, model_slug: str = "", workdir: Path | None = None) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)
    if not parse_files(output_text) and not parse_edits(output_text):
        res.reason = "no `### FILE:` or `### EDIT:` blocks found in model output"
        return res

    ws = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="r2_"))
    ws.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(WORKSPACE, ws, dirs_exist_ok=True)
        applied = apply_output(output_text, ws, strip_prefix="workspace/")
        for rel in FIXED_FILES:                     # the toolchain is fixed: restore it
            shutil.copy(WORKSPACE / rel, ws / rel)
        res.details.update(files_written=applied.written, files_edited=sorted(set(applied.edited)),
                           edit_failures=applied.edit_failures[:25])
        res.checks["edits_applied"] = not applied.edit_failures
        res.checks["has_app"] = all((ws / "src" / "app" / f).is_file()
                                    for f in ("app.component.ts", "app.config.ts"))

        problem = cache_problem()
        if problem:
            res.details["cache"] = problem
            res.checks["build"] = res.checks["parity"] = False
        else:
            dist = build_angular(ws, res)
            res.checks["build"] = dist is not None
            res.checks["parity"] = dist is not None and run_parity("/ng/", dist, res)
    finally:
        if not workdir:
            shutil.rmtree(ws, ignore_errors=True)

    required = ["edits_applied", "has_app", "build", "parity"]
    res.passed = all(res.checks.get(k, False) for k in required)
    res.score = sum(bool(res.checks.get(k)) for k in required) / len(required)
    if res.passed:
        res.reason = f"Angular port builds and passes all {MIN_PARITY} parity tests"
    else:
        failed = [k for k in required if not res.checks.get(k)]
        res.reason = "failed checks: " + ", ".join(failed)
        if pt := res.details.get("parity_tests"):
            res.reason += f" (parity {pt['passed']} passed, {pt['failed']} failed)"
        if "cache" in res.details:
            res.reason += " (unverified: " + res.details["cache"] + ")"
    return res


def baseline() -> int:
    """Run the parity suite against the original GWT app (validates the suite)."""
    res = ScoreResult(case_id=CASE_ID, model_slug="gwt-original")
    problem = cache_problem()
    if problem:
        print(problem, file=sys.stderr)
        return 1
    ok = run_parity("/", None, res)
    print(json.dumps({"passed": ok, **res.details}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--baseline" in sys.argv[1:]:
        raise SystemExit(baseline())
    raise SystemExit(cli(score))
