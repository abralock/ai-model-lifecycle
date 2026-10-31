# Agentic runs — sonnet-5.5-cc-vs-deepseek-v4-pro · run 20261031T114732Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r4_schema_load_optimize | Claude Sonnet 5.5 (CC) | medium | 1/1 | 0.5 | $0.06 | 3 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r4_schema_load_optimize | 1 | Claude Sonnet 5.5 (CC) | ✅ | 0.5 | $0.06 | 3 | 2 | 1 | index scan on orders, no seq scan, 32.0ms < 1000.0ms |
