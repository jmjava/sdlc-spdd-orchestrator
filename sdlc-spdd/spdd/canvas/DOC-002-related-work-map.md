# REASONS Canvas: DOC-002-related-work-map — Related-work and novelty matrix

## Metadata

- Work ID: DOC-002-related-work-map
- Work Type: Documentation
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: SPIKE-004-academic-contribution-bar, DOC-001-research-questions-and-constructs
- Blocks: TEST-001
- Related: DOC-001
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/DOC-002-related-work-map.md`
- Analysis: `sdlc-spdd/spdd/analysis/DOC-002-related-work-map-analysis.md`
- Parent plan: `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- Beck stage: make it right (research argument)

## R - Requirements

### User Goal

Position SDLC-SPDD against parent methods and 2024–2026 AI-SE tooling so a referee can see the delta in one matrix.

### Business / Product Goal

Make the novelty sentence rebuttal-ready and consistent with DOC-001. Stop “we implemented Fowler+SDLC Agents” from being the whole related-work story.

### Acceptance Criteria

- [x] Committed related-work matrix with claim × system × delta
- [x] Novelty sentence is consistent with DOC-001 RQs
- [x] Guide remains fork-only; no Embabel-upstream framing

### Non-Goals

- A complete literature review of all AI coding papers
- Citing Embabel/Guide as an upstream PR
- Expanding product surface (ADF, Vue3, Jira UX)
- Collecting evaluation data (TEST-001/002)

### Assumptions

- DOC-001 construct IDs are the matrix columns
- OpenSPDD is the CLI that implements Fowler SPDD, not a third independent method family
- “With evidence that…” is **not** this review’s aim (DOC-001 T03). `embabel-dif` is later / other-repo.

## E - Entities

- Comparator system (row)
- Construct column (C-DRIFT, C-COMPLY, C-CONTEXT)
- Novelty sentence
- Not-claiming item

### Files likely affected

- `sdlc-spdd/docs/research/related-work-and-novelty.md` (add)
- `docs/research/README.md` (index)
- `sdlc-spdd/docs/research/check_p0_artifacts.py` (checker)
- `tests/research/` (tests + fixtures)

## A - Approach

Write one canonical markdown matrix. Columns are DOC-001 constructs. Deltas state object-difference, not superiority.

Ship a structured checker with negative fixtures so a document that only greps for “Fowler” / “Spec Kit” fails.

Do not start TEST-001 in this operation. Do not modify engine code.

### Alternatives

- Cite parents only in README — rejected; that is the M2 failure mode.
- Full annotated bibliography — rejected; out of scope.
- Claim evidence in the novelty sentence — rejected; contradicts DOC-001 freeze.

### Risks

- Collapsing Fowler SPDD and OpenSPDD into one row and missing the required OpenSPDD comparator
- Accidental causal-finding language
- Checker weakened to token grep

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/related-work-and-novelty.md`
- `sdlc-spdd/docs/research/check_p0_artifacts.py`
- `tests/research/test_p0_artifacts.py`
- `tests/research/fixtures/*.md`
- `.github/workflows/test-research-p0.yml`

### Files to modify

- `docs/research/README.md`
- `sdlc-spdd/docs/research/prove-p0.sh`

### Test structure

- Negative fixtures: token stub, missing row, missing columns, Embabel upstream, evidence-as-finding
- Positive fixture and live DOC-002 files must parse as a real matrix
- CI workflow runs the unittest module on every PR

## O - Operations

### T01 — Commit related-work matrix, novelty sentence, and structured tests

- Status: Complete
- Description: Write `related-work-and-novelty.md` with Claim × system matrix (required comparators), novelty sentence aligned with DOC-001, not-claiming section, fork-only note. Add parser-based checker, negative fixtures, and CI so token stubs fail.
- Files: `sdlc-spdd/docs/research/related-work-and-novelty.md`, `sdlc-spdd/docs/research/check_p0_artifacts.py`, `tests/research/**`, `.github/workflows/test-research-p0.yml`, `docs/research/README.md`, `sdlc-spdd/docs/research/prove-p0.sh`
- Tests: `python3 -m unittest tests.research.test_p0_artifacts -v` and `prove-p0.sh DOC-002`
- Validation: every required comparator is a matrix row; novelty has repository-native + observable constructs; no Embabel upstream framing

## N - Norms

- Cite construct IDs from DOC-001
- One operation per session
- Do not start TEST-001 until this Work ID’s tests pass

## S - Safeguards

- Do not modify engine code
- Do not claim drift is already fixed
- No Embabel upstream framing
- Do not weaken tests to token grep

## Review Checklist

- [x] Matrix has required comparators as rows
- [x] Columns include C-DRIFT, C-COMPLY, C-CONTEXT, evidence, delta
- [x] Novelty sentence does not contradict DOC-001
- [x] Not-claiming includes LLM, RAG, multi-agent
- [x] Guide fork-only
- [x] Negative fixture tests exist and fail token stubs

## Sync Notes

Created 2026-09-06 after DOC-001 merge (`1d1c866`). Structured tests replace grep-only `prove-p0.sh` token checks.

2026-09-06 — Novelty/not-claiming synced to DOC-001 T03: stores observability is the claim; reduced-drift evidence and `embabel-dif` are not this review.

## Final Status

- Readiness: Reviewed
- Status: Complete
