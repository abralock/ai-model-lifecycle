# Agentic runs — opus-5.5-cc-vs-kimi-k3 · run 20261101T024018Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | Claude Opus 5.5 (CC) | low | 3/3 | 0.7 | $0.17 | 7 |
| r3_oracle_to_postgres | Claude Opus 5.5 (CC) | low | 3/3 | 0.6 | $0.14 | 4 |
| r4_schema_load_optimize | Claude Opus 5.5 (CC) | low | 3/3 | 0.6 | $0.14 | 3 |
| r5_etl_dashboard | Claude Opus 5.5 (CC) | low | 3/3 | 0.9 | $0.17 | 5 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | Claude Opus 5.5 (CC) | ✅ | 0.6 | $0.18 | 7 | 6 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | Claude Opus 5.5 (CC) | ✅ | 0.7 | $0.15 | 7 | 6 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | Claude Opus 5.5 (CC) | ✅ | 0.7 | $0.19 | 8 | 7 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | Claude Opus 5.5 (CC) | ✅ | 0.6 | $0.18 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | Claude Opus 5.5 (CC) | ✅ | 0.6 | $0.15 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | Claude Opus 5.5 (CC) | ✅ | 0.5 | $0.08 | 3 | 2 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | Claude Opus 5.5 (CC) | ✅ | 0.8 | $0.16 | 3 | 2 | 1 | index scan on orders, no seq scan, 29.3ms < 1000.0ms |
| r4_schema_load_optimize | 2 | Claude Opus 5.5 (CC) | ✅ | 0.5 | $0.12 | 4 | 3 | 1 | index scan on orders, no seq scan, 30.7ms < 1000.0ms |
| r4_schema_load_optimize | 3 | Claude Opus 5.5 (CC) | ✅ | 0.6 | $0.13 | 3 | 2 | 1 | index scan on orders, no seq scan, 30.7ms < 1000.0ms |
| r5_etl_dashboard | 1 | Claude Opus 5.5 (CC) | ✅ | 0.9 | $0.20 | 5 | 4 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | Claude Opus 5.5 (CC) | ✅ | 1.0 | $0.20 | 6 | 5 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | Claude Opus 5.5 (CC) | ✅ | 0.9 | $0.12 | 5 | 4 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
