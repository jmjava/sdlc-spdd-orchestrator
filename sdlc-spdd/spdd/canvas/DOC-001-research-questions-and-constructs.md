# REASONS Canvas: DOC-001-research-questions-and-constructs — RQs and constructs

## Metadata

- Work ID: DOC-001-research-questions-and-constructs
- Work Type: Documentation
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: SPIKE-004-academic-contribution-bar
- Blocks: TEST-001, FEAT-014, FEAT-015
- Related: DOC-002
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/DOC-001-research-questions-and-constructs.md`
- Analysis: `sdlc-spdd/spdd/analysis/DOC-001-research-questions-and-constructs-analysis.md`
- Parent plan: `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- Beck stage: make it right (research argument)

## R - Requirements

### User Goal

Freeze research questions and operationalized constructs so later Milestone 2 work implements **instruments**, not new vibes.

### Business / Product Goal

Make public claims allow-listed. Stop README causal language until evidence exists.

### Acceptance Criteria

- [x] RQs numbered; each names independent and dependent constructs
- [x] Every construct has: definition, measure, instrument, known proxy weakness
- [x] Claims-allowed-today vs after Milestone 2 table is committed
- [x] Rewrite guidance for README/compliance is in the same document (T01); applying README edits is T02

### Non-Goals

- Running the study
- Implementing validators
- Related-work matrix (DOC-002)

### Assumptions

- Five RQs from SPIKE-004 analysis, refined not replaced
- Construct IDs are stable names for FEAT-014–017 canvases to cite

## E - Entities

- Research question (RQ1–RQ5)
- Construct (C-DRIFT, C-COMPLY, C-CONTEXT, C-MEMORY, C-PORT)
- Instrument (current proxy vs target Work ID)
- Claim allow-list row

### Files likely affected

- `sdlc-spdd/docs/research/research-questions-and-constructs.md` (add)
- `docs/research/README.md` (index)
- `README.md` (T02 only)

## A - Approach

Write one canonical markdown spec. Machine proxies must be things this repo already has or P1 will add. Human remainders are explicit so TEST-001 can assign raters.

Do not expand to a sixth RQ. Do not implement FEAT-014 “to make the table look better.”

### Alternatives

- Put RQs only in the SPIKE canvas — rejected; children need a citable spec.
- Wait for DOC-002 — rejected; instruments would stay undefined.

### Risks

- Over-precise formulas that TEST-002 cannot collect
- Under-precise constructs that FEAT-014 can satisfy with more grep

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/research-questions-and-constructs.md`

### Files to modify

- `docs/research/README.md`
- T02: `README.md`, maybe `sdlc-spdd/docs/spdd-compliance.md`

### Test structure

- Document completeness checklist in T01 (all RQ/construct/claim sections present)
- No pytest

## O - Operations

### T01 — Freeze RQ, construct, and claims-allowed spec

- Status: Complete
- Description: Commit `sdlc-spdd/docs/research/research-questions-and-constructs.md` with RQ1–RQ5 (IV/DV), construct table (definition, measure, current instrument, target instrument, proxy weakness), claims-allowed table, README rewrite guidance. Link from `docs/research/README.md`.
- Files: `sdlc-spdd/docs/research/research-questions-and-constructs.md`, `docs/research/README.md`
- Tests: section completeness vs this canvas ACs
- Validation: every construct has four fields; every RQ cites construct IDs

### T02 — Apply public-language hedges

- Status: Complete
- Description: Apply T01 rewrite guidance to README (and compliance if it repeats causal claims). Do not invent new product claims.
- Files: `README.md`, possibly `sdlc-spdd/docs/spdd-compliance.md`
- Tests: grep for “fixes that” should not remain as an unqualified causal claim
- Validation: claims-allowed table still matches README

## N - Norms

- Cite construct IDs (`C-DRIFT`, …) in later canvases
- Prompt-update this canvas if RQs change
- One operation per session

## S - Safeguards

- Do not modify engine code
- Do not add RQ6
- Do not restore “fixes drift” as a result
- No Embabel upstream framing
- T01 must not edit README (that is T02)

## Review Checklist

- [x] T01 document exists
- [x] Five RQs with construct IDs
- [x] Five constructs with four fields each
- [x] Claims table
- [x] Rewrite guidance present
- [x] T02 not mixed into T01

## Sync Notes

Created 2026-09-06 from SPIKE-004 T04 handoff.

## Final Status

- Readiness: Reviewed
- Status: Complete

## Architecture Notes

- Readiness: Reviewed
- T01–T02 documentation only
- Risk: `docs/three-part-operating-path.md` still says “governs execution” (out of T02 file list)
- Next: DOC-002 related-work matrix
