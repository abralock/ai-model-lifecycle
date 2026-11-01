# Agentic runs — haiku-5.5-cc-vs-glm-5.3-flash · run 20261101T011617Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | Claude Haiku 5.5 (CC) | low | 3/3 | 2.9 | $0.02 | 16 |
| r3_oracle_to_postgres | Claude Haiku 5.5 (CC) | low | 3/3 | 0.8 | $0.01 | 11 |
| r4_schema_load_optimize | Claude Haiku 5.5 (CC) | low | 3/3 | 1.1 | $0.01 | 13 |
| r5_etl_dashboard | Claude Haiku 5.5 (CC) | low | 3/3 | 2.4 | $0.01 | 11 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | Claude Haiku 5.5 (CC) | ✅ | 2.2 | $0.01 | 12 | 11 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | Claude Haiku 5.5 (CC) | ✅ | 2.8 | $0.02 | 18 | 17 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | Claude Haiku 5.5 (CC) | ✅ | 3.6 | $0.02 | 18 | 17 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | Claude Haiku 5.5 (CC) | ✅ | 0.9 | $0.01 | 11 | 10 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | Claude Haiku 5.5 (CC) | ✅ | 0.8 | $0.01 | 10 | 9 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | Claude Haiku 5.5 (CC) | ✅ | 0.8 | $0.01 | 11 | 10 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | Claude Haiku 5.5 (CC) | ✅ | 1.2 | $0.02 | 13 | 12 | 1 | index scan on orders, no seq scan, 29.6ms < 1000.0ms |
| r4_schema_load_optimize | 2 | Claude Haiku 5.5 (CC) | ✅ | 1.4 | $0.02 | 16 | 15 | 1 | index scan on orders, no seq scan, 21.0ms < 1000.0ms |
| r4_schema_load_optimize | 3 | Claude Haiku 5.5 (CC) | ✅ | 0.9 | $0.01 | 10 | 9 | 1 | index scan on orders, no seq scan, 28.3ms < 1000.0ms |
| r5_etl_dashboard | 1 | Claude Haiku 5.5 (CC) | ✅ | 0.9 | $0.01 | 8 | 7 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | Claude Haiku 5.5 (CC) | ✅ | 3.2 | $0.02 | 12 | 11 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | Claude Haiku 5.5 (CC) | ✅ | 3.0 | $0.02 | 14 | 13 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
