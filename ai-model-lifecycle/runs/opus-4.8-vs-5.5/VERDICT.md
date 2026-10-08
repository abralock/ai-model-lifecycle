# VERDICT — R4 / R5 audit (opus-4.8-vs-5.5)

> Author: Charmander 🔥 (Gate 1 tester) · Date: 2026-10-08
> Scope: audit the R4 & R5 test artifacts/scorers, fix what is **unfair**, then
> re-score the **existing** model outputs (no live model calls, `runs/*.json`
> untouched).
> Reproduce: `.venv/bin/python -m audits.rescore_r4_r5` and
> `.venv/bin/python -m audits.prove_r5_passable`.

---

## TL;DR

| Case | Opus 4.8 | Opus 5.5 | Was it a model defect? |
|---|---|---|---|
| **R4** | **PASS** | **PASS** | No — 5.5's FAIL was a **test artifact** (VACUUM in a transaction). |
| **R5** | **FAIL** | **FAIL** | Yes — both models genuinely mis-designed the reconciliation. |

The headline "Opus 5.5 has a real R4 defect" is **false**. The R5 failure is a
**real, shared model behavior** (both models used a line-grain rollup for an
order-level reconciliation) — but the *original spec wording* was also unfair
(it demanded a formula that was impossible with multi-category orders), so the
spec was clarified to make the rule passable without weakening the gate.

---

## 1. What was unfair, and how it was fixed

### R4 — `VACUUM cannot run inside a transaction block` (test artifact)

**Diagnosis (case b, the scorer was too strict).** Opus 5.5's `solution.sql` is a
correct answer: four tables, ~100k orders + ~300k items, and
`CREATE INDEX idx_orders_status_date_incl_id ON orders(status, order_date)
INCLUDE (order_id)`. It *additionally* ends with four maintenance statements
(`VACUUM ANALYZE customers/products/orders/order_items`) to refresh planner
stats. The model even documented the constraint: *"Run this with plain psql, not
`psql -1` … VACUUM cannot run inside a transaction block."*

The scorer applied the whole script via `cur.execute(sql_text)` on a psycopg2
connection, which runs every statement inside an **implicit transaction**. So a
perfectly good solution died on `VACUUM` before any check could run — the
`loaded` / `index_scan` / `no_seq_scan` / `latency` checks were all reported
`False` as collateral. That is exactly the artifact described in the task's
option (b): a legitimate output that would succeed under psql autocommit still
failed because of *how the harness runs the SQL*.

**Fix.** `scorers/r4_scorer.py` now strips transaction-illegal maintenance
statements before applying the model's SQL (`strip_maintenance()`): `VACUUM` /
`VACUUM ANALYZE` / `VACUUM FULL` lines are removed and replaced with a
transaction-legal `ANALYZE <tables>;` so the planner still gets fresh statistics.
A plain `ANALYZE` (already legal) is left untouched. A new
`maintenance_statements_stripped` check records whether stripping occurred. This
keeps R4 measuring what R4 is *supposed* to measure (schema + bulk load + correct
index), and does **not** relax any of the pass criteria.

*Verification:* with the fix, Opus 5.5's R4 output passes on the merits —
`index_scan=True`, `no_seq_scan_orders=True`, ~120 ms < 1000 ms. Opus 4.8 still
passes (~107 ms); no regression.

### R5 — reconciliation formula was mathematically impossible as written

**Diagnosis (the spec was unfair *and* the models genuinely failed).** The source
is order-grain but `dash_revenue_by_category` is `month × category`. A single
order frequently contains line items in **more than one product category**, so
`SUM(order_count)` (per `month × category`) counts that order once per category
and **overshoots** `COUNT(*)` of COMPLETED orders.

Confirmed empirically on the real datasets (Opus 5.5's own R4 data):

- COMPLETED orders: **49,502**
- orders bucketed by #distinct categories: `1→11,005 · 2→12,302 · 3→13,271 · 4→9,916 · 5→3,008`
- `SUM(order_count)` over `month × category`: **130,126**
- therefore `mismatch = 49,502 − 130,126 = −80,624` (Opus 4.8's data: `−73,000`).

Orphan COMPLETED orders (no items / unknown product): **0**. So the failure is
100% multi-category double-counting, not data gaps. Under the spec's formula
`mismatch == 0` was **unachievable** for any ETL that aggregates the line-level
rollup — the requirement was impossible as written. That is unfair.

**Fix — make it precise and passable *without* dumbing it down.** `etl_spec.md`
§2/§4/§5 were rewritten to state the missing business rule: **an order has a
single reporting category** — its *controlling category* = the category of the
line with the smallest `order_item_id` (the order's first line). The ETL must
assign each COMPLETED order to exactly one `(month, category)` row, counting
DISTINCT orders and attributing that order's controlling line revenue/units once.
Then exactly one order ↔ one row, so `SUM(order_count)` = COMPLETED order count
and `mismatch = 0` is reachable. `mismatch` is a **signed** difference; the
`CHECK (mismatch >= 0)` on `etl_run_log` was removed so a naive rollup can record
its (negative) mismatch honestly instead of being unable to log it. The success
signal is unchanged and still enforced:

```
source_order_count = COUNT(*) FROM orders WHERE status = 'COMPLETED'
loaded_order_count = SUM(order_count) FROM dash_revenue_by_category
mismatch           = source_order_count - loaded_order_count   -- MUST be 0
```

The R5 scorer also gained one guard (`reconciliation_zero` now requires
`src == loaded AND loaded > 0`) so an empty rollup can't fake the gate. All other
pass criteria (dataset non-empty, model's own log row `mismatch == 0`,
idempotency) are unchanged.

**Proof the fixed gate is passable and still discriminating.**
`audits/prove_r5_passable.py` scores a minimal **correct** order-grain ETL against
each model's real dataset:

```
4.8: correct-ETL passed=True  src=50000 loaded=50000 mismatch=0  (160×2 dashboard rows)
5.5: correct-ETL passed=True  src=49502 loaded=49502 mismatch=0  (160×2 dashboard rows)
```

and the models' **actual** line-grain ETLs still **FAIL** it. The gate is fair
now, and still catches the real mistake.

**Files changed**

| File | Change | Why |
|---|---|---|
| `scorers/r4_scorer.py` | `strip_maintenance()` + call + `maintenance_statements_stripped` check; docstring note | VACUUM is maintenance, illegal in the harness txn; not part of the R4 answer |
| `scorers/r5_scorer.py` | `reconciliation_zero` requires `loaded > 0` | don't let an empty rollup fake `mismatch = 0` |
| `cases/r5_etl_dashboard/etl_spec.md` | §2 business rule (single/controlling category), §4 transform rewritten, §5 rewritten with the precise passable formula | original rule was mathematically impossible on multi-category orders |
| `cases/r5_etl_dashboard/prompt.md` | reconciliation requirement now flags multi-category de-dup | keep the task self-consistent with the spec |
| `cases/r5_etl_dashboard/dashboard_schema.sql` | dropped `CHECK (mismatch >= 0)`; comment | mismatch is signed; the gate is the ETL, not a column constraint |
| `cases/r5_etl_dashboard/README.md` | pass-criteria table updated | document the actual checks |
| `audits/rescore_r4_r5.py`, `audits/prove_r5_passable.py` (new) | re-score + passability proof | reproducibility, no live calls |
| `tests/test_r4_r5_fixes.py` (new) | 7 regression tests | lock in the fix + the R5 passability invariant |

---

## 2. Re-scored results (existing outputs, no re-run)

|| R4 | R5 |
|---|---|---|
| **Opus 4.8** | **PASS** — index scan on `orders`, no seq scan, 106.7 ms < 1000 ms | **FAIL** — `RaiseException: ETL reconciliation failed: mismatch = -73000` |
| **Opus 5.5** | **PASS** — index scan on `orders`, no seq scan, 121.1 ms < 1000 ms | **FAIL** — `RaiseException: … source_order_count=49502, loaded_order_count=130126, mismatch=-80624 … −80624 double-counts from 38497 multi-category orders` |

**Why each fails R5.** Both models sum `COUNT(DISTINCT order_id)` over the
line-level `month × category` rollup as `loaded_order_count`. For multi-category
orders this double-counts, so `mismatch < 0` (4.8: −73,000; 5.5: −80,624). The
models' own hard gates then abort the run and roll back, leaving no
`etl_run_log` row and no dashboard rows — so all four checks fail.

---

## 3. Honest judgment

- **"Opus 5.5 has a real R4 defect" is FALSE.** Its R4 answer is correct
  (composite covering index, index-only/bitmap scan, ~120 ms). The original FAIL
  was entirely the `VACUUM`-in-transaction artifact of the harness. After the
  fix, **R4 is PASS for both models** — and R4's pass criteria were *not* weakened;
  only the maintenance statement was removed from what gets applied.
- **R5 is now a fair test.** The original §5 asked for a zero mismatch that no
  line-grain aggregation could ever produce (mathematically impossible given
  multi-category orders). The rewritten rule is precise, achievable, and keeps
  `mismatch == 0` as the hard success signal. A correct order-grain ETL
  (controlling category per order) reconciles to exactly 0 on both real datasets,
  while the models' actual line-grain ETLs still fail — i.e. the failure is a
  **genuine model behavior**, correctly attributed now that the test is fair.
- **Both models genuinely mis-designed R5.** The correct approach each *should*
  have taken: *assign each COMPLETED order a single controlling category (first
  line item) before aggregating, so the rollup shares the order grain and
  `SUM(order_count)` equals the COMPLETED order count.* Notably, Opus 5.5's own
  header comment even **diagnosed this exact issue** ("These two numbers are only
  equal if every COMPLETED order has line items in exactly ONE category") — then
  declined to resolve it and raised instead. Opus 4.8 assumed the opposite
  (multi-category orders don't exist / orphans are the only risk) and guarded the
  wrong case. Both are real design errors against a now-fair spec.

## 4. Verification

- `.venv/bin/python -m pytest -q` → **36 passed** (29 pre-existing + 7 new).
- `audits/rescore_r4_r5.py` reproduces the table above from the frozen
  `runs/opus-4.8-vs-5.5/*.json`.
- `audits/prove_r5_passable.py` proves the fixed R5 gate passes a correct ETL on
  both models' datasets.
- No live model calls; `runs/*.json` unmodified; nothing committed.

**SHIP** ✅ — R4 artifact removed, R5 spec made fair & provably passable, verdicts
re-scored and honest.
