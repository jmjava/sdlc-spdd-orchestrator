# REASONS Canvas: TEST-003-cretrieve-roundtrip — C-RETRIEVE suite

## Metadata

- Work ID: TEST-003-cretrieve-roundtrip
- Work Type: Test
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: DOC-001-research-questions-and-constructs, CHORE-003-dogfood-ledger, FEAT-017-retrieval-ir-eval
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/TEST-003-cretrieve-roundtrip.md`
- Analysis: `sdlc-spdd/spdd/analysis/TEST-003-cretrieve-roundtrip-analysis.md`
- Beck stage: make it right (C-RETRIEVE / academic-review claim)

## R - Requirements

### User Goal

Give the frozen academic-review claim one complete, CI-backed test suite.

### Business / Product Goal

A referee can run one command and see ledger, SQLite, and Guide (mocked) round-trips, plus an explicit non-claim list.

### Acceptance Criteria

- [x] Named suite `tests.research.test_cretrieve` covers persist→retrieve same id on ledger, SQLite parity, mocked Guide parity
- [x] Research P0 workflow runs the suite
- [x] Research note documents out-of-bar items (RQ1, RQ4, embeddings) and cites existing live Guide+Neo4j e2e

### Non-Goals

- RQ1 / TEST-002 remainder (out of this review bar)
- RQ4 usefulness (out of this review bar)
- Re-implementing live Guide+Neo4j (already exists)
- Engine behavior change except tests/docs
- Embabel upstream
- `embabel-dif` (removed from this review)

### Assumptions

- C-RETRIEVE is engineering retrievability, not method efficacy
- Guide success path in default CI is mocked; live Guide+Neo4j e2e already exists on the experimental stack

## E - Entities

- Lesson record id
- Ledger retrieve hit
- SQLite accepted id set
- Guide by-label id set (mocked)
- Non-claim

### Files likely affected

- `tests/research/test_cretrieve.py` (add)
- `sdlc-spdd/docs/research/cretrieve-suite.md` (add)
- `.github/workflows/test-research-p0.yml`
- `sdlc-spdd/docs/research/research-questions-and-constructs.md`
- `docs/research/README.md`

## A - Approach

Temp project, persist/accept one pitfall, assert the same id is readable. Enable sqlite in that project. Mock `urlopen` for Guide `by-label` so parity `missing` is empty. Do not call a real JVM.

### Alternatives

- Only cite existing scattered tests — rejected; that is why the claim looks untested.
- Require live Guide in default research CI — rejected; that stack already has `test-guide-stack-experimental`. Replication of the hermetic suite must not require Neo4j.

### Risks

- Treating unreachable-Guide skip as a pass of C-RETRIEVE
- Letting `db query --search` (work_items FTS) stand in for lesson retrieve

## S - Structure

### Files to add

- `tests/research/test_cretrieve.py`
- `sdlc-spdd/docs/research/cretrieve-suite.md`

### Files to modify

- `.github/workflows/test-research-p0.yml`
- DOC-001 C-RETRIEVE instrument row
- `docs/research/README.md`
- CHANGELOG, MILESTONE-2

### Test structure

- unittest (same runner as CHORE-003 / research P0)
- Fail if stored id is absent from ledger retrieve, sqlite accepted ids, or mocked Guide parity

## O - Operations

### T01 — C-RETRIEVE suite and CI gate

- Status: Complete
- Description: Add `test_cretrieve.py` (ledger + SQLite + mocked Guide round-trips), research note, wire `test-research-p0.yml`, point DOC-001 C-RETRIEVE at this suite.
- Files: `tests/research/test_cretrieve.py`, `sdlc-spdd/docs/research/cretrieve-suite.md`, `.github/workflows/test-research-p0.yml`, DOC-001 spec, README, CHANGELOG
- Tests: `PYTHONPATH=engine/src python3 -m unittest tests.research.test_cretrieve -v`
- Validation: missing stored id fails; suite doc forbids RQ1/RQ4/embeddings as results

## N - Norms

- Cite C-RETRIEVE
- One operation
- Do not invent a SPIKE

## S - Safeguards

- Do not modify engine runtime except via tests
- Do not claim drift is fixed
- Do not treat mocked Guide as embedding IR
- No Embabel upstream
- Live Guide e2e already exists; this gate is the hermetic path
- `embabel-dif` is out of this review

## Review Checklist

- [x] Suite exists and is in CI
- [x] Three stores covered
- [x] Non-claims documented
- [x] No engine product change

## Sync Notes

Opened after DOC-001 T03 freeze (`5e0feea` / #244). Stakeholder: claims need a complete test suite. Live Guide+Neo4j e2e already exists; do not list it as leftover. `embabel-dif` is out of this review.

## Final Status

- Readiness: Reviewed
- Status: Complete
