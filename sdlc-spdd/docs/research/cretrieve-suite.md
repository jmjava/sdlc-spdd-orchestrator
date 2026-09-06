# C-RETRIEVE suite (TEST-003)

**Work ID:** TEST-003-cretrieve-roundtrip  
**Construct:** C-RETRIEVE (DOC-001 §1 academic-review claim)

This is the **named test pack** for “stored advice is retrievable.” It is not
RQ1, not RQ4, and not Guide embeddings.

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
| Guide | when enabled, **mocked** `by-label` HTTP so `context parity` missing is empty on default CI |

Live Guide+Neo4j remains `engine/tests_e2e/test_guide_projection_roundtrip.py` (experimental stack). That is extra. Unreachable Guide is a skip in `parity()`, **not** a C-RETRIEVE pass — this suite therefore mocks the success path.

## What it does not prove

- The hybrid **reduces drift** (RQ1 / TEST-002)
- Retrieved lessons **improve later work** (RQ4 / C-MEMORY)
- Guide **embeddings** / DICE IR (`dice_measured` stays false on FEAT-017)
- `db query --search` (work_items FTS) is the same as `context retrieve`
- `embabel-dif` attach
