"""tests/r1_reference.py — build a known-good R1 migration from the frozen input.

Applies the mechanical Boot 2.7 -> 3.x rewrites to the real case files and
returns them in the model output format (`### FILE:` / `### DELETE:`). Used to
prove the R1 gate is passable; an unmigrated copy must still fail.
"""

from __future__ import annotations

import re

from scorers.r1_scorer import CASE_DIR

FACTORIES = "src/main/resources/META-INF/spring.factories"


def _migrate_java(src: str) -> str:
    for pkg in ("persistence", "validation", "annotation", "servlet"):
        src = src.replace(f"import javax.{pkg}.", f"import jakarta.{pkg}.")
    src = src.replace("import org.junit.Test;", "import org.junit.jupiter.api.Test;")
    src = src.replace("import org.junit.Before;", "import org.junit.jupiter.api.BeforeEach;")
    src = re.sub(r"@Before\b", "@BeforeEach", src)
    src = src.replace("static org.junit.Assert.", "static org.junit.jupiter.api.Assertions.")
    # JUnit 5 takes the failure message LAST
    src = re.sub(r'assertNotNull\(("[^"]*"),\s*([^;]+)\);', r"assertNotNull(\2, \1);", src)
    return src


def _migrate_pom(pom: str) -> str:
    pom = pom.replace("<version>2.7.18</version>", "<version>3.2.5</version>")
    pom = re.sub(r"(<(?:java\.version|maven\.compiler\.(?:source|target))>)11<", r"\g<1>17<", pom)
    pom = re.sub(
        r"\s*<dependency>\s*<groupId>junit</groupId>\s*<artifactId>junit</artifactId>.*?</dependency>",
        "", pom, flags=re.DOTALL,
    )
    return pom


def _fence(rel: str, body: str) -> str:
    return f"### FILE: {rel}\n```\n{body.rstrip()}\n```\n"


def reference_output(migrate: bool = True) -> str:
    """Model-format output for the whole module, migrated (or re-emitted as-is)."""
    parts: list[str] = []
    pom = (CASE_DIR / "pom.xml").read_text(encoding="utf-8")
    parts.append(_fence("pom.xml", _migrate_pom(pom) if migrate else pom))
    for f in sorted((CASE_DIR / "src").rglob("*.java")):
        body = f.read_text(encoding="utf-8")
        parts.append(_fence(str(f.relative_to(CASE_DIR)), _migrate_java(body) if migrate else body))
    if migrate:
        parts.append(f"### DELETE: {FACTORIES}\n")
    return "\n".join(parts)
