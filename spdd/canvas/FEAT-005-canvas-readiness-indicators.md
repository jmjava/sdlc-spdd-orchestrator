# REASONS Canvas: FEAT-005-canvas-readiness-indicators - Canvas readiness + leading indicators

## Metadata

- Work ID: FEAT-005-canvas-readiness-indicators
- Work Type: Feature
- Status: Draft
- Readiness: Needs Analysis
- Created: 2026-06-19
- Updated: 2026-06-19
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Bash + Markdown
- Source System: Roadmap
- Roadmap: ROADMAP.md
- Milestone: milestone-1.md
- Delivery stage: make it fast (measurement for optimization) — **deferred, do last**
- Related PR:

## R - Requirements

### User Goal

Read canvas readiness programmatically and know how many cycles it took to get
ready, so prompt quality can be measured over time.

### Business / Product Goal

Provide structured leading indicators that feed the prompt-optimization ledger
(FEAT-004) and any later optimization. Sequenced last, after the make-it-right
refactors (FEAT-001→003) and with/after FEAT-004.

### Acceptance Criteria

- [ ] Canvases carry a machine-parseable `readiness:` value from a fixed vocabulary.
- [ ] `validate-reasons-canvas.sh` reads and validates `readiness:`.
- [ ] Validate/review cycle counts are captured as leading indicators, reusing the FEAT-004 metric Kind in `context-index.md`.
- [ ] Canvases without the field still validate (backward compatible).
- [ ] Docs describe the readiness vocabulary and indicators.

### Non-Goals

- No scoring, ranking, or acting on indicators (later make-it-fast work).

### Assumptions

- FEAT-004 metric Kind exists (or is co-delivered) as the indicator substrate.
- Markdown-first; reuse existing validation + index machinery.

### Open Questions

- Readiness vocabulary (e.g. `draft | needs-analysis | needs-clarification | ready-for-coding`) — finalize in analysis.
- Whether counts are derived from existing logs or captured at validate/review time.

## E - Entities

### Application Components

- `scripts/validate-reasons-canvas.sh` (reads/validates `readiness:`)
- `scripts/capture-session-memory.sh` (indicator capture; ties to FEAT-004 `--readiness`)
- Canvas front matter convention

### Files Likely Affected

- `scripts/validate-reasons-canvas.sh`
- `scripts/capture-session-memory.sh`
- `docs/` (readiness vocabulary)
- canvas template(s)

## A - Approach

### Proposed Approach

1. Define the readiness vocabulary and front-matter placement.
2. Teach `validate-reasons-canvas.sh` to read/validate it (optional → no break for older canvases).
3. Capture validate/review counts as `metric` rows (reusing FEAT-004's Kind).
4. Document the vocabulary and indicators.

### Alternatives Considered

- Keep readiness as prose (rejected: not measurable).

### Trade-Offs

- Adds a front-matter field, but enables structured measurement.

### Risks

- Coupling to FEAT-004 → treat FEAT-004 as a dependency; do not start before it.

### Failure Modes

- Missing/unknown readiness value warns, never blocks validation of older canvases.

## S - Structure

### Files To Add

- None expected (extends existing files + docs).

### Files To Modify

- `scripts/validate-reasons-canvas.sh`, `scripts/capture-session-memory.sh`, docs, canvas template.

### Test Structure

- Validation tests for readiness parsing + indicator capture.

## O - Operations

### T01 - Define readiness vocabulary + placement

- Status: Not Started
- Description: Finalize the fixed readiness values and front-matter location.
- Files: spdd/analysis/FEAT-005-canvas-readiness-indicators-analysis.md, docs
- Tests: Not applicable
- Validation: Analysis review

### T02 - Validate readiness in validate-reasons-canvas.sh

- Status: Not Started
- Description: Parse/validate `readiness:`; optional for backward compatibility.
- Files: scripts/validate-reasons-canvas.sh
- Tests: validation smoke (with/without field)
- Validation: old canvases still pass

### T03 - Capture leading indicators

- Status: Not Started
- Description: Record validate/review counts as `metric` rows (FEAT-004 Kind).
- Files: scripts/capture-session-memory.sh
- Tests: capture smoke
- Validation: indicators indexed, scoped by area

### T04 - Document vocabulary + indicators

- Status: Not Started
- Description: Document readiness values and indicator meaning.
- Files: docs/*
- Tests: Not applicable
- Validation: doc consistency

## N - Norms

### General

- Backward compatible: older canvases without `readiness:` still validate.
- Update this canvas before behavior changes.
- Markdown-first; no new datastore.

### Testing

- Validation + capture smoke tests are the gates.

## S - Safeguards

- Do not code until this canvas is Ready For Coding and FEAT-004 is in place.
- Measurement only: no scoring/optimization under this Work ID.
- **Ship neutral.** Any shipped docs/templates describe readiness as a neutral capability, never the internal posture.
- Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.

## Review Checklist

- [ ] Requirements satisfied
- [ ] Entities updated correctly
- [ ] Approach followed or synced
- [ ] Structure followed or synced
- [ ] Operations completed
- [ ] Norms followed
- [ ] Safeguards respected
- [ ] Tests added or updated
- [ ] No unrelated refactors
- [ ] Documentation updated if needed

## Sync Notes

Make-it-fast measurement, deferred until the refactors (FEAT-001→003) and FEAT-004
land. Use sync notes to track drift.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
