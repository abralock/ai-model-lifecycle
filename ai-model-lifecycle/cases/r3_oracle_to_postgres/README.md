# R3 — Oracle PL/SQL → PostgreSQL plpgsql

**Status: FROZEN.**

## What this case is

Two Oracle PL/SQL stored procedures must be translated to **PostgreSQL plpgsql**.
The result sets they produce must match the golden outputs exactly.

## Input

```
procedures/sp_customer_tier.sql     # cursor + FOR loop, NVL, DUAL, ROWNUM, SEQUENCE
procedures/sp_monthly_report.sql    # %ROWTYPE, DUAL, NVL, exception block
seed.sql                            # deterministic fixture (loaded before scoring)
golden_postgres.sql                 # known-correct plpgsql (reference; NOT given to model)
golden_output.csv                   # expected result of sp_customer_tier()
golden_output_monthly.csv           # expected result of sp_monthly_report('2026-09')
```

> `golden_postgres.sql` and the golden CSVs are **scorer-only**. The model receives
> only the two Oracle procedure files plus their DDL.

## Task (prompt.md)

Convert both procedures to PostgreSQL plpgsql. Output must compile on Postgres and
produce result sets identical to the golden outputs.

## Expected migrated result

PostgreSQL `CREATE OR REPLACE PROCEDURE ... LANGUAGE plpgsql` definitions + the
supporting table DDL, using:
- `COALESCE` instead of `NVL`
- no `DUAL`, no `ROWNUM`, no `(+)` outer-join syntax
- `now()` instead of `sysdate`
- `numeric`/`varchar`/`timestamptz` instead of `NUMBER`/`VARCHAR2`/`DATE`
- proper `EXCEPTION WHEN ... THEN ...` blocks

## Pass criteria (automated — see `scorers/r3_scorer.py`)

| Check | Rule |
|---|---|
| compiles | model SQL loads into Postgres without error |
| parity | `sp_customer_tier()` result == `golden_output.csv` (set compare, pandas) |
| dialect clean | no Oracle-only tokens: `DUAL`, `NVL(`, `ROWNUM`, `(+)`, `VARCHAR2`, `sysdate` |

**Score = pass / fail.**
