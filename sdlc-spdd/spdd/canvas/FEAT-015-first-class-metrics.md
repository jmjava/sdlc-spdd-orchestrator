# REASONS Canvas: FEAT-015-first-class-metrics — Queryable capture metrics

## Metadata

- Work ID: FEAT-015-first-class-metrics
- Work Type: Feature
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: DOC-001-research-questions-and-constructs
- Blocks: DOC-003-replication-package
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/FEAT-015-first-class-metrics.md`
- Analysis: `sdlc-spdd/spdd/analysis/FEAT-015-first-class-metrics-analysis.md`
- Beck stage: make it right (C-COMPLY / C-CONTEXT / C-REWORK / C-MEMORY observability)

## R - Requirements

### User Goal

Restore FEAT-004's intent: process metrics are structured, queryable fields — not optional flags buried in session body text after `kind=metric` was dropped.

### Business / Product Goal

TEST-002 and replication notes can query readiness, review-result, context-files, and rework/cycles without grepping prose.

### Acceptance Criteria

- [x] Metrics are not solely free-text in session.body
- [x] At least one documented query per DOC-001 construct that is supposed to use capture metrics
- [x] Tests: capture flags round-trip into the query surface

### Non-Goals

- Restoring `kind=metric`
- SQLite metric columns
- C-DRIFT / C-PORT as capture-flag queries
- Prompt optimization
- Embabel upstream

## E - Entities

- ProcessMetrics object on LessonRecord
- Construct query (C-COMPLY, C-CONTEXT, C-REWORK, C-MEMORY)
- Capture flags (`--readiness`, `--review-result`, `--rework`, `--context-files`, `--validate-cycles`, `--review-cycles`)

### Files likely affected

- `engine/src/sdlc_engine/lessons_ledger.py`
- `engine/src/sdlc_engine/metrics.py`
- `engine/src/sdlc_engine/context_store.py`
- `engine/src/sdlc_engine/cli_parser.py`
- `engine/src/sdlc_engine/cli_commands.py`
- `scripts/capture-session-memory.sh`
- `scripts/lib/paths.sh`

## A - Approach

Optional `metrics` JSON object on session (and persist-lesson) records. CLI `context metrics` aggregates those fields by phase. Capture writes the object; body tags remain as a human-readable copy, not the query source.

## S - Structure

### Files to add

- `engine/src/sdlc_engine/metrics.py`
- `engine/tests_unit/test_process_metrics.py`
- `sdlc-spdd/docs/research/capture-metrics-queries.md`

### Files to modify

- LessonRecord / persist-lesson / capture scripts / construct spec instrument rows

### Test structure

- Structured rework=2 wins over body `rework=99`
- CLI persist flags round-trip through `context metrics`
- Capture script writes `metrics` object
- C-DRIFT / C-PORT return `not_capture_metrics`

## O - Operations

### T01 - Structured metrics object and construct queries

- Status: Complete
- Description: Add ProcessMetrics on LessonRecord, persist-lesson flags, capture JSON object, `context metrics` CLI, documented construct queries, round-trip tests.
- Files: `engine/src/sdlc_engine/metrics.py`, `engine/src/sdlc_engine/lessons_ledger.py`, `engine/src/sdlc_engine/context_store.py`, `engine/src/sdlc_engine/cli_parser.py`, `engine/src/sdlc_engine/cli_commands.py`, `scripts/lib/paths.sh`, `scripts/capture-session-memory.sh`, `sdlc-spdd/docs/research/capture-metrics-queries.md`
- Tests: `engine/tests_unit/test_process_metrics.py`, `tests/test-canvas-readiness.sh`
- Validation: query does not parse body; capture flags appear in `record.metrics`

## N - Norms

- Cite C-COMPLY, C-CONTEXT, C-REWORK, C-MEMORY
- One operation
- Do not invent a sixth RQ
- Keep `scripts/` and `sdlc-spdd/scripts/` copies in sync

## S - Safeguards

- Do not claim C-DRIFT or C-PORT are capture-metric constructs
- Do not restore `kind=metric`
- No Embabel upstream
- Body tags are not the query source

## Review Checklist

- [x] Structured fields round-trip
- [x] Body-grep query cannot pass the tests
- [x] Construct queries documented
- [x] Dual script copies synced

## Sync Notes

Follows merged FEAT-016 (`abfc123`). JSONL is the system of record; SQLite lessons table is unchanged.

## Final Status

- Readiness: Reviewed
- Status: Complete
