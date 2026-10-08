# Task: Convert Oracle PL/SQL procedures to PostgreSQL plpgsql

Attached are two **Oracle PL/SQL** stored procedures plus their table DDL
(`sp_customer_tier.sql`, `sp_monthly_report.sql`). Convert them to **PostgreSQL
plpgsql** so they produce identical result sets.

## Requirements

1. Produce PostgreSQL-compatible `CREATE TABLE` DDL for all referenced tables
   (`customers`, `orders`, `customer_tiers`, `products`, `order_items`,
   `monthly_report`), mapping Oracle types to Postgres:
   - `NUMBER`/`NUMBER(n)` → `numeric` / `bigint`
   - `VARCHAR2(n)` → `varchar(n)`
   - `DATE` → `timestamptz`
2. Reimplement **both** procedures as `CREATE OR REPLACE PROCEDURE ... LANGUAGE plpgsql`:
   - `sp_customer_tier` — cursor/loop over aggregated orders → inserts tier rows
     (`GOLD` ≥ 1000, `SILVER` ≥ 500, else `BRONZE`).
   - `sp_monthly_report(p_month varchar)` — aggregate order_items by category into
     `monthly_report`, with exception handling.
3. Remove **all** Oracle-only constructs — the output must contain **none** of:
   `DUAL`, `NVL(`, `ROWNUM`, `(+)`, `VARCHAR2`, `sysdate`, `%ROWTYPE`, `%TYPE`.
   Use `COALESCE`, `now()`, and standard plpgsql.
4. Result sets must match the golden outputs exactly:
   - `sp_customer_tier()` → rows `(customer_id, customer_name, total_spend, order_count, tier)`
   - `sp_monthly_report('2026-09')` → rows `(report_month, category, revenue, units_sold)`

## Output format

Emit each SQL file in a fenced block preceded by a header line
`### FILE: <relative/path>`, e.g.:

```
### FILE: postgres/schema.sql
...
### FILE: postgres/procedures.sql
...
```

Put table DDL in one file and the procedures in another. No commentary outside blocks.
