# REASONS Canvas: <WORK-ID> - <Work Name>

## Metadata

- Work ID:
- Work Type: Feature
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
- Related PR:

## R - Requirements

### User Goal

Describe what the user wants.

### Business / Product Goal

Describe why this matters.

### Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Non-Goals

- Non-goal 1
- Non-goal 2

### Assumptions

- Assumption 1
- Assumption 2

### Open Questions

- Question 1
- Question 2

## E - Entities

### Domain Entities

- Entity 1
- Entity 2

### Application Components

- Controller:
- Service:
- Repository:
- Client:
- Configuration:
- Tests:

### External Systems

- System 1
- System 2

### Data / Persistence

- Tables:
- Migrations:
- Indexes:
- Queues:
- Events:

### Files Likely Affected

- `path/to/file`

## A - Approach

### Proposed Approach

Describe the implementation strategy.

### Alternatives Considered

1. Alternative 1
2. Alternative 2

### Trade-Offs

- Trade-off 1
- Trade-off 2

### Risks

- Risk 1
- Risk 2

### Failure Modes

- Failure mode 1
- Failure mode 2

## S - Structure

### Files To Add

- `path/to/new-file`

### Files To Modify

- `path/to/existing-file`

### Package / Module Structure

Describe expected organization.

### Test Structure

Describe expected tests.

### Documentation Structure

Describe expected documentation updates.

## O - Operations

### T01 - Task Name

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T02 - Task Name

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

### T03 - Task Name

- Status: Not Started
- Description:
- Files:
- Tests:
- Validation:

## N - Norms

### General

- Follow existing project conventions.
- Prefer small, targeted changes.
- Do not perform broad unrelated refactors.
- Keep implementation aligned with this canvas.
- Update this canvas if implementation reality changes.
- Do not invent requirements that were not requested.
- Prefer explicit assumptions over hidden assumptions.

### Java / Spring Boot

- Use the Java version already configured in the project.
- Use the Spring Boot version already configured in the project.
- Prefer constructor injection.
- Do not put business logic in controllers.
- Keep services focused on use-case orchestration.
- Keep repositories focused on persistence.
- Use records for DTOs if the project already uses records.
- Do not introduce Lombok unless already used.
- Do not introduce new dependencies without justification.
- Follow existing exception handling patterns.
- Follow existing validation patterns.
- Preserve existing package boundaries.

### Testing

- Add or update tests for every behavior change.
- Prefer focused unit tests for business logic.
- Prefer integration tests for database/API behavior.
- Use existing test frameworks and conventions.
- Do not weaken or delete existing tests unless explicitly justified.
- Document tests that could not be run.

## S - Safeguards

- Do not change public API behavior unless required by the feature.
- Do not change database schema without migration instructions.
- Do not change security behavior without explicit mention.
- Do not change authentication or authorization rules unless required.
- Do not introduce hidden background jobs unless required.
- Do not add network calls without documenting timeout/failure behavior.
- Do not silently swallow exceptions.
- Do not mark the feature complete until acceptance criteria are satisfied.
- Do not mark the feature complete until tests pass or failures are documented.
- Do not implement behavior changes until this canvas is updated with `/sdlc-spdd-prompt-update`.
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
- [ ] No unexplained dependencies
- [ ] Documentation updated if needed

## Sync Notes

Use this section to track changes between original plan and final implementation.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
