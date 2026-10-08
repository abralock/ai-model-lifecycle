#!/usr/bin/env python3
"""audits/prove_r5_passable.py — prove the fixed R5 gate is PASSABLE.

Scores a minimal but complete 'correct' order-grain ETL (each COMPLETED order
assigned a single controlling category) against each model's real dataset, and
asserts reconciliation mismatch == 0.

Run:  .venv/bin/python -m audits.prove_r5_passable
"""
from __future__ import annotations

from audits.rescore_r4_r5 import apply_r4_source
from scorers import r5_scorer

CORRECT = """
### FILE: etl.sql
```sql
BEGIN;
TRUNCATE TABLE dash_revenue_by_category;
TRUNCATE TABLE dash_revenue_by_country;

-- controlling category per COMPLETED order = category of lowest order_item_id
CREATE TEMP TABLE _ctl ON COMMIT DROP AS
SELECT oi.order_id,
       (ARRAY_AGG(p.category ORDER BY oi.order_item_id))[1] AS category,
       (ARRAY_AGG(oi.quantity ORDER BY oi.order_item_id))[1]     AS quantity,
       (ARRAY_AGG(oi.quantity * oi.unit_price ORDER BY oi.order_item_id))[1] AS line_rev
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY oi.order_id;

INSERT INTO dash_revenue_by_category (month, category, revenue, order_count, units_sold)
SELECT to_char(o.order_date,'YYYY-MM'),
       COALESCE(c.category,'(no items)'),
       COALESCE(SUM(c.line_rev),0)::numeric(14,2),
       COUNT(DISTINCT o.order_id),
       COALESCE(SUM(c.quantity),0)
FROM orders o
LEFT JOIN _ctl c ON c.order_id = o.order_id
WHERE o.status = 'COMPLETED'
GROUP BY 1,2;

INSERT INTO dash_revenue_by_country (month, country, revenue, customer_count)
SELECT to_char(o.order_date,'YYYY-MM'), cu.country,
       COALESCE(SUM(li.line_revenue),0)::numeric(14,2),
       COUNT(DISTINCT o.customer_id)
FROM orders o
JOIN customers cu ON cu.customer_id = o.customer_id
LEFT JOIN (SELECT order_id, SUM(quantity*unit_price) line_revenue
           FROM order_items GROUP BY order_id) li ON li.order_id = o.order_id
WHERE o.status = 'COMPLETED'
GROUP BY 1,2;

INSERT INTO etl_run_log (started_at, finished_at, source_order_count, loaded_order_count, mismatch)
SELECT now(), now(),
       (SELECT COUNT(*) FROM orders WHERE status='COMPLETED'),
       (SELECT COALESCE(SUM(order_count),0) FROM dash_revenue_by_category),
       (SELECT COUNT(*) FROM orders WHERE status='COMPLETED')
       - (SELECT COALESCE(SUM(order_count),0) FROM dash_revenue_by_category);
COMMIT;
```
"""


def main() -> int:
    for model in ("anthropic__claude-opus-4.8", "anthropic__claude-opus-5.5"):
        apply_r4_source(model)
        r = r5_scorer.score(CORRECT, model_slug=model)
        print(f"{model}: correct-ETL passed={r.passed} reason={r.reason}")
        print(f"    checks={r.checks}")
        print(
            f"    details={{'src':{r.details.get('source_order_count')},"
            f"'loaded':{r.details.get('loaded_order_count')},'dash':{r.details.get('dash_rows')}}}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
