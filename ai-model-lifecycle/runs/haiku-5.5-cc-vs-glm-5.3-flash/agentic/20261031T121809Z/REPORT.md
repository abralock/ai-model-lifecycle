# Agentic runs — haiku-5.5-cc-vs-glm-5.3-flash · run 20261031T121809Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | Claude Haiku 5.5 (CC) | medium | 3/3 | 2.9 | $0.02 | 16 |
| r3_oracle_to_postgres | Claude Haiku 5.5 (CC) | medium | 3/3 | 1.0 | $0.01 | 11 |
| r4_schema_load_optimize | Claude Haiku 5.5 (CC) | medium | 3/3 | 1.1 | $0.01 | 11 |
| r5_etl_dashboard | Claude Haiku 5.5 (CC) | medium | 3/3 | 1.3 | $0.02 | 9 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | Claude Haiku 5.5 (CC) | ✅ | 3.1 | $0.02 | 19 | 18 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | Claude Haiku 5.5 (CC) | ✅ | 2.6 | $0.02 | 13 | 12 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | Claude Haiku 5.5 (CC) | ✅ | 3.1 | $0.02 | 16 | 15 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | Claude Haiku 5.5 (CC) | ✅ | 1.1 | $0.01 | 10 | 9 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | Claude Haiku 5.5 (CC) | ✅ | 1.0 | $0.01 | 11 | 10 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | Claude Haiku 5.5 (CC) | ✅ | 1.0 | $0.01 | 12 | 11 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | Claude Haiku 5.5 (CC) | ✅ | 1.2 | $0.01 | 14 | 13 | 1 | index scan on orders, no seq scan, 30.9ms < 1000.0ms |
| r4_schema_load_optimize | 2 | Claude Haiku 5.5 (CC) | ✅ | 1.3 | $0.02 | 15 | 14 | 1 | index scan on orders, no seq scan, 30.4ms < 1000.0ms |
| r4_schema_load_optimize | 3 | Claude Haiku 5.5 (CC) | ✅ | 0.7 | $0.01 | 5 | 4 | 1 | index scan on orders, no seq scan, 20.9ms < 1000.0ms |
| r5_etl_dashboard | 1 | Claude Haiku 5.5 (CC) | ✅ | 1.2 | $0.02 | 9 | 8 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | Claude Haiku 5.5 (CC) | ✅ | 1.1 | $0.01 | 7 | 6 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | Claude Haiku 5.5 (CC) | ✅ | 1.5 | $0.02 | 12 | 11 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
