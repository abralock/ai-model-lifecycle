# R5 — ETL into Dashboard + Reconciliation

**Status: FROZEN.**

## What this case is

Build an ETL that transforms the R4 source tables (`orders`, `order_items`,
`products`, `customers`) into the dashboard aggregate tables defined in
`dashboard_schema.sql`, and **reconcile** row counts so `mismatch = 0`.

This is the last link in the **R3 → R4 → R5** continuity chain: the model's ETL
runs against **its own** R4-loaded tables, not a clean fixture.

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
| etl runs | model ETL executes without error |
| reconciliation | `source_order_count - loaded_order_count == 0` |
| idempotent | second run leaves dashboard row counts unchanged |
| dataset loads | both dashboard tables non-empty |

**Score = pass / fail.**
