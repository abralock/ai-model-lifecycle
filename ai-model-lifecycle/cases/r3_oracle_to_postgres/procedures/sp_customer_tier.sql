-- ============================================================================
-- R3 case input — Oracle PL/SQL stored procedure #1: cursor + loop
-- ============================================================================
-- Computes customer lifetime tier from orders. Reads orders with an explicit
-- cursor, loops row-by-row, and writes an aggregate row per customer.
-- Uses Oracle-only constructs: DUAL, NVL, sysdate, %TYPE, a SEQUENCE, and a
-- cursor FOR loop. Must be translated to PostgreSQL plpgsql.
-- ============================================================================

CREATE TABLE customers (
    customer_id   NUMBER PRIMARY KEY,
    customer_name VARCHAR2(120) NOT NULL,
    status        VARCHAR2(20)  DEFAULT 'ACTIVE'
);

CREATE TABLE orders (
    order_id    NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    order_total NUMBER(12,2) NOT NULL,
    order_date  DATE NOT NULL
);

CREATE TABLE customer_tiers (
    customer_id    NUMBER PRIMARY KEY,
    customer_name  VARCHAR2(120),
    total_spend    NUMBER(12,2),
    order_count    NUMBER,
    tier           VARCHAR2(20),
    computed_at    DATE
);

CREATE SEQUENCE seq_tier_id START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE PROCEDURE sp_customer_tier AS
    v_tier   VARCHAR2(20);
    v_status customers.status%TYPE;
BEGIN
    DELETE FROM customer_tiers;

    FOR rec IN (
        SELECT o.customer_id,
               c.customer_name,
               SUM(o.order_total) AS total_spend,
               COUNT(*)           AS order_count
        FROM   orders o
        JOIN   customers c ON c.customer_id = o.customer_id
        WHERE  NVL(c.status, 'ACTIVE') = 'ACTIVE'
        GROUP  BY o.customer_id, c.customer_name
    ) LOOP
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
             v_tier, sysdate);
    END LOOP;

    SELECT status INTO v_status FROM customers WHERE ROWNUM = 1;
    COMMIT;
END;
/
