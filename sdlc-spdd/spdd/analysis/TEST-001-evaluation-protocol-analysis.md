# Analysis: TEST-001 — Comparative evaluation protocol

## Metadata

- Work ID: TEST-001-evaluation-protocol
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/TEST-001-evaluation-protocol.md`
- Date: 2026-09-06
- Depends on: DOC-001 (constructs), DOC-002 (baselines)
- Parent plan: `sdlc-spdd/spdd/canvas/SPIKE-004-academic-contribution-bar.md`

## Scope Lock

### In Scope for This Work

- Written protocol: gold tasks, raters, metrics, stop rules, nondeterminism
- Four baselines: unstructured chat; canvas-only; lifecycle-only; full SDLC-SPDD
- One procedure per DOC-001 RQ (RQ4 two-session; marked out of first TEST-002 slice unless included)
- Blockers with owners (no Java in Spring Boot example; Cursor-oriented live consumer)
- Explicit: this Work ID does not collect study data

### NOT in Scope (Deferred)

- Executing the study (TEST-002)
- Building engine features (FEAT-014–017)
- Restoring Java sources in the example (TEST-002)
- Threats-to-validity appendix as a finished DOC-003 package
- Embabel upstream PRs

## Domain Keywords

- gold task, baseline, rater, C-DRIFT, C-COMPLY, nondeterminism, stop rule, portability, rework

## Code Areas

- `sdlc-spdd/docs/research/evaluation-protocol.md` (deliverable)
- `tests/research/` (live TEST-001 check + namedrop fixture)
- `examples/spring-boot-order-api/` (blocked gold — no sources)
- `tests/live-consumer/seed/` (interim gold with `hello.py`)

## Existing Concepts

- DOC-001 instruments vs proxies
- DOC-002 parent-isolation baselines
- `TESTING.md` engineering confidence stack (not this protocol)
- SPIKE-004 M3 evaluation gap

## New Concepts

- Condition table (four process arms)
- Dual gold: blocked Spring Boot vs seed hello with source
- Invalid-run stop rule (condition violation)

## Risks

- Writing a protocol that TEST-002 cannot execute (Java-only gold)
- Name-dropping RQs without procedures (checker rejects this)
- Collecting fake results in the protocol doc

## Recommendation

Commit the protocol at `sdlc-spdd/docs/research/evaluation-protocol.md`. Live tests must fail if the file is missing or if Spring Boot Java sources appear without updating the blocker text.
