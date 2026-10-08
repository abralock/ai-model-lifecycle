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

## 3. Target (dashboard) tables

Defined in `dashboard_schema.sql`:

| Table | Grain | Columns |
|---|---|---|
| `dash_revenue_by_category` | month × category | month, category, revenue, order_count, units_sold |
| `dash_revenue_by_country`  | month × country  | month, country, revenue, customer_count |
| `etl_run_log`              | one row per run  | run_id, started_at, finished_at, source_order_count, loaded_order_count, mismatch |

## 4. Transforms

1. `dash_revenue_by_category` ← join order_items→orders→products on COMPLETED orders,
   group by month + category, sum revenue, count distinct orders, sum units.
2. `dash_revenue_by_country` ← join orders→customers on COMPLETED orders,
   group by month + country, sum revenue, count distinct customers.
3. `etl_run_log` ← one reconciliation row per ETL execution.

## 5. Reconciliation requirement (hard gate)

```
source_order_count = COUNT(*) FROM orders WHERE status = 'COMPLETED'
loaded_order_count = SUM(order_count) FROM dash_revenue_by_category
mismatch           = source_order_count - loaded_order_count   -- MUST be 0
```

- **mismatch must equal 0.**
- The ETL must be **idempotent**: running it twice against the same source must
  not double-count (truncate/upsert the dashboard tables, don't append).
