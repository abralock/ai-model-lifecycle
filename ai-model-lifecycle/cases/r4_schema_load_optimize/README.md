# R4 — Schema + Bulk Load + Optimize

**Status: FROZEN.**

## What this case is

Given 4 table definitions and a target query that is slow without an index, the
model must: create the tables, bulk-load ~100k rows, and **add the correct index**
so the target query is served by an **index scan** (no seq scan on `orders`).

## Input

```
schema.sql        # DDL for customers/products/orders/order_items (NO indexes)
seed.py           # parameterizable deterministic bulk loader (default 100k orders)
target_query.sql  # SELECT filtered on orders.status + orders.order_date
```

## Task (prompt.md)

Create tables, load data, add the index that makes `target_query.sql` use an index
scan, and (optionally) report the `EXPLAIN` plan + timing before/after.

## Expected outcome

- DDL valid, ~N rows loaded (N default 100000).
- `EXPLAIN (ANALYZE, BUFFERS) target_query` shows an **index scan**
  (`Index Scan` or `Bitmap Index Scan`) on `orders` — **no `Seq Scan`** on `orders`.
- Query latency below the scorer threshold (default 1000 ms).

The natural correct index is on `orders(status, order_date)` (multi-column, filter
order = status first for selectivity, then date range).

## Pass criteria (automated — see `scorers/r4_scorer.py`)

| Check | Rule |
|---|---|
| ddl | schema applies cleanly |
| loaded | row count == expected N |
| index scan | plan contains an index/bitmap scan on orders |
| no seq scan | plan contains no `Seq Scan on orders` |
| latency | measured query time < threshold_ms |

**Score = pass / fail.**
