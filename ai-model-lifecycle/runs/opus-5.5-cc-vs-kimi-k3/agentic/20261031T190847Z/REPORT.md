# Agentic runs — opus-5.5-cc-vs-kimi-k3 · run 20261031T190847Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1b_jhipster_boot3 | Claude Opus 5.5 (CC) | high | 1/1 | 31.3 | $5.23 | 98 |
| r2_gwt_to_angular | Claude Opus 5.5 (CC) | high | 1/1 | 35.4 | $7.83 | 124 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1b_jhipster_boot3 | 1 | Claude Opus 5.5 (CC) | ✅ | 31.3 | $5.23 | 98 | 86 | 34 | migrated to Boot 3.1.5: build, 52+ unit, 140+ integration and 54+ Cypress e2e tests pass |
| r2_gwt_to_angular | 1 | Claude Opus 5.5 (CC) | ✅ | 35.4 | $7.83 | 124 | 111 | 18 | Angular port builds and passes all 8 parity tests |
