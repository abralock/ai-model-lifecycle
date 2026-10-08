# Task: Implement the ETL and reconcile

Attached is the ETL specification (`etl_spec.md`) and the dashboard target schema
(`dashboard_schema.sql`). Implement the ETL that populates the dashboard tables
from the source tables (`orders`, `order_items`, `products`, `customers`).

## Requirements

1. Write SQL to populate `dash_revenue_by_category`:
   month × category rollup over **COMPLETED** orders, with `revenue`,
   `order_count` (distinct orders), `units_sold`.
2. Write SQL to populate `dash_revenue_by_country`: month × country rollup over
   COMPLETED orders, with `revenue` and `customer_count` (distinct customers).
3. Write the reconciliation step: insert a row into `etl_run_log` where
   `source_order_count = COUNT(*) FROM orders WHERE status='COMPLETED'`,
   `loaded_order_count = SUM(order_count) FROM dash_revenue_by_category`, and
   `mismatch = source_order_count - loaded_order_count`. **`mismatch` must be 0.**
   Note that an order can span multiple product categories, so `order_count`
   must be de-duplicated at the order grain — see `etl_spec.md` §2 and §5.
4. Make the ETL **idempotent**: running it twice must not double-count.

## Deliverable

Emit a single SQL script in a fenced block headed with:

```
### FILE: etl.sql
```

The script must run top-to-bottom on the source tables and produce the reconciled
dashboard dataset. Use `TRUNCATE` or `INSERT ... ON CONFLICT` for idempotency.
No commentary outside the code block.
