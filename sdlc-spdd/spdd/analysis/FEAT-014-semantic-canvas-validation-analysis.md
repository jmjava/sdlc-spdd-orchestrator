# Analysis: FEAT-014 — Semantic REASONS canvas validation

## Metadata

- Work ID: FEAT-014-semantic-canvas-validation
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/FEAT-014-semantic-canvas-validation.md`
- Date: 2026-09-06
- Construct: C-COMPLY (DOC-001)
- Depends on: DOC-001 (merged)

## Scope Lock

### In Scope for This Work

- Structured readiness (YAML frontmatter or Metadata `- Readiness:`) as the `gate_check(code)` gate
- Semantic minima: non-empty Requirements; at least one T## operation with Status
- Headings-only canvas fails `validate-reasons-canvas.sh`
- Unrecognized readiness fails when `--strict-readiness` or `SDLC_CANVAS_STRICT_READINESS=1`
- Unit tests: false-Ready (phrase in Sync Notes / Architecture Notes) and empty Operations

### NOT in Scope (Deferred)

- LLM-judged canvas quality
- Changing REASONS section names
- Review-file semantic minima (FEAT-016)
- Unifying shell `sdlc-workflow.sh` with Python `gate_check` (REF-001)
- Embabel upstream

## Code Areas

- `engine/src/sdlc_engine/canvas.py`
- `engine/src/sdlc_engine/workflow.py` `gate_check(code)` / `infer_phase_from_artifacts`
- `scripts/validate-reasons-canvas.sh`, `scripts/lib/readiness.sh` (and dogfood copies)
- `engine/tests_unit/test_canvas.py`, `test_workflow_gates.py`
- `tests/test-canvas-readiness.sh`

## Existing Concepts

- Heading grep; `/ready for coding/i` anywhere; readiness warn-only
- FEAT-005 canonical readiness vocabulary

## New Concepts

- Structured readiness vs stray phrase
- Semantic minima vs headings-only
- Strict unrecognized-readiness policy flag

## Risks

- Existing tests seeded Status: Ready For Coding without a Readiness field
- Spring Boot example has Readiness only under Architecture Notes — validator stays optional-readiness; code gate would refuse it until Metadata is set

## Recommendation

Implement Python as the research SUT (`gate_check`) and the same minima in the shell validator CI uses.
