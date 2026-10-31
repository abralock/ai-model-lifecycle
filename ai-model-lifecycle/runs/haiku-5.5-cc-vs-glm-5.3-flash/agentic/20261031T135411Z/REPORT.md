# Agentic runs — haiku-5.5-cc-vs-glm-5.3-flash · run 20261031T135411Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1b_jhipster_boot3 | Claude Haiku 5.5 (CC) | medium | 1/1 | 28.6 | $1.38 | 131 |
| r2_gwt_to_angular | Claude Haiku 5.5 (CC) | medium | 1/1 | 23.9 | $1.91 | 154 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1b_jhipster_boot3 | 1 | Claude Haiku 5.5 (CC) | ✅ | 28.6 | $1.38 | 131 | 120 | 31 | migrated to Boot 3.1.5: build, 52+ unit, 140+ integration and 54+ Cypress e2e tests pass |
| r2_gwt_to_angular | 1 | Claude Haiku 5.5 (CC) | ✅ | 23.9 | $1.91 | 154 | 151 | 18 | Angular port builds and passes all 8 parity tests |
