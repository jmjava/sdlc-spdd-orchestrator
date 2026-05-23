# REASONS Canvas: <WORK-ID> - <Work Name>

## Metadata

- Work ID:
- Work Type: Refactor
- Status: Draft
- Created:
- Updated:
- Owner:
- Target Project:
- Stack:
- Related Issue:
- Related PR:

## R - Requirements

### User Goal

Describe the structural improvement without changing behavior.

### Business / Product Goal

Describe maintainability, performance, or clarity benefits.

### Acceptance Criteria

- [ ] Behavior preserved (no functional change)
- [ ] Tests pass before and after
- [ ] Structure matches stated target

### Non-Goals

- Feature additions
- API changes

### Assumptions

- Assumption 1

### Open Questions

- Question 1

## E - Entities

### Domain Entities

- Entities unchanged or relocated

### Application Components

- Components being reorganized

### Files Likely Affected

- `path/to/file`

## A - Approach

### Proposed Approach

Describe incremental refactor steps.

### Alternatives Considered

1. Alternative 1

### Trade-Offs

- Trade-off 1

### Risks

- Risk of behavior drift

### Failure Modes

- Large diff hard to review

## S - Structure

### Files To Add

- `path/to/new-module`

### Files To Modify

- `path/to/existing-file`

### Files To Remove

- `path/to/deprecated-file`

### Test Structure

Existing tests must continue to pass; add coverage if gaps exist.

## O - Operations

### T01 - Prepare and Baseline

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T02 - Refactor Step 1

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T03 - Verify Behavior Unchanged

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

## N - Norms

### General

- Preserve behavior unless explicitly changing it.
- Prefer small, reviewable steps.
- Run tests after each operation.

### Java / Spring Boot

- Preserve package boundaries unless refactor explicitly moves them.
- Do not introduce new dependencies without justification.

## S - Safeguards

- Do not change public API behavior unless explicitly in scope.
- Do not delete tests without justification.
- Do not mark complete until tests pass.

## Review Checklist

- [ ] Behavior preserved
- [ ] Tests pass
- [ ] Operations completed incrementally
- [ ] No scope creep into features

## Sync Notes

Use this section to track changes between original plan and final implementation.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
