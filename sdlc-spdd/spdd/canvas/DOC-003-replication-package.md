# REASONS Canvas: DOC-003-replication-package — Threats and replication notes

## Metadata

- Work ID: DOC-003-replication-package
- Work Type: Documentation
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: TEST-001-evaluation-protocol, FEAT-015-first-class-metrics
- Blocks: (none)
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/DOC-003-replication-package.md`
- Analysis: `sdlc-spdd/spdd/analysis/DOC-003-replication-package-analysis.md`
- Beck stage: make it right (research argument)

## R - Requirements

### User Goal

Give a future referee a threats-to-validity section and a replication appendix that names frozen versions, datasets, and what cannot be automated.

### Business / Product Goal

TEST-002 can copy a freeze checklist instead of inventing one. Public claims stay inside DOC-001’s claims-allowed table.

### Acceptance Criteria

- [x] Committed threats-to-validity doc referencing DOC-001 constructs
- [x] Replication checklist: commands, versions, gold-task locations
- [x] Explicit statement of chat nondeterminism and how TEST-001 handles it

### Non-Goals

- Study data
- Guide/Neo4j as a required replicator
- Expanding product surface
- Embabel upstream

## E - Entities

- Threat category (construct / internal / external / conclusion / reliability)
- Freeze row (item, how, command/path)
- Live-consumer limitation
- TEST-001 nondeterminism rule

### Files likely affected

- `sdlc-spdd/docs/research/threats-to-validity-and-replication.md`
- `sdlc-spdd/docs/research/check_p0_artifacts.py`
- `tests/research/test_p0_artifacts.py`

## A - Approach

One markdown pack. Checker parses threat headings, construct IDs in the construct section, a freeze table, gold path, and TEST-001 n≥3 / protocol-incomplete language. Token stubs fail.

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/threats-to-validity-and-replication.md`
- `tests/research/fixtures/threats_*.md`

### Files to modify

- P0 checker, prove-p0.sh, research CI, docs/research/README.md

### Test structure

- Valid fixture has no issues
- Token stub with C-DRIFT…C-PORT tokens fails
- Missing C-PORT in construct section fails
- Live `check_doc003()` passes

## O - Operations

### T01 - Threats pack, freeze checklist, structured proof

- Status: Complete
- Description: Write threats/replication notes citing C-DRIFT..C-PORT and TEST-001 nondeterminism; extend the research checker and CI.
- Files: `sdlc-spdd/docs/research/threats-to-validity-and-replication.md`, `sdlc-spdd/docs/research/check_p0_artifacts.py`, `sdlc-spdd/docs/research/prove-p0.sh`, `tests/research/test_p0_artifacts.py`, `.github/workflows/test-research-p0.yml`
- Tests: `python3 -m unittest tests.research.test_p0_artifacts -v` and `prove-p0.sh DOC-003`
- Validation: token stub fails; live DOC-003 checker passes; canvas validates

## N - Norms

- Cite DOC-001 construct IDs
- One operation
- Do not start TEST-002 in this PR

## S - Safeguards

- Do not collect or invent study data
- Do not require Guide/Neo4j
- No Embabel upstream
- Do not weaken tests to token grep
- Live-consumer is not method evidence

## Review Checklist

- [x] Five threat categories
- [x] All five constructs in construct validity
- [x] Freeze table with commands and gold path
- [x] TEST-001 n≥3 / protocol incomplete
- [x] Structured tests, not grep

## Sync Notes

Follows merged FEAT-015 (`1df0c2e` / PR #229).

## Final Status

- Readiness: Reviewed
- Status: Complete
