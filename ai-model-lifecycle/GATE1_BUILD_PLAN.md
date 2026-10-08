# AI Model Lifecycle Management — Gate 1 Build Plan

> Status: **DRAFT — for review**
> Author: Ash 🏗️ (architect)
> Date: 2026-10-08

---

## 1. Requirement (source of truth)

### Purpose
Ensure every AI model undergoes consistent and automated checks from introduction to decommissioning.

### Issues
Lack of consistent and automated checks for new models or gateway upgrades.

### Solution
Manage each model as a product, using the same set of standards and verification methods.

### Gates
- **Gate 1 — New Model Evaluation:** execute the same set of fixed tasks to determine whether the model is better, based on results.
- **Gate 2 — Capability Verification:** check that fixed test scenarios have all passed to determine if there are issues.

### Expectations
- **Speed:** shorten the time from new model release to go-live.
- **Quality:** reduce production events caused by introduction or upgrades (e.g. cache issues).
- **Risk:** controllable risks from new model release to developer availability, with predictable introduction results.

### Focus axes
**Time / Quality / Cost** — with a baseline listed for every scenario (external leaderboards may be referenced).

### Candidate model matrix
| Current | Target |
|---|---|
| Claude Opus 4.8 | Claude Opus 5.5 |
| Claude Sonnet 5 | Claude Sonnet 5.5 |
| Claude Sonnet 4.6 | Claude Sonnet 5.5 |
| Claude Haiku 4.5 | Claude Haiku 5.5 |
| GPT-5.6 Sol | GPT-6 Sol |
| GPT-5.6 Luna | GPT-6 Luna |
| GPT-5.6 Terra | GPT-6 Terra |

---

## 2. Objective

Build a **Personal AI Dev Box** that:
1. Runs the **same fixed coding tasks** against every candidate model.
2. Scores each model on **Time / Quality / Cost**.
3. Produces an **Antutu-style overall score** + go/no-go recommendation.

---

## 3. Deliverables (end state)

1. `golden_set.jsonl` — frozen prompts + input artifacts + expected outcomes (git-versioned).
2. `runner.py` — runs the full model matrix, logs usage/latency.
3. `scorers/` + `judge.py` — deterministic + free-text grading.
4. `report.py` — scorecard + `DECISION.md`.
5. Docker dev box + CI workflow to re-run on every model bump.

---

## 4. Phase-by-phase plan

### Phase 0 — Unblock prerequisites (Abraham, ~1 day)
Blocking inputs required before code:
- **Model access** — API keys / gateway URL exposing all 12 candidate models.
- **Test artifacts** — at least one real sample each:
  - Spring Boot 2.7 module
  - GWT view
  - 5–10 Oracle queries
  - ETL table schema (source + target)
- **Judge model** — which non-candidate model to use for free-text scoring (or deterministic-only).

### Phase 1 — Golden set freeze (Pikachu)
- Ingest real artifacts into `cases/`.
- Freeze 12–16 cases across 4 scenarios.
- Write expected outcomes + automatable pass criteria.
- Output: `golden_set.jsonl`.

### Phase 2 — Harness + model selection (Pikachu)
- `runner.py`: iterate case × model, `temperature=0`, fixed `max_tokens`, same system prompt, retry/backoff via `litellm`.
- `models.yaml`: the 12-model matrix.
- Capture: input/output tokens, cache read/write tokens, latency, retries, output.

### Phase 3 — Scorers + judge (Pikachu)
- Deterministic: Pytest (compile/tests), pandas (result-set diff/reconciliation), Playwright (E2E).
- `judge.py`: third-model LLM-as-judge for free-text, with rubric.

### Phase 4 — Scorecard + reporting (Pikachu)
- `report.py`: Time/Quality/Cost per scenario, normalized 0–100 vs baseline, weighted overall score, go/no-go flags.

### Phase 5 — E2E + eval CI (Charmander)
- Playwright/Cypress E2E for the migrated-Angular case.
- Cross-check scoring math (no double counts, correct normalization).
- GitHub Actions: re-run eval on every model bump, publish scorecard.
- Report **SHIP/BLOCK**.

### Phase 6 — Docker dev box + reproducibility (Squirtle)
- Containerize (`Dockerfile` + compose).
- Pin deps, identical env on any machine.
- Secure model keys (env, never committed).

### Phase 7 — First live run + baseline lock (Ash + Abraham)
- Run all 7 current→target pairs on the frozen set.
- Lock incumbent's score as baseline.
- Produce first `DECISION.md` for Opus 4.8→5.5.

---

## 5. Team assignment (by role)

| Role | Owner | Scope |
|---|---|---|
| Architect | **Ash** 🏗️ | Design, review, gate decisions, final verification |
| Developer | **Pikachu** ⚡ | Harness, scorers, judge, report (Phases 1–4) |
| Tester | **Charmander** 🔥 | E2E + eval CI + scoring validation (Phase 5) |
| DevOps | **Squirtle** 🐢 | Docker box + secrets + reproducibility (Phase 6) |

### Effort estimate
- Pikachu: ~3–4 days
- Charmander: ~1–2 days
- Squirtle: ~1 day
- **Total to first live run:** ~1 week (assuming Phase 0 inputs arrive fast).

---

## 6. Key design decisions (flag if you disagree)

1. **`litellm`** as the single abstraction — no per-provider code.
2. **`temperature=0`, fixed `max_tokens`** — measures model difference, not noise.
3. **Baseline = incumbent's actual score on the golden set**, not a leaderboard number.
4. **C-class (cache/long-context) cases pulled into Gate 1** — catch "cache issues" early, not at Gate 2.
5. **Judge uses a third, non-candidate model.**

---

## 7. Gate 1 test cases (summary)

> Full case table lives in `TEST_CASES.md` (next to this file). Scored on Time/Quality/Cost, normalized against baseline.
> **CONFIRMED decisions:** C1–C3 kept in Gate 1 · R3→R4→R5 modeled as a **chained pipeline** (model carries its own outputs forward).

| Scenario | Cases |
|---|---|
| Refactor + Data (chained) | R1 Spring Boot 2→3, R2 GWT→Angular, R3 Oracle SP→PostgreSQL, R4 Schema+Bulk-Load+Optimize, R5 ETL→Dashboard |
| Code Comprehension / Bug Fix | C1 Cache-invalidation, C2 Long-context retrieval, C3 Multi-file edit |
| Instruction / Tool Use | T1 Structured output, T2 Tool-call/async, T3 Refusal boundary |

**Dependency chain:** R3 → R4 → R5 (each downstream task consumes the model's *own* upstream output, not golden fixtures).

**Exit criteria addendum:** (3) Continuity chain R3→R4→R5 completes — no downstream break.

**Scoring:**
```
Scenario score = Wq·Quality + Wc·Cost + Wt·Time   (normalized 0–100 vs baseline)
Overall score  = Σ (scenario score × scenario weight)
```
Default weights: **Quality 0.5 / Cost 0.3 / Time 0.2**.

**Gate 1 exit criteria:**
1. Overall score ≥ incumbent, or equal score at lower cost/latency.
2. Regression subset (R1, R3, C1, C2, T2) pass rate = **100%**.

---

## 8. Personal AI Dev Box — toolchain

### Harness
| Component | Role |
|---|---|
| Python 3.12 + `uv` | harness language + dependency management |
| `litellm` | unified multi-model abstraction |
| Pydantic + `instructor` | typed, schema-valid outputs |
| `httpx` + retry/backoff | raw calls + rate-limit handling |
| `runner.py` | iterate case × model |

### Model selection (`models.yaml`)
```yaml
candidates:
  - claude-opus-4.8    -> claude-opus-5.5
  - claude-sonnet-4.6  -> claude-sonnet-5.5
  - claude-sonnet-5    -> claude-sonnet-5.5
  - claude-haiku-4.5   -> claude-haiku-5.5
  - gpt-5.6-sol        -> gpt-6-sol
  - gpt-5.6-luna       -> gpt-6-luna
  - gpt-5.6-terra      -> gpt-6-terra
```

### Tools (three-axis instrumentation)
| Axis | Tools |
|---|---|
| Quality | Pytest + `pytest-json-report`, pandas, Playwright, `judge.py` (LLM-as-judge), DeepEval/Giskard (optional) |
| Cost | provider usage fields, `tiktoken`, `costs.py` (cost per successful task) |
| Time | OpenTelemetry / Logfire / langfuse, `report.py` |
| Reproducibility & CI | Docker, git-versioned `golden_set.jsonl`, GitHub Actions, DuckDB (optional) |

### Repo layout
```
ai-dev-box/
├── cases/{refactor,newdev,comprehension,tooluse}/
├── models.yaml
├── runner.py
├── judge.py
├── scorers/
├── costs.py
├── report.py
└── .github/workflows/eval.yml
```

---

## 9. Open questions for review

1. Scope of Gate 1 — keep the C-class comprehension suite here, or defer to Gate 2?
2. Weighting — keep Quality 0.5 / Cost 0.3 / Time 0.2, or team-specific values?
3. Phase 0 inputs — when can model access + test artifacts + judge model be provided?
