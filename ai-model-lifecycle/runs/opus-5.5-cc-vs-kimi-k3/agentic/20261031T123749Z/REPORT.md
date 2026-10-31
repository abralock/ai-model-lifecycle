# Agentic runs — opus-5.5-cc-vs-kimi-k3 · run 20261031T123749Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | Claude Opus 5.5 (CC) | medium | 3/3 | 1.1 | $0.25 | 8 |
| r3_oracle_to_postgres | Claude Opus 5.5 (CC) | medium | 3/3 | 1.0 | $0.22 | 4 |
| r4_schema_load_optimize | Claude Opus 5.5 (CC) | medium | 3/3 | 1.2 | $0.25 | 6 |
| r5_etl_dashboard | Claude Opus 5.5 (CC) | medium | 3/3 | 4.0 | $0.47 | 12 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | Claude Opus 5.5 (CC) | ✅ | 1.4 | $0.28 | 7 | 6 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | Claude Opus 5.5 (CC) | ✅ | 0.7 | $0.24 | 6 | 5 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | Claude Opus 5.5 (CC) | ✅ | 1.3 | $0.25 | 10 | 9 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | Claude Opus 5.5 (CC) | ✅ | 1.0 | $0.25 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | Claude Opus 5.5 (CC) | ✅ | 0.9 | $0.21 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | Claude Opus 5.5 (CC) | ✅ | 1.1 | $0.21 | 4 | 3 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | Claude Opus 5.5 (CC) | ✅ | 1.6 | $0.36 | 9 | 8 | 1 | index scan on orders, no seq scan, 29.9ms < 1000.0ms |
| r4_schema_load_optimize | 2 | Claude Opus 5.5 (CC) | ✅ | 0.9 | $0.18 | 4 | 3 | 1 | index scan on orders, no seq scan, 28.5ms < 1000.0ms |
| r4_schema_load_optimize | 3 | Claude Opus 5.5 (CC) | ✅ | 1.1 | $0.20 | 5 | 4 | 1 | index scan on orders, no seq scan, 29.8ms < 1000.0ms |
| r5_etl_dashboard | 1 | Claude Opus 5.5 (CC) | ✅ | 2.1 | $0.52 | 12 | 10 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | Claude Opus 5.5 (CC) | ✅ | 5.1 | $0.37 | 11 | 10 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | Claude Opus 5.5 (CC) | ✅ | 4.9 | $0.51 | 14 | 13 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
