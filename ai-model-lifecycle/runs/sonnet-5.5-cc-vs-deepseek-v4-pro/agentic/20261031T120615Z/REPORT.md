# Agentic runs — sonnet-5.5-cc-vs-deepseek-v4-pro · run 20261031T120615Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | Claude Sonnet 5.5 (CC) | medium | 3/3 | 0.8 | $0.07 | 5 |
| r3_oracle_to_postgres | Claude Sonnet 5.5 (CC) | medium | 3/3 | 0.6 | $0.08 | 4 |
| r4_schema_load_optimize | Claude Sonnet 5.5 (CC) | medium | 3/3 | 0.5 | $0.05 | 4 |
| r5_etl_dashboard | Claude Sonnet 5.5 (CC) | medium | 3/3 | 1.8 | $0.10 | 7 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | Claude Sonnet 5.5 (CC) | ✅ | 0.9 | $0.07 | 5 | 4 | 10 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | Claude Sonnet 5.5 (CC) | ✅ | 0.9 | $0.06 | 5 | 4 | 10 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | Claude Sonnet 5.5 (CC) | ✅ | 0.6 | $0.06 | 4 | 3 | 10 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | Claude Sonnet 5.5 (CC) | ✅ | 0.6 | $0.09 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | Claude Sonnet 5.5 (CC) | ✅ | 0.7 | $0.08 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | Claude Sonnet 5.5 (CC) | ✅ | 0.5 | $0.07 | 3 | 2 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | Claude Sonnet 5.5 (CC) | ✅ | 0.5 | $0.07 | 4 | 3 | 1 | index scan on orders, no seq scan, 41.4ms < 1000.0ms |
| r4_schema_load_optimize | 2 | Claude Sonnet 5.5 (CC) | ✅ | 0.4 | $0.04 | 3 | 2 | 1 | index scan on orders, no seq scan, 28.0ms < 1000.0ms |
| r4_schema_load_optimize | 3 | Claude Sonnet 5.5 (CC) | ✅ | 0.7 | $0.05 | 5 | 4 | 1 | index scan on orders, no seq scan, 27.1ms < 1000.0ms |
| r5_etl_dashboard | 1 | Claude Sonnet 5.5 (CC) | ✅ | 1.0 | $0.10 | 5 | 3 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | Claude Sonnet 5.5 (CC) | ✅ | 3.8 | $0.12 | 11 | 9 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | Claude Sonnet 5.5 (CC) | ✅ | 0.8 | $0.09 | 5 | 3 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
