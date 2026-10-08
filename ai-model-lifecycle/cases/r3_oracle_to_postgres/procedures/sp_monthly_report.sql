-- ============================================================================
-- R3 case input — Oracle PL/SQL stored procedure #2: %ROWTYPE + exceptions
-- ============================================================================
-- Monthly revenue report per product category. Uses %ROWTYPE, DUAL, NVL,
-- TO_CHAR, a user-defined exception, and an exception handler. Must become
-- PostgreSQL plpgsql.
-- ============================================================================

CREATE TABLE products (
    product_id   NUMBER PRIMARY KEY,
    product_name VARCHAR2(120),
    category     VARCHAR2(60)
);

CREATE TABLE order_items (
    order_item_id NUMBER PRIMARY KEY,
    order_id      NUMBER,
    product_id    NUMBER,
    quantity      NUMBER,
    unit_price    NUMBER(10,2)
);

CREATE TABLE monthly_report (
    report_month   VARCHAR2(7),
    category       VARCHAR2(60),
    revenue        NUMBER(12,2),
    units_sold     NUMBER
);

CREATE OR REPLACE PROCEDURE sp_monthly_report(p_month IN VARCHAR2) AS
    v_row        monthly_report%ROWTYPE;
    v_has_data   NUMBER := 0;
    e_no_data    EXCEPTION;
BEGIN
    SELECT COUNT(*) INTO v_has_data FROM DUAL;

    DELETE FROM monthly_report WHERE report_month = p_month;

    FOR rec IN (
        SELECT p.category                                               AS category,
               NVL(SUM(oi.quantity * oi.unit_price), 0)                 AS revenue,
               NVL(SUM(oi.quantity), 0)                                 AS units_sold
        FROM   order_items oi
        JOIN   products p ON p.product_id = oi.product_id
        GROUP  BY p.category
    ) LOOP
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
        RAISE e_no_data;
    END IF;

    COMMIT;
EXCEPTION
    WHEN e_no_data THEN
        ROLLBACK;
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/
