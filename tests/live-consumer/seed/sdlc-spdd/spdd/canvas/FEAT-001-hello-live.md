# REASONS Canvas: FEAT-001-hello-live - Hello Live Consumer

## Metadata

- Work ID: FEAT-001-hello-live
- Work Type: Feature
- Status: In Progress
- Readiness: Needs Analysis
- Created: 2026-07-31
- Updated: 2026-07-31
- Owner: live-matrix
- Target Project: sdlc-spdd-live
- Stack: Python
- Source System:
- Source Issue:
- Source URL:
- Docs URL:
- Roadmap: ROADMAP.md
- Milestone: milestone-1
- Related PR:

## R - Requirements

### User Goal

Seed/flush a fake consumer repo and exercise every installed script and Cursor
slash command path.

### Business / Product Goal

Confidence that SDLC-SPDD works for real consumers, not only dogfood.

### Acceptance Criteria

- [ ] Install verifies with `--require-cursor`
- [ ] Workflow CLI claim/next/advance/shelf/archive succeed
- [ ] Slash-command effect checks pass after simulated (or live) invocation

### Non-Goals

- Keeping durable state across matrix runs

### Assumptions

- Cursor is the assistant under test on this machine
- Network-backed issue sync is opt-in

### Open Questions

- None for the seed stub

## E - Entities

### Domain Entities

- Greeting

### Application Components

- Controller:
- Service: `src/hello.py`
- Repository:
- Client:
- Configuration:
- Tests:

### External Systems

- None

### Data / Persistence

- Tables:
- Migrations:
- Indexes:
- Queues:
- Events:

### Files Likely Affected

- `src/hello.py`

## A - Approach

### Proposed Approach

Install framework into a wiped git repo, run shell matrix, then verify Cursor
command adapters and deterministic side-effects.

### Alternatives Considered

1. Persistent sibling GitHub repo (rejected: drifts)
2. Dogfood-only in orchestrator (rejected: wrong install paths)

### Trade-Offs

- Ephemeral realism over long-lived consumer convenience

### Risks

- Slash commands need chat invocation for full path coverage

### Failure Modes

- Install leaves incomplete `scripts/sdlc-spdd/`

## S - Structure

### Files To Add

- `src/hello.py`

### Files To Modify

- none initially

### Package / Module Structure

Single-module seed app.

### Test Structure

Orchestrator `tests/live-consumer/` matrix.

### Documentation Structure

`tests/live-consumer/README.md`

## O - Operations

### T01 - Implement greet helper

- Status: Not Started
- Description: Ensure `greet(name)` returns hello string
- Files: `src/hello.py`
- Tests: matrix scenario asserts file exists and helper works
- Validation: `python3 -c "from src.hello import greet; assert greet('x')=='hello, x'"`

### T02 - Matrix green

- Status: Not Started
- Description: All live-consumer scenarios pass
- Files: `tests/live-consumer/`
- Tests: `./tests/test-live-consumer-matrix.sh`
- Validation: exit 0

## N - Norms

### General

- Follow existing project conventions.
- Prefer small, targeted changes.

### Testing

- Prefer deterministic shell assertions.
- Keep seed/flush idempotent.

## S - Safeguards

- Do not write outside the live consumer root.
- Do not push to remotes unless an opt-in scenario enables it.
- Do not commit secrets.

## Review Checklist

- [ ] Requirements satisfied
- [ ] Operations completed
- [ ] Tests added or updated

## Sync Notes

Seed canvas for live matrix.

## Final Status

- Status: In Progress
- Completed Date:
- PR:
- Follow-Up Tasks:
