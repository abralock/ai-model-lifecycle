# Agentic runs — opus-5.5-cc-vs-glm-5.3 · run 20261103T111833Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1_springboot2to3 | GLM-5.3 · opencode | medium | 1/1 | 5.2 | $0.52 | 39 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1_springboot2to3 | 1 | GLM-5.3 · opencode | ✅ | 5.2 | $0.52 | 39 | 65 | 12 | migrated cleanly: compiles, tests pass, no javax, no spring.factories |
