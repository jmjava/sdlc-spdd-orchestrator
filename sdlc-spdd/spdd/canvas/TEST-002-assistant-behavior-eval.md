# REASONS Canvas: TEST-002-assistant-behavior-eval — First eval slice

## Metadata

- Work ID: TEST-002-assistant-behavior-eval
- Work Type: Test
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: TEST-001-evaluation-protocol, FEAT-016-intent-code-traceability
- Related: DOC-003-replication-package
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/TEST-002-assistant-behavior-eval.md`
- Analysis: `sdlc-spdd/spdd/analysis/TEST-002-assistant-behavior-eval-analysis.md`
- Beck stage: make it right (C-DRIFT / C-COMPLY slice)

## R - Requirements

### User Goal

Execute one small protocol slice so parity means behavior, not adapter markdown. Record method vs unstructured on a gold task that has source.

### Business / Product Goal

A referee can find n, model, gold paths, and stop-rule status next to any number.

### Acceptance Criteria

- [x] Gold task has source + canvas + expected operations
- [x] A recorded run (logs or review artifacts) for the method vs unstructured baseline
- [x] Limitations of n and model version are written next to any numbers

### Non-Goals

- Full user study
- Statistical significance from n=1
- Claiming C-PORT
- Embabel upstream

## E - Entities

- Frozen gold (hello farewell)
- Unstructured vs method source snapshots
- Slice log
- Symbol-proxy C-DRIFT scorer

### Files likely affected

- `tests/eval/test-002-hello/`
- `tests/research/test_test002_slice.py`

## A - Approach

Copy seed hello into a dated eval fixture. Freeze T01 `farewell`. Record n=1 patches. Score added `def` names against T01. Label protocol incomplete.

## S - Structure

### Files to add

- `tests/eval/test-002-hello/**`
- `tests/research/test_test002_slice.py`

### Test structure

- Gold greet works; farewell missing
- Method farewell passes; no shout
- Unstructured has shout (unmapped)
- Log: n=1, protocol incomplete, C-PORT not reported

## O - Operations

### T01 - Freeze gold, record n=1 slice, score C-DRIFT proxy

- Status: Complete
- Description: Frozen hello gold + unstructured/method snapshots + scorer + slice log with limitations beside numbers.
- Files: `tests/eval/test-002-hello/src/hello.py`, `tests/eval/test-002-hello/canvas/TEST-002-hello.md`, `tests/eval/test-002-hello/runs/method/src/hello.py`, `tests/eval/test-002-hello/runs/unstructured/src/hello.py`, `tests/eval/test-002-hello/score_slice.py`, `tests/eval/test-002-hello/SLICE-LOG.md`, `tests/research/test_test002_slice.py`
- Tests: `python3 -m unittest tests.research.test_test002_slice -v`
- Validation: gold test fails on frozen src; method unmapped=0; unstructured unmapped>0; log says protocol incomplete

## N - Norms

- Cite C-DRIFT / C-COMPLY / C-PORT
- One operation
- Do not invent n≥3

## S - Safeguards

- Do not claim the method works
- Do not report C-PORT
- Do not restore fake Java
- No Embabel upstream
- Symbol proxy ≠ hunk C-DRIFT

## Review Checklist

- [x] Gold completeness
- [x] Recorded runs
- [x] Limitations beside numbers
- [x] Tests fail token-only logs

## Sync Notes

Follows merged FEAT-017 (`2f51d1c` / PR #233). Spring Boot gold remains blocked.

## Final Status

- Readiness: Reviewed
- Status: Complete
