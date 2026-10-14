"""scorers/r1b_scorer.py — real-project Spring Boot 2.7 → 3 migration (JHipster sample app).

The input is the backend of jhipster/jhipster-sample-app v7.9.3 (Boot 2.7.3,
Java 11), fetched from our fork (abralock/jhipster-sample-app, see
cases/sources.py) into cases/r1b_jhipster_boot3/project/. The model answers
with FILE / EDIT / DELETE blocks, applied on top of a copy of that project.
Then, in order (a failed stage fails every later one):

  * static: Boot 3 in the pom, Java 17, every EDIT applied, no Jakarta EE API
    still used through its old `javax.*` package in src/main;
  * build: the project's own test sources are replaced by the hidden, already
    migrated suite (scorers/fixtures/r1b_hidden_tests/) and `mvn -P-webapp
    verify` runs it: checkstyle, modernizer, 52 unit tests (surefire) and 140
    integration tests on H2 (failsafe). Each must run at least that many tests.
  * e2e: the unchanged Angular frontend (prebuilt once, see setup_e2e.sh) is
    packaged into the jar, the app starts with the `dev` profile, and the
    project's own Cypress suite (54 tests) runs against it.

Maven runs in Docker (maven:3.8.6-eclipse-temurin-17, the project's wrapper
version; override with R1B_MAVEN_IMAGE), which also sandboxes model-written
code. Without Docker, or without the e2e cache, the affected checks FAIL as
unverified: a scorer never awards a pass for a check it did not run.

Usage:
    python -m scorers.r1b_scorer --output-file <model-output.txt>
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from cases import sources

from .base import ScoreResult, apply_output, cache_dir, cli, parse_edits, parse_files
from .base import run_command as _run

CASE_ID = "r1b_jhipster_boot3"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID
PROJECT = CASE_DIR / "project"
HIDDEN_TESTS = Path(__file__).resolve().parent / "fixtures" / "r1b_hidden_tests"
MAVEN_IMAGE = os.environ.get("R1B_MAVEN_IMAGE", "maven:3.8.6-eclipse-temurin-17")
M2_VOLUME = "aidb_m2"                    # shared with R1: dependency cache across runs
FRONTEND = cache_dir() / CASE_ID / "frontend"   # created by cases/r1b_jhipster_boot3/setup_e2e.sh
MIN_UNIT, MIN_IT, MIN_E2E = 52, 140, 54
BUILD_TIMEOUT_S, E2E_TIMEOUT_S = 2400, 1200

# Jakarta EE APIs that moved javax.* -> jakarta.* (JSR-305 javax.annotation.Nonnull,
# javax.cache, javax.sql etc. did not move and are fine).
_JAVAX_EE_RE = re.compile(
    r"\bjavax\.(persistence|validation|servlet|mail|transaction|ws\.rs|inject|xml\.bind|activation"
    r"|annotation\.(PostConstruct|PreDestroy|Generated|Resource|Priority|ManagedBean|security))\b"
)
_COMMENT_LINE_RE = re.compile(r"^\s*(//|/\*|\*)")
_SUMMARY_RE = re.compile(r"^\[(?:INFO|WARNING|ERROR)\] Tests run: (\d+), Failures: (\d+), Errors: (\d+), "
                         r"Skipped: (\d+)\s*$", re.MULTILINE)
_CYPRESS_TOTAL_RE = re.compile(r"(?:All specs passed!|\d+ of \d+ failed \(\d+%\))\s+[\d:]+\s+(\d+)\s+(\d+)\s+(\d+|-)")


def _mvn(project: Path, *args: str) -> list[str]:
    return ["docker", "run", "--rm", "-v", f"{project}:/w", "-v", f"{M2_VOLUME}:/root/.m2", "-w", "/w",
            MAVEN_IMAGE, "mvn", "-B", "-ntp", *args]


def _reclaim(project: Path) -> None:
    """Give files the root-run Maven/app containers wrote back to us, so cleanup works."""
    _run(["docker", "run", "--rm", "-v", f"{project}:/w", MAVEN_IMAGE,
          "chown", "-R", f"{os.getuid()}:{os.getgid()}", "/w"], timeout=300)


def boot_version(pom: str) -> str | None:
    """Spring Boot version: the `spring-boot.version` property or the starter parent."""
    m = re.search(r"<spring-boot\.version>\s*([^<\s]+)\s*</spring-boot\.version>", pom) or re.search(
        r"<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([^<]+)</version>", pom)
    return m.group(1).strip() if m else None


def java_version(pom: str) -> int | None:
    m = re.search(r"<java\.version>\s*(\d+)\s*</java\.version>", pom)
    return int(m.group(1)) if m else None


def test_summaries(mvn_output: str) -> list[tuple[int, int, int]]:
    """(run, failures, errors) per surefire/failsafe "Results:" summary, in order."""
    return [(int(r), int(f), int(e)) for r, f, e, _ in _SUMMARY_RE.findall(mvn_output)]


def cypress_totals(output: str) -> tuple[int, int, int] | None:
    """(tests, passing, failing) from Cypress's final run table, or None."""
    clean = re.sub(r"\x1b\[[0-9;]*m", "", output)
    m = _CYPRESS_TOTAL_RE.search(clean)
    if not m:
        return None
    failing = 0 if m.group(3) == "-" else int(m.group(3))
    return int(m.group(1)), int(m.group(2)), failing


def javax_hits(project: Path) -> list[str]:
    hits: list[str] = []
    for f in sorted((project / "src" / "main").rglob("*.java")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if _JAVAX_EE_RE.search(line) and not _COMMENT_LINE_RE.match(line):
                hits.append(f"{f.relative_to(project)}:{i}: {line.strip()}")
    return hits


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_http(url: str, timeout_s: int) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:  # noqa: S310 - local health probe
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def http_status(url: str) -> int | None:
    """Status code of a GET (errors included), or None if nothing answered."""
    try:
        with urllib.request.urlopen(url, timeout=10) as r:  # noqa: S310 - local probe
            return r.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return None


def run_e2e(project: Path, res: ScoreResult) -> bool:
    """Package the jar with the prebuilt frontend, start it, run the Cypress suite."""
    static = FRONTEND / "target" / "classes" / "static"
    if not (static / "index.html").is_file() or not (FRONTEND / "node_modules" / ".bin" / "cypress").exists():
        res.details["e2e"] = f"e2e cache missing at {FRONTEND}; run cases/{CASE_ID}/setup_e2e.sh (UNVERIFIED)"
        return False
    _reclaim(project)   # `verify` ran as root in Docker: target/ is root's until we take it back
    shutil.copytree(static, project / "target" / "classes" / "static", dirs_exist_ok=True)
    rc, out = _run(_mvn(project, "-P-webapp", "-DskipTests", "-Dcheckstyle.skip", "-Dmodernizer.skip",
                        "-Djacoco.skip", "package"), timeout=BUILD_TIMEOUT_S)
    jars = sorted((project / "target").glob("*.jar"))
    if rc != 0 or not jars:
        res.details["e2e"] = "packaging the app jar failed"
        res.details["e2e_tail"] = out[-1500:]
        return False

    port, name = _free_port(), f"r1b-app-{uuid.uuid4().hex[:8]}"
    rc, out = _run(["docker", "run", "-d", "--rm", "--name", name, "-p", f"127.0.0.1:{port}:8080",
                    "-v", f"{project}:/w", "-w", "/w", MAVEN_IMAGE,
                    "java", "-jar", f"target/{jars[0].name}", "--spring.profiles.active=dev"])
    if rc != 0:
        res.details["e2e"] = f"could not start the app container: {out[-300:]}"
        return False
    try:
        if not _wait_http(f"http://127.0.0.1:{port}/management/health", 240):
            _, logs = _run(["docker", "logs", "--tail", "60", name])
            res.details["e2e"] = "app did not become healthy within 240s"
            res.details["e2e_tail"] = logs[-1500:]
            return False
        # Every spec starts with cy.visit('/'), which needs a 2xx. If the app does not serve
        # the frontend, all 54 tests fail anyway, slowly (each waits out its timeouts, then
        # retries twice), and the run outlasts E2E_TIMEOUT_S: fail now with the real reason.
        status = http_status(f"http://127.0.0.1:{port}/")
        if status != 200:
            res.details["e2e"] = f"GET / returned {status}: the app does not serve the frontend (Cypress not run)"
            return False
        env = dict(os.environ, CYPRESS_baseUrl=f"http://localhost:{port}/", NO_COLOR="1")
        rc, out = _run(["npx", "cypress", "run", "--e2e", "--browser", "chrome",
                        "--config", f"baseUrl=http://localhost:{port}/"],
                       cwd=FRONTEND, timeout=E2E_TIMEOUT_S, env=env)
        totals = cypress_totals(out)
        res.details["e2e_tests"] = ({"tests": totals[0], "passing": totals[1], "failing": totals[2]}
                                    if totals else None)
        res.details["e2e_tail"] = re.sub(r"\x1b\[[0-9;]*m", "", out)[-2000:]
        return rc == 0 and totals is not None and totals[2] == 0 and totals[1] >= MIN_E2E
    finally:
        _run(["docker", "rm", "-f", name])


def score(output_text: str, *, model_slug: str = "", workdir: Path | None = None) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)
    if not parse_files(output_text) and not parse_edits(output_text):
        res.reason = "no `### FILE:` or `### EDIT:` blocks found in model output"
        return res

    tmp = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="r1b_"))
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        sources.ensure(CASE_ID)                 # fetched from the fork, see cases/sources.py
        shutil.copytree(PROJECT, tmp, dirs_exist_ok=True)
        applied = apply_output(output_text, tmp, strip_prefix="project/")
        res.details.update(files_written=applied.written, files_deleted=applied.deleted,
                           files_edited=sorted(set(applied.edited)),
                           edit_failures=applied.edit_failures[:25])

        # --- static ----------------------------------------------------------- #
        pom = (tmp / "pom.xml").read_text(encoding="utf-8") if (tmp / "pom.xml").is_file() else ""
        boot = boot_version(pom)
        res.details["spring_boot_version"] = boot
        res.checks["edits_applied"] = not applied.edit_failures
        res.checks["boot3"] = bool(boot and boot.startswith("3."))
        res.checks["java17"] = (java_version(pom) or 0) >= 17
        hits = javax_hits(tmp)
        res.checks["javax_free"] = not hits
        res.details["javax_hits"] = hits[:25]

        # --- build + hidden test suite ---------------------------------------- #
        test_dir = tmp / "src" / "test"
        shutil.rmtree(test_dir, ignore_errors=True)
        shutil.copytree(HIDDEN_TESTS, test_dir, copy_function=shutil.copy)
        if not shutil.which("docker"):
            res.details["maven"] = "docker unavailable: build/tests/e2e UNVERIFIED (fail)"
            for k in ("build", "unit_tests", "integration_tests", "e2e"):
                res.checks[k] = False
        else:
            rc, out = _run(_mvn(tmp, "-P-webapp", "verify"), timeout=BUILD_TIMEOUT_S)
            sums = test_summaries(out)
            unit = sums[0] if sums else (0, 0, 0)
            it = sums[1] if len(sums) > 1 else (0, 0, 0)
            res.checks["build"] = rc == 0
            res.checks["unit_tests"] = rc == 0 and unit[0] >= MIN_UNIT and unit[1] == unit[2] == 0
            res.checks["integration_tests"] = rc == 0 and it[0] >= MIN_IT and it[1] == it[2] == 0
            res.details["tests_run"] = {"unit": unit[0], "integration": it[0],
                                        "expected_at_least": [MIN_UNIT, MIN_IT]}
            errors = [ln for ln in out.splitlines() if ln.startswith("[ERROR]")]
            res.details["build_errors"] = errors[:30]
            res.details["build_tail"] = out[-1500:]
            res.checks["e2e"] = res.checks["build"] and run_e2e(tmp, res)
    finally:
        if shutil.which("docker"):
            _reclaim(tmp)
        if not workdir:
            shutil.rmtree(tmp, ignore_errors=True)

    required = ["edits_applied", "boot3", "java17", "javax_free", "build", "unit_tests",
                "integration_tests", "e2e"]
    res.passed = all(res.checks.get(k, False) for k in required)
    res.score = sum(bool(res.checks.get(k)) for k in required) / len(required)
    if res.passed:
        res.reason = (f"migrated to Boot {boot}: build, {MIN_UNIT}+ unit, {MIN_IT}+ integration "
                      f"and {MIN_E2E}+ Cypress e2e tests pass")
    else:
        failed = [k for k in required if not res.checks.get(k)]
        res.reason = "failed checks: " + ", ".join(failed)
        if applied_failures := res.details.get("edit_failures"):
            res.reason += f" ({len(applied_failures)} edit(s) did not apply)"
        if "maven" in res.details or "UNVERIFIED" in str(res.details.get("e2e", "")):
            res.reason += " (unverified: missing docker or e2e cache)"
    return res


if __name__ == "__main__":
    raise SystemExit(cli(score))
