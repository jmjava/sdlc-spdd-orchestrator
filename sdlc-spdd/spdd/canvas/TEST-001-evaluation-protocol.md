# REASONS Canvas: TEST-001-evaluation-protocol — Comparative evaluation protocol

## Metadata

- Work ID: TEST-001-evaluation-protocol
- Work Type: Test
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: DOC-001-research-questions-and-constructs, DOC-002-related-work-map
- Blocks: TEST-002, DOC-003
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/TEST-001-evaluation-protocol.md`
- Analysis: `sdlc-spdd/spdd/analysis/TEST-001-evaluation-protocol-analysis.md`
- Parent plan: `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`
- Beck stage: make it right (research argument)

## R - Requirements

### User Goal

Write a replicable protocol that evaluates the *method* (outcomes vs baselines), not only the CLI. Do not collect study data in this Work ID.

### Business / Product Goal

Give TEST-002 a procedure it cannot silently skip: gold, raters, metrics, stop rules, nondeterminism, blockers.

### Acceptance Criteria

- [x] Protocol document names tasks, gold files, raters, metrics, stop rules
- [x] Each RQ in DOC-001 maps to at least one protocol procedure
- [x] Live-consumer / example gaps (no Java source, Cursor-only) are listed as current blockers with owners

### Non-Goals

- Executing the study
- Engine features except stubs required to record protocol IDs
- Expanding product surface
- Upstream PRs to embabel/guide

### Assumptions

- First TEST-002 slice uses the live-consumer seed (has `hello.py`) unless Java is restored
- RQ4 is specified but out of the first slice unless a two-session fixture is added
- Python `gate_check` is the SUT until REF-001

## E - Entities

- Process condition / baseline
- Gold task
- Rater sheet
- Session run (not collected here)
- Blocker + owner

### Files likely affected

- `sdlc-spdd/docs/research/evaluation-protocol.md`
- `tests/research/test_p0_artifacts.py`
- `.github/workflows/test-research-p0.yml`
- `docs/research/README.md`

## A - Approach

One protocol markdown. Procedures are headings (`RQ1 procedure` … `RQ5 procedure`) so the checker cannot be satisfied by name-drops.

Filesystem-backed check: if `examples/spring-boot-order-api` still has no `*.java`, the protocol must say so; if Java appears, the “no Java” sentence must go.

Do not record fabricated n or findings.

### Alternatives

- Protocol only in the SPIKE canvas — rejected; TEST-002 needs a citable spec.
- Spring Boot as the only gold — rejected; it cannot score C-DRIFT today.

### Risks

- TEST-002 ignores stop rules
- Raters skipped because canvas presence leaks the condition

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/evaluation-protocol.md`

### Files to modify

- `docs/research/README.md`
- `tests/research/test_p0_artifacts.py`
- `.github/workflows/test-research-p0.yml`

### Test structure

- Live `check_test001()` must pass
- Namedrop fixture (RQ tokens, no procedure headings) must fail
- Token stub must fail
- CI runs `prove-p0.sh TEST-001`

## O - Operations

### T01 — Commit evaluation protocol and live TEST-001 checks

- Status: Complete
- Description: Write the protocol with four baselines, gold paths, RQ1–RQ5 procedures, rater protocol, nondeterminism, stop rules, blockers with owners. Extend the P0 unittest live check and CI.
- Files: `sdlc-spdd/docs/research/evaluation-protocol.md`, `tests/research/**`, `.github/workflows/test-research-p0.yml`
- Tests: `python3 -m unittest tests.research.test_p0_artifacts -v` and `prove-p0.sh TEST-001`
- Validation: every RQ has a procedure heading; Spring Boot Java gap is filesystem-checked

## N - Norms

- Cite DOC-001 construct IDs
- One operation
- Do not start FEAT-014 in this Work ID

## S - Safeguards

- Do not collect or invent study data
- Do not modify engine code
- No Embabel upstream framing
- Do not weaken tests to token grep

## Review Checklist

- [x] Four baselines named
- [x] Gold files named
- [x] RQ1–RQ5 procedures
- [x] Raters, nondeterminism, stop rules
- [x] Blockers with owners
- [x] Live tests include TEST-001

## Sync Notes

Created 2026-09-06 after DOC-002 merge (`9a6b00a` / PR #221).

## Final Status

- Readiness: Reviewed
- Status: Complete
