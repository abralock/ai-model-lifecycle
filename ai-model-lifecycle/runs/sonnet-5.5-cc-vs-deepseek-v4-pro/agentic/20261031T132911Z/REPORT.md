# Agentic runs — sonnet-5.5-cc-vs-deepseek-v4-pro · run 20261031T132911Z

The model works on a copy of the project inside a sandbox with Claude Code (edit, build, test, fix) until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r2_gwt_to_angular | Claude Sonnet 5.5 (CC) | medium | 0/0 (+1 infra) | n/a | n/a | n/a |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r2_gwt_to_angular | 1 | Claude Sonnet 5.5 (CC) | infra error | 4.0 | n/a | n/a | 23 | 10 | agent did not run (exit 143): ent_tool_use_id":null,"session_id":"d037cf58-5f4e-4bf1-b10a-47aaad372948","uuid":"a57be491-60a4-4bbe-919c-e14658201b99","timestamp |
