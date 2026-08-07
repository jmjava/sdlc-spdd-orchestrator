# SPIKE-084: Registry / claims across three paths

GitHub: [#84](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/84)  
Status: **implemented**

## Decision

| Path | Encoding |
|------|----------|
| Git | Compact `spdd/memory/registry.jsonl` append-only events (claim/release) on every claim/release. Legacy `agent-context/work-registry.tsv` still updated for transition. |
| SQLite | `claims` table fan-out from `TeamRegistry.claim` / `release` |
| Guide | WorkId properties / projection from stay-set; claim hot-path is SQLite-first |

## Conflict rule

Last-write-wins by timestamp within a machine; multi-user sync for v1 still allows TSV. JSONL is the lean committed event log.

Proof: `engine/tests/test_hard_review_gaps.py::test_registry_lean_jsonl_and_sqlite_on_claim`
