# C-RETRIEVE suite (TEST-003)

**Work ID:** TEST-003-cretrieve-roundtrip  
**Construct:** C-RETRIEVE (DOC-001 §1 academic-review claim)

This is the **named hermetic test pack** for “stored advice is retrievable” on
default CI. Live Guide+Neo4j round-trips already exist (see below). RQ1, RQ4,
and Guide embeddings are **out of scope** for this academic-review bar.
`embabel-dif` was **removed** from this review (later / other-repo).

## Command

```bash
PYTHONPATH=engine/src python3 -m unittest tests.research.test_cretrieve -v
```

Research CI (`test-research-p0.yml`) runs the same module.

## What it proves

| Store | Round-trip |
|-------|------------|
| Git ledger | persist/accept → `context retrieve` / `context show` returns the same id |
| SQLite | when enabled, `context parity` has empty missing/extra; retrieve `sqlite_graph` includes the id |
| Guide (hermetic) | **mocked** `by-label` HTTP so `context parity` missing is empty on default CI |
| Guide (live) | already exists: `engine/tests_e2e/test_guide_projection_roundtrip.py` + `test_context_store_guide_live.py` via `tests/test-guide-stack-live.sh` / `test-guide-stack-experimental.yml` |

TEST-003 mocks Guide so research P0 does not need a JVM+Neo4j stack. That is a CI split, **not** a missing live test. Unreachable Guide is a skip in `parity()`, **not** a C-RETRIEVE pass — the mocked path is what default CI uses.

## Out of this academic-review bar

- RQ1 drift (TEST-002 remains instrumentation, not this review’s pass bar)
- RQ4 usefulness / C-MEMORY follow-on rework
- Guide **embeddings** / DICE IR (`dice_measured` stays false on FEAT-017)
- `db query --search` (work_items FTS) is the same as `context retrieve`
