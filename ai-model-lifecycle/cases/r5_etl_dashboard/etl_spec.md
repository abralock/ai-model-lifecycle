# R5 ETL specification — source → aggregate → dashboard

> Input to the "Implement ETL and reconcile" task. The source tables are those
> created in R4 (`customers`, `products`, `orders`, `order_items`); the ETL must
> consume **the model's own R4 outputs** (continuity chain R4 → R5).

## 1. Sources

| Table | Grain | Key columns |
|---|---|---|
| `orders` | one row per order | order_id, customer_id, order_date, status, total_amount |
| `order_items` | one row per order line | order_item_id, order_id, product_id, quantity, unit_price |
| `products` | one row per product | product_id, product_name, category, unit_price |
| `customers` | one row per customer | customer_id, customer_name, email, country |

## 2. Business rules

- Only orders with `status = 'COMPLETED'` contribute to revenue.
- Revenue for a line = `quantity * unit_price`.
- Dates are bucketed to a **month** (`YYYY-MM`, from `orders.order_date`).
- **An order has a single category for reporting.** When an order's lines span
  more than one product category, the order is attributed to its *controlling
  category* — the category of the line with the smallest `order_item_id` (the
  order's first line). See §5 for why this is required by the reconciliation.

## 3. Target (dashboard) tables

Defined in `dashboard_schema.sql`:

| Table | Grain | Columns |
|---|---|---|
| `dash_revenue_by_category` | month × category | month, category, revenue, order_count, units_sold |
| `dash_revenue_by_country`  | month × country  | month, country, revenue, customer_count |
| `etl_run_log`              | one row per run  | run_id, started_at, finished_at, source_order_count, loaded_order_count, mismatch |

## 4. Transforms

1. `dash_revenue_by_category` ← assign each COMPLETED order its controlling
   category (§2/§5.1), then group by month + category: sum the controlling line's
   revenue, count distinct orders, sum the controlling line's units.
2. `dash_revenue_by_country` ← join orders→customers on COMPLETED orders,
   group by month + country, sum revenue, count distinct customers.
3. `etl_run_log` ← one reconciliation row per ETL execution.

## 5. Reconciliation requirement (hard gate)

### 5.1 The problem the reconciliation must solve

`orders` is the **order-level** source of truth. `dash_revenue_by_category` is a
`month × category` rollup, and an order can contain line items spanning **more
than one product category**. A naive `SUM(order_count)` over the rollup therefore
counts a multi-category order once per category it touches and **overstates** the
order count (it can never reconcile to a zero mismatch).

To make the rollup and the order-level source comparable, the ETL must assign
each order to **exactly one** category before aggregating — the order's
*single controlling category*. Define it as the category of the order's
lowest-`order_item_id` line (i.e. the order's first line item).

That gives a category rollup with the same grain as `orders`, so every COMPLETED
order contributes to **exactly one** `(month, category)` row and no order is
dropped:

- `order_count` = number of DISTINCT orders whose controlling category is that
  `(month, category)`.
- `revenue` / `units_sold` = the order's **controlling line** (`quantity *
  unit_price`, `quantity`), so an order's full contribution is attributed once
  and no revenue is double-counted across categories.

### 5.2 The reconciliation formula (hard gate)

```
source_order_count = COUNT(*) FROM orders WHERE status = 'COMPLETED'
loaded_order_count = SUM(order_count) FROM dash_revenue_by_category
mismatch           = source_order_count - loaded_order_count   -- MUST be 0
```

`mismatch` is a **signed** order-count difference, recorded in `etl_run_log`.

- **mismatch must equal 0.** This is only achievable when each COMPLETED order is
  attributed to exactly one category (see 5.1). Aggregating line-level rows
  directly with `GROUP BY month, category` and summing `order_count` will not
  reconcile on multi-category orders and must be rejected by the gate.
- The dashboard dataset **must still be non-empty**: every COMPLETED order appears
  in `dash_revenue_by_category` exactly once, so `source_order_count ==
  SUM(order_count) > 0`.
- **Every COMPLETED order must be attributed.** If a COMPLETED order has no
  line items (or no joinable product) it must still be counted — bucket it under a
  sentinel category (e.g. `'(no items)'`) rather than dropping it, or the count
  will under-reconcile.
- The ETL must be **idempotent**: running it twice against the same source must
  not double-count (truncate/upsert the dashboard tables, don't append).

> Implementation note (the intended read of this rule): do NOT sum the
> line-level rollup's `order_count`. Aggregate at the order grain — assign each
> order its controlling category, then count DISTINCT orders per `month ×
> category`. That is what makes the formula achievable without dumbing the gate
> down: `mismatch = 0` remains the success signal, and a broken dedup still
> fails it.
