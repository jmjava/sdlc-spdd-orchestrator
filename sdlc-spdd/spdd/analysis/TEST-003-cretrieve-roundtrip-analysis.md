# Analysis: TEST-003 — C-RETRIEVE round-trip suite

## Metadata

- Work ID: TEST-003-cretrieve-roundtrip
- Date: 2026-09-06
- Depends on: DOC-001 T03, CHORE-003, FEAT-017

## Scope Lock

### In Scope

DOC-001 §1 claims stored advice is retrievable. Existing tests do not add up to that claim:

- CHORE-003 retrieves *some* pitfall from the dogfood ledger (non-vacuous), not persist→same-id.
- FEAT-017 scores a lexical fixture (`dice_measured: false`), not a persist round-trip.
- SQLite parity unit tests check `ok` after accept; they are not the named research suite.
- Live Guide+Neo4j round-trip **already exists** (`test_guide_projection_roundtrip.py` / `test-guide-stack-experimental`). Default research CI still treated unreachable Guide as skip, so TEST-003 adds a **hermetic mocked** success path. That is a CI split, not a missing live test.

### NOT in Scope

RQ1, RQ4, and embeddings (out of this academic-review bar). Re-implementing live Guide+Neo4j. `embabel-dif` (removed from this review). A new SPIKE.

## Recommendation

One unittest module `tests/research/test_cretrieve.py` plus `sdlc-spdd/docs/research/cretrieve-suite.md`. Mock Guide HTTP in-process so the parity success path is always in default CI. Cite the existing live Guide+Neo4j e2e; do not treat it as leftover work.
