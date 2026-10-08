# Task: Create tables, bulk-load data, and optimize the target query

You are given a Postgres schema (`schema.sql`) defining four tables
(`customers`, `products`, `orders`, `order_items`) and a `target_query.sql` that
joins them with a filter on `orders.status` and `orders.order_date`.

## Requirements

1. Produce the DDL to create the four tables exactly as specified in `schema.sql`.
2. Provide a bulk-load plan for ~100,000 orders (and corresponding order_items).
   The dataset distribution is documented: `status` is one of
   `COMPLETED/PENDING/CANCELLED/REFUNDED` (COMPLETED ≈ 50%), `order_date` spans
   2025-06-01..2026-09-30.
3. Add **the index** (or indexes) needed so that `target_query.sql` is served by
   an **index scan** — specifically, no sequential scan on `orders`.
4. The target query must complete in **under 1 second** on the loaded dataset.

## Deliverable

Emit a single SQL script in a fenced block headed with:

```
### FILE: solution.sql
```

The script must: create the tables, load the data, and create the index(es), in that
order. Use `CREATE INDEX` (or `CREATE INDEX IF NOT EXISTS`). Justify your index
choice in a `--` comment above it. No commentary outside the code block.
