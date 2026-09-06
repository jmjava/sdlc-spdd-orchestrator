# REASONS Canvas: FEAT-017-retrieval-ir-eval — Lexical retrieve as IR

## Metadata

- Work ID: FEAT-017-retrieval-ir-eval
- Work Type: Feature
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: DOC-001-research-questions-and-constructs
- Related: FEAT-015-first-class-metrics
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/FEAT-017-retrieval-ir-eval.md`
- Analysis: `sdlc-spdd/spdd/analysis/FEAT-017-retrieval-ir-eval-analysis.md`
- Beck stage: make it right (C-CONTEXT relevance proxy)

## R - Requirements

### User Goal

Replace “retrieve = exact keyword filter” as the scientific story. Evaluate lexical retrieval as IR, or stop claiming DICE/hybrid retrieval as a contribution.

### Business / Product Goal

C-CONTEXT relevance has a measured lexical baseline. DICE stays a non-claim until embeddings are measured.

### Acceptance Criteria

- [x] Written algorithm for context retrieve (what matches, sort key, limits)
- [x] At least one eval fixture where exact keyword-list miss is a ranked title/body hit
- [x] Contribution language for DICE is conditional on measured gain or marked non-claim

### Non-Goals

- Requiring Neo4j
- Claiming Guide embeddings
- TEST-002
- Embabel upstream

## E - Entities

- keyword-list algorithm
- title-body ranking
- qrel fixture
- precision@k / recall@k

### Files likely affected

- `engine/src/sdlc_engine/retrieve.py`
- `engine/src/sdlc_engine/context_store.py`
- `sdlc-spdd/docs/research/retrieve-algorithm.md`

## A - Approach

Document both algorithms. Add `--query` / `--rank title-body`. Commit a qrel fixture plus `context eval-retrieve`. Do not set `dice_measured` true.

## S - Structure

### Files to add

- `engine/src/sdlc_engine/retrieve.py`
- `engine/tests_unit/test_retrieve_ir.py`
- `tests/research/fixtures/retrieve_ir_qrels.json`
- `sdlc-spdd/docs/research/retrieve-algorithm.md`

### Files to modify

- context_store retrieve, CLI, DOC-001 DICE claim cell

### Test structure

- Keyword-list precision@1 = 0 on the fixture
- Title-body precision@1 = 1 and rank-1 id is the qrel
- `dice_measured` is false

## O - Operations

### T01 - Lexical retrieve algorithm, qrel fixture, DICE non-claim

- Status: Complete
- Description: Implement title-body ranking, eval-retrieve CLI, qrel fixture proving keyword-list miss vs title-body hit, write the algorithm, mark DICE unmeasured.
- Files: `engine/src/sdlc_engine/retrieve.py`, `engine/src/sdlc_engine/context_store.py`, `engine/src/sdlc_engine/cli_parser.py`, `engine/src/sdlc_engine/cli_commands.py`, `sdlc-spdd/docs/research/retrieve-algorithm.md`, `tests/research/fixtures/retrieve_ir_qrels.json`
- Tests: `engine/tests_unit/test_retrieve_ir.py`
- Validation: keyword-list miss / title-body hit; DICE not claimed

## N - Norms

- Cite C-CONTEXT
- One operation
- Do not start TEST-002 in this PR

## S - Safeguards

- Do not claim DICE/Guide embeddings as measured
- No Embabel upstream
- Do not require Neo4j for the eval
- Keep `--keyword` behavior for existing callers

## Review Checklist

- [x] Algorithm documented
- [x] Fixture shows keyword-list miss / title-body hit
- [x] DICE non-claim
- [x] Unit tests

## Sync Notes

Follows merged DOC-003 (`6f51680` / PR #232).

## Final Status

- Readiness: Reviewed
- Status: Complete
