# Gate 1 Test Cases — AI Model Lifecycle Management

> Status: **CONFIRMED** (Abraham approved decisions on 2026-10-08)
> Decisions locked: C1–C3 kept in Gate 1 · R3→R4→R5 modeled as a **chained pipeline**

---

## Design principle

Same fixed tasks, every model, scored on **Time / Quality / Cost** against a **baseline**.
Two structural features distinguish this set:

1. **Dependency chain** — R3 → R4 → R5 are not independent; each downstream task consumes
   the *model's own* upstream output (not golden fixtures). This measures a model's ability
   to carry state across a workflow — the realistic developer scenario — and directly serves
   the "reduce production events" goal (a model that breaks its own schema downstream causes incidents).

2. **Two case families** — "Refactor + Data" (R1–R5) and "Comprehension + Tool-use" (C1–C3, T1–T3).

---

## Refactor + Data suite (R1–R5)

| ID | Case (fixed task) | Input artifact | Quality check (automatable) | Baseline (reference) |
|---|---|---|---|---|
| **R1 · Spring Boot 2→3** | Upgrade project from Spring Boot 2.7 → 3.x, complete javax→jakarta migration | Real Boot 2.7 Maven module (~30 classes) | `mvn compile` ✅ + all JUnit green ✅ + no `javax.*` ✅ + no `spring.factories` ✅ | build✅ / tests✅ / API-breaks=0; SWE-bench Lite |
| **R2 · GWT→Angular** | Migrate GWT view to Angular components, keep functional parity | GWT module (2–3 views) + spec | `ng build` ✅ + Playwright E2E ✅ + parity checklist 100% | build✅ / E2E✅ / parity=100% |
| **R3 · Oracle Stored Proc → PostgreSQL** | Convert Oracle PL/SQL stored procedure to PostgreSQL (plpgsql), result must match | Real Oracle SP (cursors, `%ROWTYPE`, `SEQUENCE`, exceptions, `DUAL`) | Compiles on Postgres ✅ + SP output = golden output ✅ + no Oracle-only syntax | result-parity=100% / dialect-tokens=0 |
| **R4 · Schema + Bulk Load + Optimize** | Create tables, bulk-insert N million records, add correct indexes so SELECT is optimized | Table schemas + seed data (or R3 output schema) | DDL valid ✅ + N rows loaded ✅ + `EXPLAIN` shows index scan (no seq scan) ✅ + latency < threshold | index-hit / no-seq-scan / latency<X ms |
| **R5 · ETL into Dashboard** | Build ETL from R4 tables → aggregate → dashboard-ready dataset with reconciliation | R4 table outputs + dashboard schema | ETL end-to-end ✅ + row-count reconciliation = 0 ✅ + idempotent ✅ + dashboard dataset loads ✅ | runs✅ / mismatch=0 / idempotent✅ |

### Dependency continuity chain

| Chain | What it measures |
|---|---|
| R3 → R4 | Reuses schema/DDL from a prior task correctly |
| R4 → R5 | Builds downstream on tables *it* created (not clean fixtures) |

Continuity counts as a **bonus** — awarded only when downstream tasks succeed on the model's
*own* upstream outputs.

---

## Comprehension suite (C1–C3) — anti-incident gate

> Kept in **Gate 1** per decision. Targets "cache issues" and long-context reliability.

| ID | Case (fixed task) | Quality check | Purpose |
|---|---|---|---|
| **C1 · Cache-invalidation defect** | Given a service with a stale-cache bug, locate root cause + add regression test | root cause correct ✅ + regression test passes ✅ | Directly targets "cache issues" |
| **C2 · Long-context retrieval** | 100–200k token repo slice, find planted fact | cites correct file:line, zero hallucination | long-context reliability |
| **C3 · Multi-file edit** | Feature touching 4+ files | diff applies clean ✅ + tests green ✅ + no unrelated changes | change controllability |

---

## Tool-use suite (T1–T3)

| ID | Case | Quality check |
|---|---|---|
| **T1 · Structured output** | schema-valid N/N runs |
| **T2 · Tool-call / async** | behavior matches spec, no race |
| **T3 · Refusal boundary** | refuses unsafe, doesn't over-refuse benign |

---

## Scoring model

```
Scenario score = Wq·Quality + Wc·Cost + Wt·Time   (normalized 0–100 vs baseline)
Overall score  = Σ (scenario score × scenario weight)
```

Weights: **Quality 0.5 / Cost 0.3 / Time 0.2**.

### Gate 1 exit criteria

1. Overall score ≥ incumbent model's score, **or** equal score at lower cost/latency.
2. Regression subset (R1, R3, C1, C2) pass rate = **100%** — the "must not regress" floor.
3. Continuity chain R3→R4→R5 completes (no downstream break).

---

## Candidate model matrix

| Current | Target |
|---|---|
| Claude Opus 4.8 | Claude Opus 5.5 |
| Claude Sonnet 5 | Claude Sonnet 5.5 |
| Claude Sonnet 4.6 | Claude Sonnet 5.5 |
| Claude Haiku 4.5 | Claude Haiku 5.5 |
| GPT-5.6 Sol | GPT-6 Sol |
| GPT-5.6 Luna | GPT-6 Luna |
| GPT-5.6 Terra | GPT-6 Terra |
