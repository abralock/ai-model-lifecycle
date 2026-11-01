# Agentic runs — opus-5.5-cc-vs-glm-5.3 · run 20261101T044458Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | GLM-5.3 · opencode | medium | 3/3 | 2.3 | $0.14 | 14 |
| r3_oracle_to_postgres | GLM-5.3 · opencode | medium | 3/3 | 8.9 | $0.64 | 29 |
| r4_schema_load_optimize | GLM-5.3 · opencode | medium | 3/3 | 9.7 | $0.68 | 24 |
| r5_etl_dashboard | GLM-5.3 · opencode | medium | 3/3 | 9.3 | $0.58 | 26 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | GLM-5.3 · opencode | ✅ | 1.7 | $0.10 | 10 | 44 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 2 | GLM-5.3 · opencode | ✅ | 3.9 | $0.22 | 13 | 45 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r1_springboot2to3 | 3 | GLM-5.3 · opencode | ✅ | 1.4 | $0.11 | 18 | 41 | 11 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
| r3_oracle_to_postgres | 1 | GLM-5.3 · opencode | ✅ | 7.8 | $0.65 | 35 | 48 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 2 | GLM-5.3 · opencode | ✅ | 7.6 | $0.39 | 15 | 25 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r3_oracle_to_postgres | 3 | GLM-5.3 · opencode | ✅ | 11.1 | $0.86 | 37 | 42 | 2 | plpgsql translation matches golden result set; no oracle dialect tokens |
| r4_schema_load_optimize | 1 | GLM-5.3 · opencode | ✅ | 6.0 | $0.37 | 18 | 23 | 1 | index scan on orders, no seq scan, 33.9ms < 1000.0ms |
| r4_schema_load_optimize | 2 | GLM-5.3 · opencode | ✅ | 11.4 | $0.89 | 29 | 34 | 1 | index scan on orders, no seq scan, 31.1ms < 1000.0ms |
| r4_schema_load_optimize | 3 | GLM-5.3 · opencode | ✅ | 11.6 | $0.77 | 24 | 28 | 1 | index scan on orders, no seq scan, 29.7ms < 1000.0ms |
| r5_etl_dashboard | 1 | GLM-5.3 · opencode | ✅ | 10.8 | $0.78 | 26 | 33 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 2 | GLM-5.3 · opencode | ✅ | 12.0 | $0.60 | 31 | 34 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
| r5_etl_dashboard | 3 | GLM-5.3 · opencode | ✅ | 5.0 | $0.36 | 21 | 25 | 1 | ETL idempotent, dashboard loaded, reconciliation mismatch = 0 |
