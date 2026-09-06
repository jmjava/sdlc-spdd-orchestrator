# REASONS Canvas: FEAT-014-semantic-canvas-validation — Semantic canvas validation

## Metadata

- Work ID: FEAT-014-semantic-canvas-validation
- Work Type: Feature
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: DOC-001-research-questions-and-constructs
- Blocks: FEAT-016
- Related: FEAT-015
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/FEAT-014-semantic-canvas-validation.md`
- Analysis: `sdlc-spdd/spdd/analysis/FEAT-014-semantic-canvas-validation-analysis.md`
- Beck stage: make it right (C-COMPLY observability)

## R - Requirements

### User Goal

Make 'valid canvas' and 'Ready For Coding' mean structured, checkable properties — not heading presence or a regex anywhere in the file.

### Business / Product Goal

Raise C-COMPLY above existence-only for the code phase.

### Acceptance Criteria

- [x] gate_check(code) uses canonical readiness, not substring search over the whole file
- [x] validate-reasons-canvas.sh (or engine equivalent) fails canvases that have headings and empty bodies
- [x] Unit tests cover false-Ready (phrase in the wrong section) and empty Operations

### Non-Goals

- LLM-judged canvas quality as a hard gate
- Changing REASONS section names
- FEAT-016 review minima
- REF-001 dual-engine unification

## E - Entities

- Structured readiness token
- Semantic minima (Requirements prose, T## + Status)
- Policy flag `--strict-readiness`

### Files likely affected

- `engine/src/sdlc_engine/canvas.py`
- `engine/src/sdlc_engine/workflow.py`
- `scripts/validate-reasons-canvas.sh`
- `scripts/lib/readiness.sh`

## A - Approach

Python `coding_gate_issues` is the SUT for `gate_check(code)`. Shell validator implements the same minima so CI that does not install the engine still fails headings-only canvases. Readiness is taken only from YAML frontmatter or the Metadata section.

### Alternatives

- Flag-only semantic checks — rejected; AC requires headings-only to fail by default
- Shell-only — rejected; research SUT is Python `gate_check`

### Risks

- Dual implementation (Python vs bash) until REF-001
- Spring Boot example Metadata lacks Readiness (Architecture Notes only)

## S - Structure

### Files to add

- This canvas, analysis, review

### Files to modify

- Engine canvas + workflow
- Shell validator + readiness extractor
- Unit and smoke tests
- DOC-001 C-COMPLY instrument-today row (path sync)

### Test structure

- `test_canvas.py` false-Ready / headings-only / Architecture Notes
- `test_workflow_gates.py` code gate
- `tests/test-canvas-readiness.sh` headings-only fail + `--strict-readiness`

## O - Operations

### T01 - Semantic minima and structured readiness gate

- Status: Complete
- Description: Implement coding-gate issues in `canvas.py`, wire `gate_check(code)`, fail headings-only in `validate-reasons-canvas.sh`, Metadata-only readiness extraction, strict-readiness flag, unit tests.
- Files: `engine/src/sdlc_engine/canvas.py`, `engine/src/sdlc_engine/workflow.py`, `scripts/validate-reasons-canvas.sh`, `scripts/lib/readiness.sh`, tests
- Tests: pytest unit + `./tests/test-canvas-readiness.sh`
- Validation: false-Ready fails; empty Operations fail; headings-only fails; semantic canvas with Metadata Readiness passes

## N - Norms

- Cite C-COMPLY
- One operation
- Do not start FEAT-016 in this PR

## S - Safeguards

- Do not change REASONS section names
- No Embabel upstream
- Do not weaken tests to substring search
- Do not claim empty review is now C-COMPLY (that is FEAT-016)

## Review Checklist

- [x] gate_check no longer uses whole-file regex
- [x] Headings-only fails validator
- [x] False-Ready tests exist and fail the gate
- [x] Empty Operations fail the gate
- [x] Engine unit tests green

## Sync Notes

P0 (DOC-001/002, TEST-001) merged. This is Milestone 2 P1 item 1.

## Final Status

- Readiness: Reviewed
- Status: Complete
