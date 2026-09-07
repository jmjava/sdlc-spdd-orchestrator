# REASONS Canvas: TEST-003-cretrieve-roundtrip — C-RETRIEVE suite

## Metadata

- Work ID: TEST-003-cretrieve-roundtrip
- Work Type: Test
- Status: In Progress
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-07
- Milestone: milestone-2
- Depends on: DOC-001-research-questions-and-constructs, CHORE-003-dogfood-ledger, FEAT-017-retrieval-ir-eval
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/TEST-003-cretrieve-roundtrip.md`
- Analysis: `sdlc-spdd/spdd/analysis/TEST-003-cretrieve-roundtrip-analysis.md`
- Beck stage: make it right (C-RETRIEVE / academic-review claim)

## R - Requirements

### User Goal

Give the frozen academic-review claim one complete, CI-backed test suite.

### Business / Product Goal

A referee can see **three storage modes** persist→read: ledger and SQLite on the hermetic suite, live Guide/Neo4j on the graph stack. Mocked Guide is the client contract, not the graph.

### Acceptance Criteria

- [x] Named suite `tests.research.test_cretrieve` covers persist→retrieve same id on ledger, SQLite parity, mocked Guide **client**
- [x] Research P0 workflow runs the hermetic suite
- [x] Research note documents out-of-bar items (RQ1, RQ4, embeddings)
- [x] T02: live Guide+Neo4j is **required evidence** for the graph mode; `test_context_store_guide_live` asserts all three backends

### Non-Goals

- RQ1 / TEST-002 remainder (this review's **scope removed** drift)
- RQ4 usefulness (this review's **scope removed** usefulness)
- Re-implementing live Guide+Neo4j (already exists)
- Engine behavior change except tests/docs
- Embabel upstream
- `embabel-dif` (removed from this review)

### Assumptions

- C-RETRIEVE is engineering retrievability, not method efficacy
- Guide success path in default CI is mocked **client**; live Guide+Neo4j is the graph-mode proof (`test-guide-stack-experimental`)

## E - Entities

- Lesson record id
- Ledger retrieve hit
- SQLite accepted id set
- Guide work_subgraph id set (mocked client; live graph uses the same retrieve API)
- Non-claim

### Files likely affected

- `tests/research/test_cretrieve.py` (add)
- `sdlc-spdd/docs/research/cretrieve-suite.md` (add)
- `.github/workflows/test-research-p0.yml`
- `sdlc-spdd/docs/research/research-questions-and-constructs.md`
- `docs/research/README.md`

## A - Approach

Temp project, persist/accept one pitfall, assert the same id is readable. Enable sqlite in that project. Mock Guide ``work_subgraph`` so parity ``missing`` is empty. Do not call a real JVM.

### Alternatives

- Only cite existing scattered tests — rejected; that is why the claim looks untested.
- Treat mocked Guide HTTP as the graph store — rejected (DOC-001 T05). Live stack remains `test-guide-stack-experimental`; hermetic research P0 stays Python 3.

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

### T02 — Live graph is required evidence (three modes)

- Status: Complete
- Description: Align TEST-003 with DOC-001 T05. Hermetic suite stays ledger+SQLite+mocked client. Live `test_context_store_guide_live` must assert git + sqlite + Guide ok and parity/subgraph contains the id. `test-guide-stack-experimental` is the graph-mode CI job, not an optional extra.
- Files: `engine/tests_e2e/test_context_store_guide_live.py`, `sdlc-spdd/docs/research/cretrieve-suite.md`, `prove-academic-review.sh`, `.github/workflows/test-guide-stack-experimental.yml`
- Tests: hermetic unittest; live stack on CI when e2e/research paths change
- Validation: suite doc says mocked is not the graph; live test asserts `result.guide` ok

### T03 — Ledger-derived Guide v2 ingest (no test-only index)

- Status: Complete
- Description: `project_to_guide` rebuilds `context-index.md` from accepted ledger records. Live C-RETRIEVE requires the subgraph id, not a skip and not a hand-written table in the test.
- Files: `engine/src/sdlc_engine/context_store.py`, `engine/tests_e2e/test_context_store_guide_live.py`, `engine/tests_e2e/test_guide_projection_roundtrip.py`, `engine/tests_unit/test_context_store_guide_parity.py`
- Tests: unit ingest-id reconstruction; live stack on CI
- Validation: live `work_subgraph` returns the ledger id; skip/unreachable is not a pass

### T04 — Context-select (right data given retrieve context)

- Status: Complete
- Description: Four-record fixture (two Work IDs, three areas, three kinds). Ledger/SQLite retrieve and live `work_subgraph` / `area_lessons` must return the matching subset and exclude sibling records. Query inside a work must not leak the other work. Staged records stay out of accepted retrieve; last-wins overwrites the body.
- Files: `tests/research/test_cretrieve.py`, `tests/research/cretrieve_context_select.py`, `engine/tests_e2e/test_context_store_guide_live.py`, `sdlc-spdd/docs/research/cretrieve-suite.md`, DOC-001 C-RETRIEVE row
- Tests: `PYTHONPATH=engine/src python3 -m unittest tests.research.test_cretrieve -v`; live `test_live_context_selects_right_records`
- Validation: exact id-set equality on hermetic; live work subgraph has no sibling-work ids; area lessons have no other-area ids. Not RQ4 usefulness.

### T05 — Unreachable Guide fails parity (not a skip-pass)

- Status: In Progress
- Description: When `guide-dice` is enabled, Guide down sets `parity.guide.ok=false` and overall `ok=false` (CLI exit 1). Live stack script and experimental CI fail if Embabel/Guide cannot boot. Slash commands still must not block the lifecycle when Guide is absent.
- Files: `engine/src/sdlc_engine/context_store.py`, `tests/test-guide-stack-live.sh`, `.github/workflows/test-guide-stack-experimental.yml`, TEST-003 tests/docs
- Tests: `test_parity_fails_when_guide_unreachable`, `test_cli_parity_exits_nonzero_when_guide_unreachable`, `test_unreachable_guide_fails_parity`
- Validation: no `ok: true` + `skipped`/`unreachable` pair; CI does not exit 0 on Embabel down

## N - Norms

- Cite C-RETRIEVE
- One operation
- Do not invent a SPIKE

## S - Safeguards

- Do not modify engine runtime except via tests, except the Guide ingest
  adapter required for ledger→graph persist (`write_guide_ingest_index`)
- Do not claim drift is fixed
- Do not treat mocked Guide as embedding IR
- No Embabel upstream
- Live Guide e2e is the graph-mode proof; hermetic TEST-003 is not a substitute
- `embabel-dif` is out of this review
- Do not hand-write `context-index.md` in a live test and call that retrieve

## Review Checklist

- [x] Suite exists and is in CI
- [x] Three stores covered
- [x] Non-claims documented
- [x] Engine change is the ledger→Guide v2 ingest adapter (not a test-only table)
- [x] T04 context-select: retrieve returns the matching subset, not sibling records
- [ ] T05 unreachable Guide fails parity (not skip-pass)

## Sync Notes

Opened after DOC-001 T03 freeze (`5e0feea` / #244). Stakeholder: claims need a complete test suite. Live Guide+Neo4j e2e already exists; do not list it as leftover. `embabel-dif` is out of this review.

2026-09-07 — T02 / DOC-001 T05: live graph is required evidence for mode 3; hermetic suite is not a substitute.

2026-09-07 — T03: Guide v2 does not read `lessons.jsonl`; persist→load now derives the ingest table from the ledger so the graph stores the same id.

2026-09-07 — T04: non-trivial C-RETRIEVE is context-select (work/area/kind/query), not another single-id write.

2026-09-07 — T05: guide-dice enabled + Guide down fails `context parity`; live CI fails if Embabel cannot boot.

## Final Status

- Readiness: Reviewed
- Status: Complete
