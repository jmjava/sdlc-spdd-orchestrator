# Analysis: TEST-002 — First behavioral eval slice

## Metadata

- Work ID: TEST-002-assistant-behavior-eval
- Date: 2026-09-06
- Depends on: TEST-001, FEAT-016, DOC-003, FEAT-017 (merged)

## Scope Lock

### In Scope

- Freeze hello gold (source + canvas T01 + failing test + non-goals)
- Record n=1 unstructured vs full-method patches scored for C-DRIFT (symbol proxy)
- Write limitations beside numbers (protocol incomplete, C-PORT not reported)
- Do not restore Spring Boot Java

### NOT in Scope

- n≥3 (log must say protocol incomplete)
- Second assistant / C-PORT as a result
- Claiming the method works
- Embabel upstream

## Recommendation

Dated eval fixture under `tests/eval/test-002-hello/`. Operator-as-agent n=1 is a recorded run, not a journal finding.
