# Agentic runs — opus-5.5-cc-vs-kimi-k3 · run 20261105T121013Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1b_jhipster_boot3 | Claude Opus 5.5 (CC) | low | 1/1 | 10.0 | $0.00 | 27 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1b_jhipster_boot3 | 1 | Claude Opus 5.5 (CC) | ✅ (time limit) | 10.0 | n/a | 27 | 26 | 29 | migrated to Boot 3.0.7: build, 52+ unit, 140+ integration and 54+ Cypress e2e tests pass |
