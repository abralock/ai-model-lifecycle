-- ============================================================================
-- R4 case input — schema DDL for the "Schema + Bulk Load + Optimize" task.
-- ============================================================================
-- Four related tables. The model must create them, bulk-load ~100k rows, then
-- add the correct index so target_query.sql uses an index scan (no seq scan).
-- NOTE: intentionally NO indexes declared here — the model adds them.
-- ============================================================================

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id   bigint PRIMARY KEY,
    customer_name varchar(120) NOT NULL,
    email         varchar(200) NOT NULL,
    country       varchar(2)   NOT NULL,
    created_at    timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE products (
    product_id   bigint PRIMARY KEY,
    product_name varchar(160) NOT NULL,
    category     varchar(60)  NOT NULL,
    unit_price   numeric(10,2) NOT NULL
);

CREATE TABLE orders (
    order_id     bigint PRIMARY KEY,
    customer_id  bigint NOT NULL REFERENCES customers(customer_id),
    order_date   timestamptz NOT NULL,
    status       varchar(20) NOT NULL,
    total_amount numeric(12,2) NOT NULL
);

CREATE TABLE order_items (
    order_item_id bigint PRIMARY KEY,
    order_id      bigint NOT NULL REFERENCES orders(order_id),
    product_id    bigint NOT NULL REFERENCES products(product_id),
    quantity      integer NOT NULL,
    unit_price    numeric(10,2) NOT NULL
);

-- ============================================================================
-- Target query: "revenue by category for COMPLETED orders since a given date".
-- Without an index on (orders.status, orders.order_date) this does a seq scan on
-- orders; the whole point of the task is to make it an index scan.
-- Read together with target_query.sql.
-- ============================================================================
