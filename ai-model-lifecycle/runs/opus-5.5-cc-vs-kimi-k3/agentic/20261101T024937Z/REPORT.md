# Agentic runs — opus-5.5-cc-vs-kimi-k3 · run 20261101T024937Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1b_jhipster_boot3 | Claude Opus 5.5 (CC) | low | 1/1 | 17.8 | $1.71 | 57 |
| r2_gwt_to_angular | Claude Opus 5.5 (CC) | low | 1/1 | 10.6 | $1.60 | 36 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1b_jhipster_boot3 | 1 | Claude Opus 5.5 (CC) | ✅ | 17.8 | $1.71 | 57 | 55 | 31 | migrated to Boot 3.1.5: build, 52+ unit, 140+ integration and 54+ Cypress e2e tests pass |
| r2_gwt_to_angular | 1 | Claude Opus 5.5 (CC) | ✅ | 10.6 | $1.60 | 36 | 27 | 15 | Angular port builds and passes all 8 parity tests |
