# REASONS Canvas: <WORK-ID> - <Work Name>

## Metadata

- Work ID:
- Work Type: Bugfix
- Status: Draft
- Created:
- Updated:
- Owner:
- Target Project:
- Stack:
- Source System:
- Source Issue:
- Source URL:
- Docs URL:
- Roadmap:
- Milestone:
- Related PR:

## R - Requirements

### User Goal

Describe the broken behavior and expected fix.

### Business / Product Goal

Describe impact of the bug and why fixing it matters.

### Acceptance Criteria

- [ ] Bug is reproduced or root cause identified
- [ ] Fix resolves the reported behavior
- [ ] Regression test added

### Non-Goals

- Non-goal 1
- Non-goal 2

### Assumptions

- Assumption 1

### Open Questions

- Question 1

## E - Entities

### Domain Entities

- Entity affected

### Application Components

- Controller:
- Service:
- Repository:
- Tests:

### External Systems

- System 1

### Data / Persistence

- Tables:
- Migrations:

### Files Likely Affected

- `path/to/file`

## A - Approach

### Proposed Approach

Describe root cause and fix strategy.

### Alternatives Considered

1. Alternative 1

### Trade-Offs

- Trade-off 1

### Risks

- Risk of regression

### Failure Modes

- Fix incomplete or introduces new failure

## S - Structure

### Files To Add

- `path/to/regression-test`

### Files To Modify

- `path/to/buggy-file`

### Package / Module Structure

Describe expected organization.

### Test Structure

Describe regression and unit tests.

### Documentation Structure

Note any release notes or runbook updates.

## O - Operations

### T01 - Reproduce and Document

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T02 - Implement Fix

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T03 - Verify and Close

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

## N - Norms

### General

- Fix the smallest surface area that resolves the bug.
- Do not perform unrelated refactors.
- Add a regression test when feasible.
- Document root cause in the canvas or progress log.

### Java / Spring Boot

- Follow existing exception handling patterns.
- Preserve existing package boundaries.
- Do not upgrade dependencies unless required for the fix.

### Testing

- Add or update tests for the fixed behavior.
- Prefer a focused regression test over broad suite changes.

## S - Safeguards

- Do not change unrelated public API behavior.
- Do not change security behavior without explicit mention.
- Do not silently swallow exceptions.
- Do not mark complete until acceptance criteria are satisfied.
- Do not implement behavior changes until this canvas is updated with `/sdlc-spdd-prompt-update`.
- Do not let implementation drift from this canvas without running `/sdlc-spdd-sync`.

## Review Checklist

- [ ] Root cause addressed
- [ ] Regression test added
- [ ] No unrelated refactors
- [ ] Safeguards respected

## Sync Notes

Use this section to track changes between original plan and final implementation.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
