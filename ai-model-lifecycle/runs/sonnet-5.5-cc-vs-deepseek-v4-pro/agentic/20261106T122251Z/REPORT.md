# Agentic runs — sonnet-5.5-cc-vs-deepseek-v4-pro · run 20261106T122251Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r2_gwt_to_angular | Claude Sonnet 5.5 (CC) | medium | 1/1 | 5.0 | $0.60 | 34 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r2_gwt_to_angular | 1 | Claude Sonnet 5.5 (CC) | ✅ | 5.0 | $0.60 | 34 | 21 | 6 | Angular port builds, passes all 8 parity tests and all 7 UI-vs-API integration tests |
