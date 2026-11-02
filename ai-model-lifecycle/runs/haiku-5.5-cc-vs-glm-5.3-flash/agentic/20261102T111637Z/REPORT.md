# Agentic runs — haiku-5.5-cc-vs-glm-5.3-flash · run 20261102T111637Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r4_schema_load_optimize | Claude Haiku 5.5 (CC) | low | 1/1 | 1.7 | $0.02 | 15 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r4_schema_load_optimize | 1 | Claude Haiku 5.5 (CC) | ✅ | 1.7 | $0.02 | 15 | 14 | 1 | index scan on orders, no seq scan, 30.1ms < 1000.0ms |
