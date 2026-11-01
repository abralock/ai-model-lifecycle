# Agentic runs — sonnet-5.5-cc-vs-deepseek-v4-pro · run 20261031T161435Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1b_jhipster_boot3 | Claude Sonnet 5.5 (CC) | high | 1/1 | 27.8 | $1.39 | 76 |
| r2_gwt_to_angular | Claude Sonnet 5.5 (CC) | high | 1/1 | 11.5 | $1.10 | 52 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1b_jhipster_boot3 | 1 | Claude Sonnet 5.5 (CC) | ✅ | 27.8 | $1.39 | 76 | 65 | 31 | migrated to Boot 3.1.5: build, 52+ unit, 140+ integration and 54+ Cypress e2e tests pass |
| r2_gwt_to_angular | 1 | Claude Sonnet 5.5 (CC) | ✅ | 11.5 | $1.10 | 52 | 38 | 17 | Angular port builds and passes all 8 parity tests |
