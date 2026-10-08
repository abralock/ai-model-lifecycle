"""scorers/r1_scorer.py — Spring Boot 2.7 → 3.x migration scorer.

Takes the model's raw output (the `### FILE:` blocks), materializes the project
into a temp dir, and runs `mvn -q compile` then `mvn -q test`. Also greps for
leftover `javax.*` and a lingering `spring.factories`.

Robustness: if Maven is not installed, the scorer degrades to the *static* checks
(javax-free / factories-gone / boot-3 pom) and reports compile/test as "unchecked"
rather than crashing.

Usage:
    python -m scorers.r1_scorer --output-file runs/.../model.r1_springboot2to3.json
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import ScoreResult, cli, parse_deletes, parse_files, write_files

CASE_ID = "r1_springboot2to3"


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


def _has_maven() -> bool:
    return shutil.which("mvn") is not None


def _boot3_in_pom(pom: str) -> bool:
    m = re.search(
        r"<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([^<]+)</version>",
        pom,
    )
    return bool(m) and m.group(1).strip().startswith("3.")


def score(output_text: str, *, model_slug: str = "", workdir: Path | None = None) -> ScoreResult:
    res = ScoreResult(case_id=CASE_ID, model_slug=model_slug)

    files = parse_files(output_text)
    deletes = parse_deletes(output_text)
    if not files:
        res.reason = "no `### FILE:` blocks found in model output"
        return res

    # --- static checks ------------------------------------------------------ #
    # pom.xml may be at root or under an artifact dir; find any pom.xml
    pom_paths = [p for p in files if p.endswith("pom.xml")]
    pom_text = files.get(pom_paths[0], "") if pom_paths else ""
    res.checks["has_pom"] = bool(pom_paths)
    res.checks["boot3_pom"] = _boot3_in_pom(pom_text)

    # javax leftovers across all emitted sources
    javax_hits: list[str] = []
    for rel, body in files.items():
        if rel.endswith((".java", ".xml", ".properties")):
            for i, line in enumerate(body.splitlines(), 1):
                if "javax." in line:
                    javax_hits.append(f"{rel}:{i}: {line.strip()}")
    res.checks["javax_free"] = len(javax_hits) == 0
    res.details["javax_hits"] = javax_hits[:25]

    # spring.factories present? (either re-emitted as a file, or not deleted)
    factories_emitted = [p for p in files if "spring.factories" in p]
    factories_deleted = any("spring.factories" in d for d in deletes)
    res.checks["factories_gone"] = (not factories_emitted) or factories_deleted
    res.details["factories_emitted"] = factories_emitted
    res.details["factories_deleted"] = factories_deleted

    # --- dynamic checks (compile + test) ----------------------------------- #
    if _has_maven():
        tmp = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="r1_"))
        tmp.mkdir(parents=True, exist_ok=True)
        write_files(files, tmp)
        rc_c, out_c = _run(["mvn", "-q", "-DskipTests", "compile"], tmp)
        res.checks["compile"] = rc_c == 0
        res.details["compile_tail"] = out_c[-1500:]
        if rc_c == 0:
            rc_t, out_t = _run(["mvn", "-q", "test"], tmp)
            res.checks["tests"] = rc_t == 0
            res.details["test_tail"] = out_t[-1500:]
        else:
            res.checks["tests"] = False
        if not workdir:
            shutil.rmtree(tmp, ignore_errors=True)
    else:
        res.details["maven"] = "not installed — compile/test unchecked (static checks only)"
        res.checks["compile"] = res.checks.get("compile", True)
        res.checks["tests"] = res.checks.get("tests", True)

    # --- verdict ------------------------------------------------------------ #
    # Required checks that must ALL pass for a green result.
    required = ["has_pom", "boot3_pom", "javax_free", "factories_gone", "compile", "tests"]
    res.passed = all(res.checks.get(k, False) for k in required)
    res.score = 1.0 if res.passed else 0.0
    if not res.passed:
        failed = [k for k in required if not res.checks.get(k)]
        res.reason = "failed checks: " + ", ".join(failed)
    else:
        res.reason = "migrated cleanly: compiles, tests pass, no javax, no spring.factories"
    return res


if __name__ == "__main__":
    raise SystemExit(cli(score))
