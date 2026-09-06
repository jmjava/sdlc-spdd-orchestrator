# REASONS Canvas: TEST-002-hello — freeze one new AC for the first eval slice

## Metadata

- Work ID: TEST-002-hello
- Work Type: Test gold
- Status: Frozen
- Readiness: Ready For Coding
- Created: 2026-09-06
- Milestone: milestone-2
- Slice: TEST-002 first slice (TEST-001 §3.2)

## R - Requirements

### User Goal

Add `farewell(name)` that returns `goodbye, {name}` without extra helpers.

### Acceptance Criteria

- [ ] `farewell("ada") == "goodbye, ada"`
- [ ] Existing `greet()` behavior is unchanged

### Non-Goals

- Do not add `shout`, logging, CLI flags, or other helpers
- Do not modify the live-consumer seed in `tests/live-consumer/seed/`
- Do not restore Spring Boot Java in this slice

## E - Entities

- Greeting / farewell string
- Files: `src/hello.py`, `tests/test_farewell.py`

## A - Approach

Implement one function next to `greet`. Do not refactor the module.

## S - Structure

- `src/hello.py` — add `farewell`
- `tests/test_farewell.py` — already frozen failing until the function exists

## O - Operations

### T01 - Add farewell(name)

- Status: Frozen (eval operation)
- Description: Add `farewell(name: str) -> str` returning `goodbye, {name}`.
- Files: `src/hello.py`, `tests/test_farewell.py`
- Tests: `tests/test_farewell.py`
- Validation: `python3 -m pytest tests/test_farewell.py` from this directory after implementation

## N - Norms

- One operation
- Cite C-DRIFT: extra helpers are unmapped

## S - Safeguards

- Non-goals list is the extra-hunk list
- This canvas is the spec for **both** conditions (unstructured is still scored against it)

## Review Checklist

- [x] Gold completeness: source runs, T01 named, non-goals explicit, failing test exists

## Sync Notes

Frozen 2026-09-06 from live-consumer seed hello.py. Spring Boot gold remains blocked (no Java).

## Final Status

- Readiness: Ready For Coding
- Status: Frozen
