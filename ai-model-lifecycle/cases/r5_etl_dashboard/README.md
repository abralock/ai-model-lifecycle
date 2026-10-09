# R5 — ETL into Dashboard + Reconciliation

**Status: FROZEN.**

## What this case is

Build an ETL that transforms the R4 source tables (`orders`, `order_items`,
`products`, `customers`) into the dashboard aggregate tables defined in
`dashboard_schema.sql`, and **reconcile** row counts so `mismatch = 0`.

Designed as the last link in the **R3 → R4 → R5** continuity chain. For a fair
comparison the scorer runs every model's ETL against the **same fixed dataset**
(R4 schema + deterministic seed, extended with multi-category orders and
COMPLETED orders without lines) in an isolated schema. Scoring the ETL on each
model's own R4 data made results depend on scoring order; continuity should be
scored as a separate, explicit check.

## Input

```
etl_spec.md            # source → transform → target spec + reconciliation rule
dashboard_schema.sql   # target aggregate tables
```

## Task (prompt.md)

Implement the ETL (as SQL — a stored procedure or idempotent script) that loads
`dash_revenue_by_category` and `dash_revenue_by_country` from the source tables,
then writes a reconciliation row into `etl_run_log` with `mismatch = 0`.
Running it twice must be idempotent.

## Expected outcome

- ETL runs end-to-end without error.
- `dash_revenue_by_category` and `dash_revenue_by_country` populated.
- `etl_run_log.mismatch = 0` for the run.
- Re-running the ETL does not change the row counts (idempotent — truncate or upsert).

## Pass criteria (automated — see `scorers/r5_scorer.py`)

| Check | Rule |
|---|---|
| etl runs | model ETL executes without error under `psql` (ON_ERROR_STOP) |
| reconciliation | `source_order_count - SUM(order_count) == 0` **and** `SUM(order_count) > 0` (independently recomputed from `orders`) |
| log row | the model's own `etl_run_log` row records `mismatch == 0` |
| dataset loads | both dashboard tables non-empty |
| idempotent | second run succeeds and leaves dashboard row counts and `SUM(order_count)` unchanged |

**Score = pass / fail.** Note the reconciliation rule is only satisfiable when
each COMPLETED order is attributed to exactly one category (an order's
controlling category) — see `etl_spec.md` §2 and §5.
