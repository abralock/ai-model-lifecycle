"""scorers/r1_scorer.py — Spring Boot 2.7 → 3.x migration scorer.

Takes the model's raw output (the `### FILE:` / `### DELETE:` blocks) and applies
it as a patch: the frozen input module is copied to a temp dir, deleted paths are
removed, and emitted files overwrite/add on top. Untouched input files therefore
stay in the build, exactly as in a real migration. Then:

  * static checks on the RESULTING tree: Boot 3 parent, no code use of the
    Jakarta-renamed `javax.{persistence,validation,annotation,servlet}` packages
    under src/ (comments and JDK packages such as `javax.sql` are fine), no
    `spring.factories` left;
  * `mvn -q -DskipTests compile` then `mvn test`, which must pass AND actually
    run at least as many tests as the input module defines. (Under Boot 2.7's
    Jupiter-only test starter the JUnit 4 input tests run 0 times, so "tests
    pass" alone is vacuous: an unmigrated test suite would sail through.)
  * hidden tests: the model's test sources are replaced by the input's own
    tests migrated to JUnit 5 (`scorers/fixtures/r1_hidden_tests/`, never shown
    to models) and `mvn test` runs again. This checks business behavior
    survived; a model that invents classes instead of migrating them fails.

Maven runs locally if `mvn` is on PATH, otherwise inside a throwaway Docker
container (`maven:3.9-eclipse-temurin-17`, override with R1_MAVEN_IMAGE). The
container also sandboxes model-written build code from the host.

If neither is available, compile/test are UNVERIFIED and the case FAILS: a
scorer must never award a pass for a check it did not run.

Usage:
    python -m scorers.r1_scorer --output-file <model-output.txt>
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import ScoreResult, cli, parse_deletes, parse_files, write_files

CASE_ID = "r1_springboot2to3"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID
CASE_META_FILES = ("prompt.md", "README.md")   # task docs, not part of the module
MAVEN_IMAGE = os.environ.get("R1_MAVEN_IMAGE", "maven:3.9-eclipse-temurin-17")
HIDDEN_TESTS = Path(__file__).resolve().parent / "fixtures" / "r1_hidden_tests"
M2_VOLUME = "aidb_m2"                          # dependency cache shared across runs
_JAVAX_EE_RE = re.compile(r"\bjavax\.(persistence|validation|annotation|servlet)\b")
_COMMENT_LINE_RE = re.compile(r"^\s*(//|/\*|\*|#|<!--)")
_SUREFIRE_RE = re.compile(r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+)")


def expected_test_count() -> int:
    """Number of @Test methods in the frozen input's test sources."""
    return sum(
        f.read_text(encoding="utf-8").count("@Test")
        for f in (CASE_DIR / "src" / "test").rglob("*.java")
    )


def tests_run(mvn_output: str) -> int:
    """Total tests run per the final surefire summary line (0 if none found)."""
    hits = _SUREFIRE_RE.findall(mvn_output)
    return int(hits[-1][0]) if hits else 0


def _run(cmd: list[str], cwd: Path, timeout: int = 900) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s: {' '.join(cmd)}"


def _maven_argv(project: Path) -> list[str] | None:
    """argv prefix that runs Maven on `project`, or None if no Maven is available."""
    if shutil.which("mvn"):
        return ["mvn", "-B"]
    if shutil.which("docker"):
        return [
            "docker", "run", "--rm",
            "-v", f"{project}:/w", "-v", f"{M2_VOLUME}:/root/.m2", "-w", "/w",
            MAVEN_IMAGE, "mvn", "-B",
        ]
    return None


def _boot3_in_pom(pom: str) -> bool:
    m = re.search(
        r"<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([^<]+)</version>",
        pom,
    )
    return bool(m) and m.group(1).strip().startswith("3.")


def materialize(output_text: str, dest: Path) -> tuple[list[str], list[str]]:
    """Copy the frozen module into `dest`, apply DELETEs, overlay emitted files."""
    shutil.copytree(
        CASE_DIR, dest, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*CASE_META_FILES),
    )
    dest_r = dest.resolve()
    deleted: list[str] = []
    for rel in parse_deletes(output_text):
        target = (dest_r / rel).resolve()
        if str(target).startswith(str(dest_r)) and target.is_file():
            target.unlink()
            deleted.append(rel)
    written = write_files(parse_files(output_text), dest)
    return written, deleted


def score(output_text: str, *, model_slug: str = "", workdir: Path | None = None) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)

    if not parse_files(output_text):
        res.reason = "no `### FILE:` blocks found in model output"
        return res

    tmp = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="r1_"))
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        written, deleted = materialize(output_text, tmp)
        res.details["files_written"] = written
        res.details["files_deleted"] = deleted

        # --- static checks on the resulting tree -------------------------- #
        pom = tmp / "pom.xml"
        res.checks["has_pom"] = pom.is_file()
        res.checks["boot3_pom"] = pom.is_file() and _boot3_in_pom(pom.read_text(encoding="utf-8"))

        javax_hits: list[str] = []
        for f in sorted((tmp / "src").rglob("*")):
            if f.is_file() and f.suffix in (".java", ".xml", ".properties"):
                for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if _JAVAX_EE_RE.search(line) and not _COMMENT_LINE_RE.match(line):
                        javax_hits.append(f"{f.relative_to(tmp)}:{i}: {line.strip()}")
        res.checks["javax_free"] = not javax_hits
        res.details["javax_hits"] = javax_hits[:25]

        leftover = [str(p.relative_to(tmp)) for p in (tmp / "src").rglob("spring.factories")]
        res.checks["factories_gone"] = not leftover
        res.details["factories_left"] = leftover

        # --- dynamic checks (compile + test) ------------------------------ #
        mvn = _maven_argv(tmp)
        if mvn is None:
            res.details["maven"] = "no mvn and no docker — compile/test UNVERIFIED (fail)"
            res.checks["compile"] = False
            res.checks["tests"] = False
            res.checks["tests_executed"] = False
            res.checks["hidden_tests"] = False
        else:
            rc_c, out_c = _run(mvn + ["-q", "-DskipTests", "compile"], tmp)
            res.checks["compile"] = rc_c == 0
            res.details["compile_tail"] = out_c[-1500:]
            if rc_c == 0:
                rc_t, out_t = _run(mvn + ["test"], tmp)
                ran, expected = tests_run(out_t), expected_test_count()
                res.checks["tests"] = rc_t == 0
                res.checks["tests_executed"] = ran >= expected
                res.details["tests_run"] = {"ran": ran, "expected_at_least": expected}
                res.details["test_tail"] = out_t[-1500:]
            else:
                res.checks["tests"] = False
                res.checks["tests_executed"] = False

            if rc_c == 0:
                test_root = tmp / "src" / "test" / "java"
                shutil.rmtree(test_root, ignore_errors=True)
                # drop compiled model tests too: copytree's default copy2 keeps
                # the fixtures' old mtimes, so Maven would skip recompiling and
                # rerun the model's stale test classes
                shutil.rmtree(tmp / "target" / "test-classes", ignore_errors=True)
                shutil.copytree(HIDDEN_TESTS, test_root, copy_function=shutil.copy)
                rc_h, out_h = _run(mvn + ["test"], tmp)
                ran_h = tests_run(out_h)
                res.checks["hidden_tests"] = rc_h == 0 and ran_h >= expected_test_count()
                res.details["hidden_tests_run"] = ran_h
                res.details["hidden_test_tail"] = out_h[-1500:]
            else:
                res.checks["hidden_tests"] = False
    finally:
        if not workdir:
            shutil.rmtree(tmp, ignore_errors=True)

    # --- verdict ------------------------------------------------------------ #
    required = ["has_pom", "boot3_pom", "javax_free", "factories_gone", "compile", "tests",
                "tests_executed", "hidden_tests"]
    res.passed = all(res.checks.get(k, False) for k in required)
    res.score = 1.0 if res.passed else 0.0
    if not res.passed:
        failed = [k for k in required if not res.checks.get(k)]
        res.reason = "failed checks: " + ", ".join(failed)
        if "maven" in res.details:
            res.reason += " (maven unavailable: unverified)"
    else:
        res.reason = "migrated cleanly: compiles, tests pass, no javax, no spring.factories"
    return res


if __name__ == "__main__":
    raise SystemExit(cli(score))
