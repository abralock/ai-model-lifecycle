-- ============================================================================
-- R5 dashboard target schema — the aggregate tables the ETL must populate.
-- ============================================================================

DROP TABLE IF EXISTS dash_revenue_by_category CASCADE;
DROP TABLE IF EXISTS dash_revenue_by_country  CASCADE;
DROP TABLE IF EXISTS etl_run_log              CASCADE;

-- month × category revenue rollup (primary dashboard dataset)
CREATE TABLE dash_revenue_by_category (
    month       varchar(7)  NOT NULL,     -- 'YYYY-MM'
    category    varchar(60) NOT NULL,
    revenue     numeric(14,2) NOT NULL,
    order_count bigint      NOT NULL,     -- distinct orders (for reconciliation)
    units_sold  bigint      NOT NULL,
    PRIMARY KEY (month, category)
);

-- month × country revenue rollup
CREATE TABLE dash_revenue_by_country (
    month          varchar(7)  NOT NULL,
    country        varchar(2)  NOT NULL,
    revenue        numeric(14,2) NOT NULL,
    customer_count bigint      NOT NULL,  -- distinct customers
    PRIMARY KEY (month, country)
);

-- one reconciliation row per ETL run
CREATE TABLE etl_run_log (
    run_id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at           timestamptz NOT NULL,
    finished_at          timestamptz NOT NULL,
    source_order_count   bigint NOT NULL,
    loaded_order_count   bigint NOT NULL,
    mismatch             bigint NOT NULL,
    CONSTRAINT mismatch_must_be_zero CHECK (mismatch >= 0)
);
