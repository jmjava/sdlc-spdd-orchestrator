# REASONS Canvas: REF-001-engine-single-source — One gate_check semantics

## Metadata

- Work ID: REF-001-engine-single-source
- Work Type: Refactor
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: SPIKE-004-academic-contribution-bar
- Related: FEAT-016-intent-code-traceability, FEAT-014-semantic-canvas-validation
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/REF-001-engine-single-source.md`
- Analysis: `sdlc-spdd/spdd/analysis/REF-001-engine-single-source-analysis.md`
- Beck stage: make it right (C-COMPLY validity)

## R - Requirements

### User Goal

Remove the internal-validity confound of default-shell vs Python engines implementing 'the method' differently. Research claims must name one semantics.

### Business / Product Goal

Milestone 2 evaluation names Python `gate_check` as the SUT. Operators who can import `sdlc_engine` get those semantics without setting an extra env var.

### Acceptance Criteria

- [x] Documented system-under-test engine for Milestone 2 evaluation
- [x] gate_check semantics live in one place; the other path delegates or is tested equal
- [x] ROADMAP/TESTING mention the chosen SUT

### Non-Goals

- Deleting all shell scripts
- New workflow phases
- Embabel upstream

## E - Entities

- `SDLC_ENGINE` (auto / python / shell)
- `SDLC_GATE_ENGINE=shell` fallback
- Python `WorkflowEngine.gate_check`

### Files likely affected

- `scripts/sdlc.sh`
- `templates/agent-context/sdlc-workflow.sh`
- `TESTING.md`
- `sdlc-spdd/docs/research/engine-sut.md`

## A - Approach

Default `SDLC_ENGINE` to `auto`. Workflow gates call Python whenever it is importable. Keep a labeled shell fallback for harnesses that set `SDLC_GATE_ENGINE=shell`. Prove a headings-only canvas that the old substring gate would accept fails on the SUT path and on `SDLC_ENGINE=shell` when Python is available. `sdlc.sh capture`/`start`/`accept` stay on the shell path (`local capture` / `context accept` are the Python verbs).

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/engine-sut.md`
- `tests/research/test_ref001_sut.py`

### Files to modify

- `scripts/sdlc.sh`, `sdlc-spdd/scripts/sdlc.sh`
- workflow scripts (templates + dogfood)
- TESTING.md, ROADMAP, DOC-003 dual-engine row

### Test structure

- Headings-only + “ready for coding” substring fails Python `gate_check(code)`
- Same fixture fails `SDLC_ENGINE=shell` workflow gate when PYTHONPATH can import the engine
- `SDLC_GATE_ENGINE=shell` is the only path that still uses the substring fallback
- SUT doc names Python

## O - Operations

### T01 - Name SUT, default auto, delegate gates to Python

- Status: Complete
- Description: Document Python gate_check as the Milestone 2 SUT; default SDLC_ENGINE=auto; workflow gates delegate to Python when importable; SDLC_GATE_ENGINE=shell is the explicit fallback.
- Files: `scripts/sdlc.sh`, `sdlc-spdd/scripts/sdlc.sh`, `templates/agent-context/sdlc-workflow.sh`, `sdlc-spdd/scripts/sdlc-workflow.sh`, `scripts/accept-lessons.sh`, `sdlc-spdd/scripts/accept-lessons.sh`, `tests/test-sdlc-workflow.sh`, `tests/test-sdlc-engine-shim.sh`, `TESTING.md`, `docs/engine-v2.md`, `sdlc-spdd/docs/research/engine-sut.md`, `tests/research/test_ref001_sut.py`, `sdlc-spdd/ROADMAP.md`, `sdlc-spdd/requirements/milestones/milestone-2/MILESTONE-2.md`, `CHANGELOG.md`, `sdlc-spdd/docs/research/evaluation-protocol.md`, `sdlc-spdd/docs/research/threats-to-validity-and-replication.md`, `.github/workflows/test-research-p0.yml`, `engine/src/sdlc_engine/archive.py`, `engine/tests_unit/test_registry_archive.py`
- Tests: `python3 -m unittest tests.research.test_ref001_sut -v`
- Validation: headings-only canvas fails SUT and delegated shell-CLI; ROADMAP/TESTING name Python

## N - Norms

- Cite C-COMPLY
- One operation
- Do not claim this unifies every shell script, only gate_check

## S - Safeguards

- No Embabel upstream
- Install/upgrade scripts stay shell
- Do not treat SDLC_GATE_ENGINE=shell as an evaluation condition
- Dual copies of sdlc.sh / sdlc-workflow.sh stay in sync

## Review Checklist

- [x] SUT documented
- [x] Default auto
- [x] Delegation test
- [x] ROADMAP/TESTING updated

## Sync Notes

Follows merged CHORE-003 (`7b8a139` / PR #237).

## Final Status

- Readiness: Reviewed
- Status: Complete
