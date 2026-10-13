"""tests/test_r1b_reference_slow.py — the R1b scorer passes a known-good answer, end to end.

Proves a "no model passed R1b" result is the models' fault, not the harness's:
the reference answer (tests/r1b_reference_answer.txt) must clear the build, the
hidden 52 unit + 140 integration tests and the 54 Cypress e2e tests.

Slow (about 2-5 min with a warm Maven cache) and needs Docker plus the e2e cache
(cases/r1b_jhipster_boot3/setup_e2e.sh), so it is collected only on request:

    GATE1_SLOW_TESTS=1 pytest -q tests/test_r1b_reference_slow.py
"""

from __future__ import annotations

from pathlib import Path

from scorers import r1b_scorer


def test_r1b_reference_answer_passes_every_stage():
    answer = (Path(__file__).parent / "r1b_reference_answer.txt").read_text(encoding="utf-8")
    res = r1b_scorer.score(answer)
    assert res.passed, (res.reason, res.details.get("build_errors"), res.details.get("e2e"))
    assert res.details["tests_run"]["unit"] >= r1b_scorer.MIN_UNIT
    assert res.details["tests_run"]["integration"] >= r1b_scorer.MIN_IT
    assert res.details["e2e_tests"]["passing"] >= r1b_scorer.MIN_E2E
