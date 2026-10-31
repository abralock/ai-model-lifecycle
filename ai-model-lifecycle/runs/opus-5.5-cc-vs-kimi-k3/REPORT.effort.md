# Gate 1 effort sweep — opus-5.5-cc-vs-kimi-k3 · sanity suite

> Generated: 2026-10-30T15:02:31+00:00  
> Current: **Claude Opus 5.5 (CC)** (`claude-opus-5-5`) · Target: **Kimi K3** (`kimi-k3`)  
> Live scoring: on  

One row per model × thinking effort. Each level is its own run (`runner.py --effort low,medium,high`); **default** is the main scorecard's run, at the effort `models.yaml` sends. Thinking and answer times are client-observed stream phases (docs/LATENCY.md) and need `thinking_time: true`; `n/a` means the run was not instrumented. Descriptive only: these rows feed no score or verdict.

## Summary

| Model | Effort | Run | Passed | Mean latency (s) | Thinking (s) | Answer (s) | Answer ÷ thinking | Thinking tokens / call | TTFS (s) | Pass@30s | Pass@60s | Pass@120s | Cost / run (USD) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Claude Opus 5.5 (CC) | low | `20261030T142631Z` | 1/1 | 22.83 | 6.86 | 14.70 | 2.14 | 635 | 22.83 | 100.0% | 100.0% | 100.0% | $0.0584 |
| Claude Opus 5.5 (CC) | medium | `20261030T142654Z` | 1/1 | 30.56 | 10.30 | 18.21 | 1.77 | 1,078 | 30.56 | 0.0% | 100.0% | 100.0% | $0.0758 |
| Claude Opus 5.5 (CC) | high | `20261030T142724Z` | 1/1 | 50.90 | 28.69 | 20.03 | 0.70 | 2,966 | 50.90 | 0.0% | 100.0% | 100.0% | $0.1177 |
| Claude Opus 5.5 (CC) | xhigh | `20261030T144107Z` | 1/1 | 132.32 | 109.75 | 21.01 | 0.19 | 12,326 | 132.32 | 0.0% | 0.0% | 0.0% | $0.3090 |
| Claude Opus 5.5 (CC) | default (model default) | `20261030T134516Z` | 12/12 | 39.31 | 12.86 | 24.77 | 1.93 | 1,325 | 39.31 | 8.3% | 100.0% | 100.0% | $0.1083 |
| Kimi K3 | default (model default) | `20261030T134516Z` | 2/2 (+10 infra) | 69.15 | 51.15 | 15.95 | 0.31 | 6,106 | 69.15 | 0.0% | 0.0% | 100.0% | $0.1520 |

> Claude Opus 5.5 (CC) · low: partial run — no r1_springboot2to3, r4_schema_load_optimize, r5_etl_dashboard.
> Claude Opus 5.5 (CC) · medium: partial run — no r1_springboot2to3, r4_schema_load_optimize, r5_etl_dashboard.
> Claude Opus 5.5 (CC) · high: partial run — no r1_springboot2to3, r4_schema_load_optimize, r5_etl_dashboard.
> Claude Opus 5.5 (CC) · xhigh: partial run — no r1_springboot2to3, r4_schema_load_optimize, r5_etl_dashboard.

## Thinking time by task

Mean thinking seconds per call · passes / scored runs.

### Claude Opus 5.5 (CC)

| Task | low | medium | high | xhigh | default |
|---|---:|---:|---:|---:|---:|
| r1_springboot2to3 | — | — | — | — | 7.5 s · 3/3 |
| r3_oracle_to_postgres | 6.9 s · 1/1 | 10.3 s · 1/1 | 28.7 s · 1/1 | 109.7 s · 1/1 | 11.6 s · 3/3 |
| r4_schema_load_optimize | — | — | — | — | 19.5 s · 3/3 |
| r5_etl_dashboard | — | — | — | — | 12.7 s · 3/3 |

### Kimi K3

| Task | default |
|---|---:|
| r1_springboot2to3 | 51.2 s · 2/2 |
| r3_oracle_to_postgres | — |
| r4_schema_load_optimize | — |
| r5_etl_dashboard | — |
