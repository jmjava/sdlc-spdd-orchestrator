# Review: FEAT-015-first-class-metrics

**Work ID:** FEAT-015-first-class-metrics  
**Date:** 2026-09-06  
**Result:** Approved With Notes  

## Summary

T01 restores queryable capture metrics without bringing back `kind=metric`. Session records carry a structured `metrics` object. `sdlc-engine context metrics` aggregates those fields by phase for C-COMPLY, C-CONTEXT, C-REWORK, and C-MEMORY. Body tags remain a human copy. Tests plant `rework=99` in body with structured `rework=2` so a grep-based query cannot pass.

## Proof

| Check | Result |
|-------|--------|
| Structured rework vs body `rework=99` | query returns 2 |
| CLI persist flags → `context metrics` | C-COMPLY / C-CONTEXT / C-REWORK round-trip |
| Capture script writes `metrics` object | schema 2; validate_cycles / review_cycles present |
| C-DRIFT / C-PORT | `not_capture_metrics`, empty rows |
| Schema 1 records without metrics | still load; omitted from query |
| `pytest engine/tests_unit` | 225 passed, 3 skipped |
| `tests/test-canvas-readiness.sh` | 14 passed |

## Findings

1. **Note:** Flags remain self-reported. Omitted flags leave the measure undefined.
2. **Note:** SQLite `lessons` has no metric columns. JSONL is the query source.
3. **Safeguards:** C-DRIFT and C-PORT are not treated as capture-metric constructs. No Embabel upstream.

## Required changes

None.

## Recommendation

Mark Complete. Next P1 item: DOC-003 (replication / threats).
