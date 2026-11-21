# Agentic runs — haiku-5.5-cc-vs-glm-5.3-flash · run 20261113T154643Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r7_shogun_hibernate6 | Claude Haiku 5.5 (CC) | medium | 0/1 | 60.0 | $0.00 | 196 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r7_shogun_hibernate6 | 1 | Claude Haiku 5.5 (CC) | ❌ (time limit) | 60.0 | n/a | 196 | 195 | 147 | failed checks: grading_tests |
