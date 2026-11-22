# Agentic runs — haiku-5.5-cc-vs-glm-5.3-flash · run 20261122T035114Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r8_shogun_rust | Claude Haiku 5.5 (CC) | high | 0/2 | 71.2 | $11.53 | 342 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r8_shogun_rust | 1 | Claude Haiku 5.5 (CC) | ❌ | 42.0 | $10.70 | 385 | 383 | 12 | failed checks: crud, queries, database |
| r8_shogun_rust | 2 | Claude Haiku 5.5 (CC) | ❌ | 100.4 | $12.36 | 298 | 265 | 16 | failed checks: own_tests, crud, permissions, database |
