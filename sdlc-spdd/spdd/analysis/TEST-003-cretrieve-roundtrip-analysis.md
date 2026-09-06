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
- Guide round-trip is live e2e only (`test-guide-stack-experimental`); default CI never proves Guide retrievability. Unreachable Guide is treated as skip, not as a pass of the claim.

### NOT in Scope

RQ1, RQ4, embeddings, live Guide stack, DIF, a new SPIKE.

## Recommendation

One unittest module `tests/research/test_cretrieve.py` plus `sdlc-spdd/docs/research/cretrieve-suite.md`. Mock Guide HTTP in-process so the parity success path is always in CI. Keep live Guide e2e as extra, not as the paper-claim gate.
