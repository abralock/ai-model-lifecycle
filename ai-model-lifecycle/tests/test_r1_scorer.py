"""tests/test_r1_scorer.py — R1 scorer soundness.

* The model's files are applied as a patch over the frozen module.
* A missing Maven makes compile/test UNVERIFIED -> fail, never a free pass.
* Comments and JDK `javax.*` packages don't count as leftover javax usage.
* Build-backed: a reference migration passes and actually runs the tests; the
  unmigrated module fails. Auto-skips without mvn or docker.
"""

from __future__ import annotations

import shutil

import pytest

from scorers import r1_scorer
from tests.r1_reference import reference_output

requires_maven = pytest.mark.skipif(
    not (shutil.which("mvn") or shutil.which("docker")), reason="no mvn and no docker"
)


@pytest.fixture
def no_maven(monkeypatch):
    monkeypatch.setattr(r1_scorer, "_maven_argv", lambda project: None)


def test_missing_maven_is_unverified_not_pass(no_maven):
    r = r1_scorer.score(reference_output(), model_slug="t/m")
    # every static check holds on the reference migration...
    assert r.checks["boot3_pom"] and r.checks["javax_free"] and r.checks["factories_gone"]
    # ...but without a build the case cannot pass
    assert r.passed is False
    assert r.checks["compile"] is False
    assert "unverified" in r.reason


def test_partial_output_is_overlaid_on_input(no_maven):
    """Emitting only pom.xml leaves the input's javax sources in the build."""
    only_pom = (
        "### FILE: pom.xml\n```xml\n<parent><artifactId>spring-boot-starter-parent</artifactId>"
        "<version>3.2.5</version></parent>\n```\n"
    )
    r = r1_scorer.score(only_pom, model_slug="t/m")
    assert r.checks["boot3_pom"] is True
    assert r.checks["javax_free"] is False
    assert r.checks["factories_gone"] is False  # not deleted


def test_javax_check_ignores_comments_and_jdk_packages(no_maven):
    extra = (
        "### FILE: src/main/java/com/example/demo/Extra.java\n```java\n"
        "package com.example.demo;\n"
        "// was javax.servlet.Filter before the migration\n"
        "import javax.sql.DataSource;\n"
        "class Extra {}\n```\n"
    )
    r = r1_scorer.score(reference_output() + extra, model_slug="t/m")
    assert r.checks["javax_free"] is True, r.details["javax_hits"]


def test_fabricated_project_cannot_pass_without_build(no_maven):
    """A refusal/hallucination with no FILE blocks fails with a clear reason."""
    r = r1_scorer.score("I can't see the sources.\n### DELETE: x\n", model_slug="t/m")
    assert r.passed is False
    assert "no `### FILE:` blocks" in r.reason


@requires_maven
def test_reference_migration_passes_and_runs_tests():
    r = r1_scorer.score(reference_output(), model_slug="t/m")
    assert r.passed is True, f"{r.reason}\n{r.details.get('compile_tail') or r.details.get('test_tail')}"
    assert r.details["tests_run"]["ran"] >= r1_scorer.expected_test_count() > 0


@requires_maven
def test_fabricated_main_code_fails_hidden_tests():
    """Rewriting Customer with a different API passes its own (rewritten) tests
    but fails the input's hidden tests."""
    import re

    out = reference_output()
    out = re.sub(r"getFullName", "getName", out)   # renames the API everywhere, tests included
    r = r1_scorer.score(out, model_slug="t/m")
    assert r.checks["compile"] and r.checks["tests"], r.details.get("test_tail")
    assert r.checks["hidden_tests"] is False
    assert r.passed is False


@requires_maven
def test_unmigrated_module_fails():
    r = r1_scorer.score(reference_output(migrate=False), model_slug="t/m")
    assert r.passed is False
    assert not r.checks["boot3_pom"] and not r.checks["javax_free"]
