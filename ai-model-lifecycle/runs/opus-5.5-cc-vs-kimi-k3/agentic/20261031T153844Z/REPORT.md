# Agentic runs — opus-5.5-cc-vs-kimi-k3 · run 20261031T153844Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r2_gwt_to_angular | Claude Opus 5.5 (CC) | medium | 1/1 | 9.3 | $2.65 | 41 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r2_gwt_to_angular | 1 | Claude Opus 5.5 (CC) | ✅ | 9.3 | $2.65 | 41 | 39 | 18 | Angular port builds and passes all 8 parity tests |
