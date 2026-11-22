# Agentic runs — opus-5.5-cc-vs-qwen3.8-max · run 20261121T235702Z

The model works on a copy of the project inside a sandbox with an agent (Claude Code for Claude models, opencode for open-weight models): edit, build, test, fix, until its `/goal` is met or the time limit is hit; what it delivered is then scored by the case's acceptance check, including hidden tests it never saw. Infra errors (the session never ran) are left out.

## Summary

| Case | Model | Effort | Passed | Mean time (min) | Mean cost (USD) | Mean turns |
|---|---|---|---:|---:|---:|---:|
| r8_shogun_rust | Qwen3.8 Max · opencode | high | 0/1 | 186.5 | $21.60 | 226 |

## Per attempt

| Case | Rep | Model | Result | Time (min) | Cost (USD) | Turns | Tool calls | Files | Reason |
|---|---:|---|---|---:|---:|---:|---:|---:|---|
| r8_shogun_rust | 1 | Qwen3.8 Max · opencode | ❌ | 186.5 | $21.60 | 226 | 290 | 15 | failed checks: crud, database |
