-- ============================================================================
-- R3 GOLDEN — known-correct PostgreSQL plpgsql translation of the two Oracle
-- procedures. This is the reference the model's output is compared against
-- (result parity) and is also what the scorer loads to build the schema.
-- ============================================================================
-- Translation notes (Oracle -> Postgres):
--   NUMBER            -> numeric            (or bigint for ids)
--   VARCHAR2(n)       -> varchar(n)         (or text)
--   DATE              -> timestamptz        (Oracle DATE carries time)
--   sysdate           -> now()
--   NVL(a,b)          -> COALESCE(a,b)
--   DUAL              -> (SELECT ...) with no FROM, or `SELECT COUNT(*) ...`
--   ROWNUM = 1        -> LIMIT 1
--   1-based SEQUENCE  -> GENERATED ALWAYS AS IDENTITY
--   %TYPE / %ROWTYPE  -> explicit types / RECORD
--   cursor FOR loop   -> FOR rec IN SELECT ... LOOP
--   exception blocks  -> BEGIN ... EXCEPTION WHEN ... END with RAISE
-- ============================================================================

-- --- schema -----------------------------------------------------------------
DROP TABLE IF EXISTS customer_tiers CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS monthly_report CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE customers (
    customer_id   bigint PRIMARY KEY,
    customer_name varchar(120) NOT NULL,
    status        varchar(20)  DEFAULT 'ACTIVE'
);

CREATE TABLE orders (
    order_id    bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    order_total numeric(12,2) NOT NULL,
    order_date  timestamptz NOT NULL
);

CREATE TABLE customer_tiers (
    customer_id    bigint PRIMARY KEY,
    customer_name  varchar(120),
    total_spend    numeric(12,2),
    order_count    bigint,
    tier           varchar(20),
    computed_at    timestamptz
);

CREATE TABLE products (
    product_id   bigint PRIMARY KEY,
    product_name varchar(120),
    category     varchar(60)
);

CREATE TABLE order_items (
    order_item_id bigint PRIMARY KEY,
    order_id      bigint,
    product_id    bigint,
    quantity      integer,
    unit_price    numeric(10,2)
);

CREATE TABLE monthly_report (
    report_month varchar(7),
    category     varchar(60),
    revenue      numeric(12,2),
    units_sold   bigint
);

-- --- procedure 1: cursor + loop, tiering by spend ---------------------------
CREATE OR REPLACE PROCEDURE sp_customer_tier()
LANGUAGE plpgsql AS $$
DECLARE
    v_tier varchar(20);
BEGIN
    DELETE FROM customer_tiers;

    FOR rec IN
        SELECT o.customer_id,
               c.customer_name,
               SUM(o.order_total) AS total_spend,
               COUNT(*)           AS order_count
        FROM   orders o
        JOIN   customers c ON c.customer_id = o.customer_id
        WHERE  COALESCE(c.status, 'ACTIVE') = 'ACTIVE'
        GROUP  BY o.customer_id, c.customer_name
    LOOP
        IF rec.total_spend >= 1000 THEN
            v_tier := 'GOLD';
        ELSIF rec.total_spend >= 500 THEN
            v_tier := 'SILVER';
        ELSE
            v_tier := 'BRONZE';
        END IF;

        INSERT INTO customer_tiers
            (customer_id, customer_name, total_spend, order_count, tier, computed_at)
        VALUES
            (rec.customer_id, rec.customer_name, rec.total_spend, rec.order_count,
             v_tier, now());
    END LOOP;
END;
$$;

-- --- procedure 2: %ROWTYPE + exception handling -----------------------------
CREATE OR REPLACE PROCEDURE sp_monthly_report(p_month varchar)
LANGUAGE plpgsql AS $$
DECLARE
    v_row      monthly_report%ROWTYPE;
    v_has_data bigint := 0;
BEGIN
    SELECT COUNT(*) INTO v_has_data FROM customers;

    DELETE FROM monthly_report WHERE report_month = p_month;

    FOR rec IN
        SELECT p.category                                   AS category,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue,
               COALESCE(SUM(oi.quantity), 0)                 AS units_sold
        FROM   order_items oi
        JOIN   products p ON p.product_id = oi.product_id
        GROUP  BY p.category
    LOOP
        v_row.report_month := p_month;
        v_row.category     := rec.category;
        v_row.revenue      := rec.revenue;
        v_row.units_sold   := rec.units_sold;

        INSERT INTO monthly_report
            (report_month, category, revenue, units_sold)
        VALUES
            (v_row.report_month, v_row.category, v_row.revenue, v_row.units_sold);
    END LOOP;

    IF v_has_data = 0 THEN
        RAISE EXCEPTION 'no data available';
    END IF;
END;
$$;
