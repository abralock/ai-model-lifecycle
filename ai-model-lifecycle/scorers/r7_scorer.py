"""scorers/r7_scorer.py — real-project Hibernate 5 → 6 and JUnit 4 → 5 migration (shogun-core).

The input is terrestris/shogun-core at d1881aa (Java 8, Spring 5.3 without
Boot, Spring Security 5.5, Hibernate 5.4, JUnit 4 + PowerMock), fetched from
our fork (abralock/shogun-core, see cases/sources.py) into
cases/r7_shogun_hibernate6/project/. The answer (FILE / EDIT / DELETE blocks;
agentic runs harvest the changed files) is applied on top of a copy of that
project. Then:

  * static: every EDIT applied; no Jakarta EE API still used through its old
    `javax.*` package in shogun-core-main's src/main or src/test; the agent's
    own tests use JUnit 5 only (no `org.junit.*` outside jupiter/platform, no
    PowerMock, none disabled) and no pom declares JUnit 4, the vintage engine
    or PowerMock, or skips or excludes tests;
  * build + own tests: `mvn -B -pl shogun-core-main -am verify` on the
    agent's tree, its own migrated tests included: at least 776 tests (the
    original suite's count) run, none failed, errored or skipped;
  * versions, from the resolved dependencies and the compiled classes:
    Hibernate ORM 6.x, Spring Framework 6.x, Spring Security 6.x, Java 17
    bytecode;
  * grading tests: shogun-core-main/src/test replaced by our own JUnit 5
    migration of the same suite (scorers/fixtures/r7_hidden_tests/, written
    against the public API and the prompt's QueryRestriction/SortOrder types),
    then the same `verify`: at least as many tests as the fixture holds, all
    passing.

Maven runs in Docker (maven:3.9-eclipse-temurin-17; override with
R7_MAVEN_IMAGE), which also sandboxes model-written code. The original build's
dependency closure (cases/r7_shogun_hibernate6/setup.sh) is mounted read-only
as Maven's tail repository, so the three libraries that only terrestris's
Nexus serves resolve offline; anything new is cached in a scorer volume.
Without Docker or that cache, the affected checks FAIL as unverified.

Usage:
    python -m scorers.r7_scorer --output-file <model-output.txt>
    python -m scorers.r7_scorer --baseline [<reference project dir>]
    python -m scorers.r7_scorer --tree-from-record <record.json> <dest dir>
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from cases import sources

from .base import ScoreResult, apply_output, cache_dir, cli, parse_edits, parse_files, record_tests
from .base import run_command as _run

CASE_ID = "r7_shogun_hibernate6"
CASE_DIR = Path(__file__).resolve().parent.parent / "cases" / CASE_ID
PROJECT = CASE_DIR / "project"
MODULE = "shogun-core-main"
HIDDEN_TESTS = Path(__file__).resolve().parent / "fixtures" / "r7_hidden_tests"
MAVEN_IMAGE = os.environ.get("R7_MAVEN_IMAGE", "maven:3.9-eclipse-temurin-17")
M2_SEED = cache_dir() / CASE_ID / "m2"           # cases/r7_shogun_hibernate6/setup.sh
M2_VOLUME = "gate1_r7_scorer_m2"                  # what the migrated builds add (Central)
REFERENCE = cache_dir() / CASE_ID / "reference"   # the reference migration (baseline)
MIN_OWN_TESTS = 776                               # the original suite: 56 classes, all passing
BUILD_TIMEOUT_S = 2400
REQUIRED = ["edits_applied", "jakarta", "junit5", "build", "own_tests",
            "hibernate6", "spring6", "java17", "grading_tests"]

# Jakarta EE APIs that moved javax.* -> jakarta.* (javax.xml, javax.naming,
# javax.imageio, javax.sql did not move and are fine).
_JAVAX_EE_RE = re.compile(
    r"\bjavax\.(persistence|validation|servlet|mail|transaction|ws\.rs|inject|activation"
    r"|annotation\.(PostConstruct|PreDestroy|Generated|Resource|Priority|ManagedBean|security))\b")
# JUnit 4 is everything under org.junit except JUnit 5's jupiter and platform packages
_JUNIT4_RE = re.compile(r"\borg\.junit\.(?!jupiter\b|platform\b)[A-Za-z]|\borg\.powermock\b")
_DISABLED_RE = re.compile(
    r"@(Disabled|Ignore|DisabledIf\w*|DisabledOn\w*|EnabledIf\w*|EnabledOn\w*)\b"
    r"|\bAssumptions\s*\.|\bAssume\s*\.|\bassume(True|False|That)\s*\(")
_COMMENT_LINE_RE = re.compile(r"^\s*(//|/\*|\*)")
_POM_BANNED_RE = re.compile(
    r"<artifactId>\s*(junit|junit-vintage-engine|powermock-[\w-]+)\s*</artifactId>")
# anywhere in a pom: properties that skip tests or ignore their failures
_POM_SKIP_RE = re.compile(
    r"<(skipTests|maven\.test\.skip|maven\.test\.failure\.ignore|skipITs)>\s*true\s*<")
# inside the surefire/failsafe configuration: anything that leaves tests out
_RUNNER_PLUGIN_RE = re.compile(
    r"<plugin>(?:(?!</plugin>).)*?<artifactId>\s*maven-(surefire|failsafe)-plugin\s*</artifactId>"
    r"(?:(?!</plugin>).)*</plugin>", re.DOTALL)
_RUNNER_SKIP_RE = re.compile(
    r"<(skip|skipTests|skipExec|testFailureIgnore)>\s*true\s*<"
    r"|<(excludes|exclude|excludesFile|groups|excludedGroups|test|includes|include)>")
_SUMMARY_RE = re.compile(r"^\[(?:INFO|WARNING|ERROR)\] Tests run: (\d+), Failures: (\d+), Errors: (\d+), "
                         r"Skipped: (\d+)\s*$", re.MULTILINE)
_DEP_RE = re.compile(r"^\s*([\w.-]+):([\w.-]+):(?:jar|pom|test-jar):(?:[\w.-]+:)?([\w.+-]+):(\w+)", re.MULTILINE)


class _Done(Exception):
    """Stop scoring early; the checks set so far stand."""


def cache_problem() -> str | None:
    if not (M2_SEED / "org" / "geotools" / "gt-main" / "22.2").is_dir():
        return f"r7 needs its Maven cache ({M2_SEED}): run cases/r7_shogun_hibernate6/setup.sh"
    return None


def _mvn(project: Path, *args: str) -> list[str]:
    return ["docker", "run", "--rm", "-v", f"{project}:/w", "-v", f"{M2_VOLUME}:/root/.m2",
            "-v", f"{M2_SEED}:/seed:ro", "-w", "/w", MAVEN_IMAGE,
            "mvn", "-B", "-ntp", "-Dmaven.repo.local.tail=/seed", *args]


def _reclaim(project: Path) -> None:
    """Give files the root-run Maven containers wrote back to us, so cleanup works."""
    _run(["docker", "run", "--rm", "-v", f"{project}:/w", MAVEN_IMAGE,
          "chown", "-R", f"{os.getuid()}:{os.getgid()}", "/w"], timeout=300)


def last_summary(mvn_output: str) -> tuple[int, int, int, int] | None:
    """(run, failures, errors, skipped) of the last surefire "Results:" summary."""
    sums = _SUMMARY_RE.findall(mvn_output)
    return tuple(int(x) for x in sums[-1]) if sums else None  # type: ignore[return-value]


def _source_lines(root: Path):
    for f in sorted(root.rglob("*.java")) if root.is_dir() else []:
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not _COMMENT_LINE_RE.match(line):
                yield f, i, line


def javax_hits(project: Path) -> list[str]:
    base = project / MODULE / "src"
    return [f"{f.relative_to(project)}:{i}: {line.strip()}"
            for part in ("main", "test") for f, i, line in _source_lines(base / part)
            if _JAVAX_EE_RE.search(line)]


def junit4_hits(project: Path) -> list[str]:
    """JUnit 4 / PowerMock in the agent's tests, disabled or assumed-away tests,
    and poms that declare JUnit 4, the vintage engine or PowerMock, or skip or
    exclude tests."""
    hits = [f"{f.relative_to(project)}:{i}: {line.strip()}"
            for f, i, line in _source_lines(project / MODULE / "src" / "test")
            if _JUNIT4_RE.search(line) or _DISABLED_RE.search(line)]
    for pom in (project / "pom.xml", project / MODULE / "pom.xml"):
        text = pom.read_text(encoding="utf-8") if pom.is_file() else ""
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        # excluding JUnit 4 from another library is the fix, not a use: blank
        # <exclusions> out (same length, so line numbers stay right)
        text = re.sub(r"<exclusions>.*?</exclusions>", lambda m: re.sub(r"[^\n]", " ", m.group(0)),
                      text, flags=re.DOTALL)
        found = [(m.start(), m.group(0)) for m in _POM_BANNED_RE.finditer(text)]
        found += [(m.start(), m.group(0)) for m in _POM_SKIP_RE.finditer(text)]
        for plugin in _RUNNER_PLUGIN_RE.finditer(text):
            found += [(plugin.start() + m.start(), m.group(0))
                      for m in _RUNNER_SKIP_RE.finditer(plugin.group(0))]
        for pos, snippet in sorted(found):
            line = text.count("\n", 0, pos) + 1
            hits.append(f"{pom.relative_to(project)}:{line}: {snippet.strip()}")
    return hits


def resolved_versions(deps_txt: str) -> dict[str, str]:
    """{groupId:artifactId: version} from `mvn dependency:list` output."""
    return {f"{g}:{a}": v for g, a, v, _scope in _DEP_RE.findall(deps_txt)}


def major(version: str | None) -> int:
    m = re.match(r"(\d+)", version or "")
    return int(m.group(1)) if m else 0


def class_major(project: Path) -> int | None:
    """Class-file major version of the module's compiled classes (61 = Java 17)."""
    classes = project / MODULE / "target" / "classes"
    for f in sorted(classes.rglob("*.class")) if classes.is_dir() else []:
        data = f.read_bytes()[:8]
        if data[:4] == b"\xca\xfe\xba\xbe":
            return int.from_bytes(data[6:8], "big")
    return None


def fixture_min_tests() -> int:
    """The grading suite's test count (recorded when the fixture was made)."""
    meta = HIDDEN_TESTS / "SUITE.json"
    return int(json.loads(meta.read_text())["tests"]) if meta.is_file() else MIN_OWN_TESTS


def _verify(tmp: Path, res: ScoreResult, label: str) -> tuple[int, str, tuple[int, int, int, int] | None]:
    rc, out = _run(_mvn(tmp, "-pl", MODULE, "-am", "verify"), timeout=BUILD_TIMEOUT_S)
    summary = last_summary(out)
    res.details[f"{label}_errors"] = [ln for ln in out.splitlines() if ln.startswith("[ERROR]")][:30]
    res.details[f"{label}_tail"] = out[-1500:]
    res.details[f"{label}_summary"] = summary
    return rc, out, summary


def _passes(rc: int, summary, minimum: int) -> bool:
    return rc == 0 and summary is not None and summary[0] >= minimum and summary[1:] == (0, 0, 0)


def score(output_text: str, *, model_slug: str = "", workdir: Path | None = None,
          base: Path | None = None) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)
    if not parse_files(output_text) and not parse_edits(output_text):
        res.reason = "no `### FILE:` or `### EDIT:` blocks found in model output"
        return res
    for k in REQUIRED:
        res.checks[k] = False
    tmp = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="r7_"))
    tmp.mkdir(parents=True, exist_ok=True)
    docker = shutil.which("docker") is not None
    try:
        sources.ensure(CASE_ID)                 # fetched from the fork, see cases/sources.py
        shutil.copytree(base or PROJECT, tmp, dirs_exist_ok=True)
        applied = apply_output(output_text, tmp, strip_prefix="project/")
        res.details.update(files_written=applied.written, files_deleted=applied.deleted,
                           files_edited=sorted(set(applied.edited)),
                           edit_failures=applied.edit_failures[:25])

        # --- static ----------------------------------------------------------- #
        res.checks["edits_applied"] = not applied.edit_failures
        hits = javax_hits(tmp)
        res.checks["jakarta"] = not hits
        res.details["javax_hits"] = hits[:25]
        j4 = junit4_hits(tmp)
        res.checks["junit5"] = not j4
        res.details["junit4_hits"] = j4[:25]

        problem = None if docker else "docker unavailable"
        problem = problem or cache_problem()
        if problem:
            res.details["maven"] = f"{problem}: build and tests UNVERIFIED (fail)"
            record_tests(res, "own", total=MIN_OWN_TESTS, ran=False)
            record_tests(res, "grading", total=fixture_min_tests(), ran=False)
        else:
            # --- build + the agent's own tests -------------------------------- #
            rc, _out, own = _verify(tmp, res, "own")
            if own:
                record_tests(res, "own", passed=own[0] - own[1] - own[2] - own[3], total=own[0])
            else:
                record_tests(res, "own", total=MIN_OWN_TESTS, ran=False)
            res.checks["own_tests"] = _passes(rc, own, MIN_OWN_TESTS) and not j4
            if rc == 0:
                res.checks["build"] = True
            else:   # did the main code build, with the tests the only problem?
                brc, _ = _run(_mvn(tmp, "-pl", MODULE, "-am", "-DskipTests", "verify"),
                              timeout=BUILD_TIMEOUT_S)
                res.checks["build"] = brc == 0

            # --- versions actually used ---------------------------------------- #
            drc, deps = _run(_mvn(tmp, "-q", "-pl", MODULE, "dependency:list",
                                  "-DoutputFile=/w/deps.txt", "-DappendOutput=false"), timeout=900)
            deps_txt = (tmp / "deps.txt").read_text() if (tmp / "deps.txt").is_file() else ""
            vers = resolved_versions(deps_txt)
            picked = {k: vers.get(k) for k in ("org.hibernate.orm:hibernate-core",
                                                "org.hibernate:hibernate-core",
                                                "org.springframework:spring-core",
                                                "org.springframework.security:spring-security-core")}
            res.details["versions"] = picked
            res.details["bytecode_major"] = cmaj = class_major(tmp)
            res.checks["hibernate6"] = major(picked["org.hibernate.orm:hibernate-core"]) >= 6
            res.checks["spring6"] = (major(picked["org.springframework:spring-core"]) >= 6
                                     and major(picked["org.springframework.security:spring-security-core"]) >= 6)
            res.checks["java17"] = (cmaj or 0) >= 61

            # --- our grading tests --------------------------------------------- #
            if not (HIDDEN_TESTS / "java").is_dir():
                res.details["grading"] = f"grading tests missing ({HIDDEN_TESTS}): UNVERIFIED (fail)"
                record_tests(res, "grading", total=fixture_min_tests(), ran=False)
                raise _Done
            test_dir = tmp / MODULE / "src" / "test"
            shutil.rmtree(test_dir, ignore_errors=True)
            shutil.copytree(HIDDEN_TESTS, test_dir, copy_function=shutil.copy,
                            ignore=shutil.ignore_patterns("SUITE.json"))
            rc, _out, grading = _verify(tmp, res, "grading")
            want = fixture_min_tests()
            if grading:
                record_tests(res, "grading", passed=grading[0] - grading[1] - grading[2] - grading[3],
                             total=grading[0])
            else:
                record_tests(res, "grading", total=want, ran=False)
            res.checks["grading_tests"] = _passes(rc, grading, want)
    except _Done:
        pass
    finally:
        if docker:
            _reclaim(tmp)
        if not workdir:
            shutil.rmtree(tmp, ignore_errors=True)

    res.passed = all(res.checks.get(k, False) for k in REQUIRED)
    res.score = sum(bool(res.checks.get(k)) for k in REQUIRED) / len(REQUIRED)
    if res.passed:
        v = res.details.get("versions", {})
        res.reason = (f"migrated to Hibernate {v.get('org.hibernate.orm:hibernate-core')} and JUnit 5: "
                      f"build, {MIN_OWN_TESTS}+ own tests and {fixture_min_tests()}+ grading tests pass")
    else:
        res.reason = "failed checks: " + ", ".join(k for k in REQUIRED if not res.checks.get(k))
        if "maven" in res.details or "grading" in res.details:
            res.reason += " (unverified: missing docker, the r7 Maven cache or the grading tests)"
    return res


def answer_from_tree(reference: Path) -> str:
    """FILE blocks for every deliverable the reference changed or added, DELETE
    for the ones it removed (the same answer an agentic run would harvest)."""
    import agentic
    spec = agentic.CASES[CASE_ID]
    return agentic.answer_from(agentic.snapshot(PROJECT, spec), agentic.snapshot(reference, spec),
                               spec.deliverables)


def tree_from_answer(output_text: str, dest: Path) -> Path:
    """The project an answer produces (the pristine project plus its blocks):
    how the reference migration is rebuilt from an agentic run's record."""
    sources.ensure(CASE_ID)
    shutil.copytree(PROJECT, dest, dirs_exist_ok=True)
    applied = apply_output(output_text, dest, strip_prefix="project/")
    if applied.edit_failures:
        raise ValueError(f"{len(applied.edit_failures)} edit(s) did not apply: {applied.edit_failures[:3]}")
    return dest


def baseline(reference: Path | None = None) -> int:
    """Score the reference migration: it must pass every check (proves the task
    is solvable in this setup and the grading tests are right)."""
    ref = reference or REFERENCE
    if not (ref / MODULE).is_dir():
        print(f"no reference migration at {ref}", file=sys.stderr)
        return 1
    res = score(answer_from_tree(ref), model_slug="reference")
    print(json.dumps({"passed": res.passed, "reason": res.reason, "checks": res.checks,
                      **{k: res.details.get(k) for k in ("versions", "bytecode_major", "own_summary",
                                                          "grading_summary", "javax_hits", "junit4_hits",
                                                          "own_errors", "grading_errors")}},
                     indent=2, default=str))
    return 0 if res.passed else 1


if __name__ == "__main__":
    if "--tree-from-record" in sys.argv[1:]:
        # python -m scorers.r7_scorer --tree-from-record <record.json> <dest dir>
        i = sys.argv.index("--tree-from-record")
        rec, dest = Path(sys.argv[i + 1]), Path(sys.argv[i + 2])
        print(tree_from_answer(json.loads(rec.read_text())["output_text"], dest))
        raise SystemExit(0)
    if "--baseline" in sys.argv[1:]:
        rest = [a for a in sys.argv[1:] if a != "--baseline"]
        raise SystemExit(baseline(Path(rest[0]) if rest else None))
    raise SystemExit(cli(score))
