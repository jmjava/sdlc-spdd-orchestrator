# Requirement: FEAT-005-canvas-readiness-indicators

## Summary

Make canvas readiness machine-parseable (a `readiness:` value in canvas front
matter) and capture leading indicators — counts of validate/review cycles — so the
prompt-optimization signal has structured inputs. This is measurement in service of
prompt optimization.

## Source

- Roadmap: ROADMAP.md (make it fast — measurement for optimization)
- Milestone: milestone-1.md (item 6, do last)

## Stage note

This is **make it fast** and is sequenced last, after the make-it-right refactors
(FEAT-001→003) and alongside/after the prompt-optimization ledger (FEAT-004). Do not
start it before the refactors land.

## Motivation

Today readiness lives in prose ("Readiness: Ready For Coding") and the cost of
getting a canvas to ready (how many validate/review/rework cycles) is not captured.
Structuring these turns them into leading indicators that feed the FEAT-004 ledger
and any later optimization.

## Acceptance Criteria

- [ ] Canvases carry a machine-parseable `readiness:` value (fixed vocabulary).
- [ ] `validate-reasons-canvas.sh` reads/validates the `readiness:` value.
- [ ] Validate/review cycle counts are captured as leading indicators (indexed, reusing the FEAT-004 metric Kind).
- [ ] Existing canvases without the field still validate (backward compatible).
- [ ] Docs describe the readiness vocabulary and indicators.

## Non-Goals

- No scoring, ranking, or acting on the indicators (that is later make-it-fast work).

## Next Step

Deferred. When its turn comes:

    /sdlc-spdd-analysis @requirements/milestones/FEAT-005-canvas-readiness-indicators.md
    /sdlc-spdd-plan @spdd/analysis/FEAT-005-canvas-readiness-indicators-analysis.md
