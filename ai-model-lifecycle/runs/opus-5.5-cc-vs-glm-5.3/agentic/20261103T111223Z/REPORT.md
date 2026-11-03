# Agentic runs — opus-5.5-cc-vs-glm-5.3 · run 20261103T111223Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | GLM-5.3 · opencode | medium | 0/0 (+1 infra) | n/a | n/a | n/a |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | GLM-5.3 · opencode | infra error | 3.1 | $0.21 | 31 | 47 | 11 | opencode error: provider.invalid-output: OpenAI Chat stream ended without finish_reason (status 200) |
