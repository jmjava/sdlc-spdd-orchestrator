# Analysis: FEAT-015 — First-class queryable process metrics

## Metadata

- Work ID: FEAT-015-first-class-metrics
- Date: 2026-09-06
- Depends on: DOC-001 (merged), FEAT-014/016 (merged)

## Scope Lock

### In Scope

- Structured metric fields on ledger records: readiness, review_result, rework, context_files, validate_cycles, review_cycles
- Capture → stage → accept writes those fields (not only `session.body` tags)
- Engine CLI query that answers `rework` by phase from structured fields
- One documented query per DOC-001 construct that uses capture flags (C-COMPLY, C-CONTEXT, C-REWORK, C-MEMORY)
- Round-trip tests that fail if the query greps prose

### NOT in Scope

- Restoring ledger `kind=metric` (kinds stay `decision|pitfall|pattern|session|analysis`)
- SQLite column projection of metric fields (JSONL is the query source)
- C-DRIFT / C-PORT capture-flag queries (those constructs are not capture metrics)
- Prompt optimization / `spdd --metrics` product surface
- Guide ontology changes
- Embabel upstream

## Current state

`LEDGER_KINDS` has no `metric`. `capture-session-memory.sh` still accepts `--readiness`, `--review-result`, `--rework`, `--context-files`, `--validate-cycles`, `--review-cycles` and stuffs `review-result=…` into **session body**. `--validate-cycles` / `--review-cycles` are parsed but not even written to the body tags. Python `LessonRecord` / `persist-lesson` have no metric fields. `LessonsLedger.records()` cannot answer “rework by phase” without parsing prose.

## Recommendation

Keep `kind=session`. Add an optional `metrics` object on `LessonRecord` (schema 2 when present). Query via `sdlc-engine context metrics --construct C-REWORK` over ledger JSONL. Capture scripts write the object **and** keep body tags so existing live-consumer greps still pass.

## Risks

- Body tags remaining could tempt a grep-based query. Tests plant `rework=99` in body with structured `rework=2`.
- Dual capture copies (`scripts/` and `sdlc-spdd/scripts/`) must stay in sync.
