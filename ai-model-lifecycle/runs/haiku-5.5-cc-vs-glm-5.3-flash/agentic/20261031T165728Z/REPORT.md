# Agentic runs — haiku-5.5-cc-vs-glm-5.3-flash · run 20261031T165728Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | Claude Haiku 5.5 (CC) | high | 3/3 | 5.1 | $0.03 | 24 |
| r3_oracle_to_postgres | Claude Haiku 5.5 (CC) | high | 3/3 | 1.8 | $0.02 | 14 |
| r4_schema_load_optimize | Claude Haiku 5.5 (CC) | high | 3/3 | 2.1 | $0.02 | 16 |
| r5_etl_dashboard | Claude Haiku 5.5 (CC) | high | 3/3 | 3.5 | $0.02 | 13 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | Claude Haiku 5.5 (CC) | ✅ | 5.9 | $0.03 | 36 | 35 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | Claude Haiku 5.5 (CC) | ✅ | 4.2 | $0.03 | 21 | 20 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | Claude Haiku 5.5 (CC) | ✅ | 5.2 | $0.03 | 16 | 15 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | Claude Haiku 5.5 (CC) | ✅ | 1.4 | $0.02 | 10 | 9 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | Claude Haiku 5.5 (CC) | ✅ | 1.6 | $0.02 | 12 | 11 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | Claude Haiku 5.5 (CC) | ✅ | 2.3 | $0.02 | 19 | 18 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | Claude Haiku 5.5 (CC) | ✅ | 2.1 | $0.02 | 16 | 15 | 1 | index scan on orders, no seq scan, 33.6ms < 1000.0ms |
| r4_schema_load_optimize | 2 | Claude Haiku 5.5 (CC) | ✅ | 1.4 | $0.02 | 9 | 8 | 1 | index scan on orders, no seq scan, 35.0ms < 1000.0ms |
| r4_schema_load_optimize | 3 | Claude Haiku 5.5 (CC) | ✅ | 2.9 | $0.03 | 22 | 21 | 1 | index scan on orders, no seq scan, 27.4ms < 1000.0ms |
| r5_etl_dashboard | 1 | Claude Haiku 5.5 (CC) | ✅ | 5.4 | $0.03 | 14 | 13 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | Claude Haiku 5.5 (CC) | ✅ | 2.1 | $0.02 | 14 | 13 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | Claude Haiku 5.5 (CC) | ✅ | 3.0 | $0.02 | 12 | 11 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
