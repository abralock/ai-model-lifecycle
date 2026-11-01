# Agentic runs — opus-5.5-cc-vs-kimi-k3 · run 20261031T183901Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | Claude Opus 5.5 (CC) | high | 3/3 | 1.6 | $0.36 | 11 |
| r3_oracle_to_postgres | Claude Opus 5.5 (CC) | high | 3/3 | 1.3 | $0.28 | 6 |
| r4_schema_load_optimize | Claude Opus 5.5 (CC) | high | 3/3 | 1.5 | $0.31 | 7 |
| r5_etl_dashboard | Claude Opus 5.5 (CC) | high | 3/3 | 5.4 | $0.62 | 13 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | Claude Opus 5.5 (CC) | ✅ | 1.4 | $0.39 | 10 | 9 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | Claude Opus 5.5 (CC) | ✅ | 2.1 | $0.38 | 13 | 12 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | Claude Opus 5.5 (CC) | ✅ | 1.4 | $0.32 | 9 | 8 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | Claude Opus 5.5 (CC) | ✅ | 1.6 | $0.36 | 8 | 7 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | Claude Opus 5.5 (CC) | ✅ | 1.1 | $0.25 | 5 | 4 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | Claude Opus 5.5 (CC) | ✅ | 1.1 | $0.22 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | Claude Opus 5.5 (CC) | ✅ | 1.3 | $0.30 | 7 | 6 | 1 | index scan on orders, no seq scan, 32.5ms < 1000.0ms |
| r4_schema_load_optimize | 2 | Claude Opus 5.5 (CC) | ✅ | 1.5 | $0.30 | 7 | 6 | 1 | index scan on orders, no seq scan, 30.1ms < 1000.0ms |
| r4_schema_load_optimize | 3 | Claude Opus 5.5 (CC) | ✅ | 1.7 | $0.33 | 8 | 7 | 1 | index scan on orders, no seq scan, 34.7ms < 1000.0ms |
| r5_etl_dashboard | 1 | Claude Opus 5.5 (CC) | ✅ | 4.0 | $0.63 | 12 | 11 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | Claude Opus 5.5 (CC) | ✅ | 2.5 | $0.51 | 10 | 9 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | Claude Opus 5.5 (CC) | ✅ | 9.6 | $0.73 | 17 | 16 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
