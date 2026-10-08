-- ============================================================================
-- R4 target query — must be served by an index scan after optimization.
-- ============================================================================
-- Correlated join across order_items -> orders -> products, filtered on
-- orders.status and orders.order_date. Expected EXPLAIN: index scan on orders
-- (or bitmap index scan) — NOT a seq scan on orders.
-- ============================================================================

SELECT p.category,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       COUNT(*)                         AS line_count
FROM   order_items oi
JOIN   orders   o ON o.order_id    = oi.order_id
JOIN   products p ON p.product_id  = oi.product_id
WHERE  o.status = 'COMPLETED'
  AND  o.order_date >= DATE '2026-01-01'
GROUP  BY p.category
ORDER  BY revenue DESC;
