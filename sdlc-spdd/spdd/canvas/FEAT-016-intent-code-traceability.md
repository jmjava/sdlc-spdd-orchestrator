# REASONS Canvas: FEAT-016-intent-code-traceability — Review minima and mapping

## Metadata

- Work ID: FEAT-016-intent-code-traceability
- Work Type: Feature
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: FEAT-014-semantic-canvas-validation
- Blocks: TEST-002
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/FEAT-016-intent-code-traceability.md`
- Analysis: `sdlc-spdd/spdd/analysis/FEAT-016-intent-code-traceability-analysis.md`
- Beck stage: make it right (C-COMPLY / C-DRIFT)

## R - Requirements

### User Goal

Close the gap where GATE_LABELS list code_maps_to_ops, tests_updated, and safeguards_checked but gate_check does not enforce them, and sync() auto-passes safeguards when a review file exists.

### Business / Product Goal

Empty reviews must not count as C-COMPLY. Advertised gates must be enforced or labeled advisory.

### Acceptance Criteria

- [x] An empty review file does not pass safeguards_checked
- [x] Documented rule for code_maps_to_ops with at least one automated check and one documented remainder for humans
- [x] phases.py and workflow.gate_check no longer advertise unenforced gates without labeling them advisory

### Non-Goals

- Full static analysis of acceptance criteria
- Replacing human review
- FEAT-015 metrics

## E - Entities

- Review minima (Result, safeguards)
- Operation Files: mapping
- Advisory vs enforced gate

### Files likely affected

- `engine/src/sdlc_engine/canvas.py`
- `engine/src/sdlc_engine/workflow.py`
- `engine/src/sdlc_engine/phases.py`
- `sdlc-spdd/docs/research/code-maps-to-ops.md`

## A - Approach

Review minima on retro/sync. Files: mapping on code. Advisory suffix on remaining GATE_LABELS. Document hunk mapping as the human remainder.

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/code-maps-to-ops.md`

### Files to modify

- Engine canvas, workflow, phases, tests

### Test structure

- Empty review fails retro and does not pass safeguards on sync
- Missing Files: fails mapping
- Advisory labels cover exactly ADVISORY_GATES

## O - Operations

### T01 - Review minima, Files mapping, advisory labels

- Status: Complete
- Description: Implement review_minima_issues, operation_mapping_issues, wire retro/sync/code gates, label advisory gates, document remainder.
- Files: `engine/src/sdlc_engine/canvas.py`, `engine/src/sdlc_engine/workflow.py`, `engine/src/sdlc_engine/phases.py`, `sdlc-spdd/docs/research/code-maps-to-ops.md`
- Tests: `engine/tests_unit/test_workflow_gates.py`, `engine/tests_unit/test_canvas.py`
- Validation: empty review ≠ safeguards passed; Files: required; advisory set equals unlabeled unenforced gates

## N - Norms

- Cite C-COMPLY and C-DRIFT
- One operation
- Do not start FEAT-015 in this PR

## S - Safeguards

- Do not claim hunk-level C-DRIFT is automated
- No Embabel upstream
- Do not weaken empty-review tests

## Review Checklist

- [x] Empty review fails
- [x] Mapping rule documented
- [x] Advisory labels present
- [x] Unit tests added

## Sync Notes

Follows merged FEAT-014 (`64d09a1`).

## Final Status

- Readiness: Reviewed
- Status: Complete
