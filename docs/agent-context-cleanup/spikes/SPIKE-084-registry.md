# SPIKE-084: Registry / claims across three paths

GitHub: [#84](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/84)  
Status: **proposal accepted for implementation**

## Decision

| Path | Encoding |
|------|----------|
| Git | Compact `spdd/memory/registry.jsonl` append-only events (claim/release/shelf) + optional mirror of last-known status in SQLite/Guide. Legacy `agent-context/work-registry.tsv` remains readable during upgrade; new writes prefer JSONL + SQLite. |
| SQLite | `claims` table (work_id PK/history rows, owner, status, phase, note, ts) |
| Guide | WorkId properties / projection from stay-set; claim hot-path is SQLite-first |

## Conflict rule

Last-write-wins by timestamp within a machine; multi-user sync for v1 still allows TSV import on upgrade. JSONL is the lean committed event log.
