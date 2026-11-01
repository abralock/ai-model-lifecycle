# Agentic runs — opus-5.5-cc-vs-glm-5.3 · run 20261101T061953Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r1b_jhipster_boot3 | GLM-5.3 · opencode | medium | 0/1 | 48.8 | $12.26 | 245 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r1b_jhipster_boot3 | 1 | GLM-5.3 · opencode | ❌ | 48.8 | $12.26 | 245 | 276 | 44 | failed checks: build, unit_tests, integration_tests, e2e |
