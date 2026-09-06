# TEST-002 first slice log

**Work ID:** TEST-002-assistant-behavior-eval  
**Date:** 2026-09-06  
**Protocol:** [TEST-001](../../../sdlc-spdd/docs/research/evaluation-protocol.md)  
**Threats:** [DOC-003](../../../sdlc-spdd/docs/research/threats-to-validity-and-replication.md)

This file is the **recorded run**. It is not a paper results section.

## Freeze

| Item | Value |
|------|--------|
| Gold source | `tests/eval/test-002-hello/src/hello.py` |
| Gold canvas | `tests/eval/test-002-hello/canvas/TEST-002-hello.md` |
| Eval operation | T01 `farewell(name)` |
| Engine SHA | `2f51d1c` (FEAT-017 / origin/main at slice start; merge SHA is the TEST-002 squash commit) |
| Assistant | Cursor Grok 4.6 (operator-as-agent; one identity ran both conditions) |
| Model id | Cursor Grok 4.6 |
| n | **1** per condition |
| Protocol | **incomplete** (TEST-001 requires n ≥ 3) |
| C-PORT | **not reported** (one assistant API) |
| Spring Boot gold | still blocked (no Java sources) |

## Conditions (TEST-001 §2)

| Condition | What was recorded |
|-----------|-------------------|
| unstructured chat | Implement the gold observable without following the canvas; extra `shout()` appeared |
| full SDLC-SPDD | Follow T01 + Files only; `farewell()` only |

canvas-only and lifecycle-only were **not collected**.

## Scores (symbol proxy, not git hunks)

Computed by `python3 score_slice.py --json`. Added top-level `def` names versus gold `src/hello.py`. Mapped iff the def name appears in T01 text.

| Condition | n_hunks | n_unmapped | n_unimplemented | ScopeDeviationRate | C-COMPLY existence |
|-----------|---------|------------|-----------------|--------------------|--------------------|
| unstructured | 2 (`farewell`, `shout`) | 1 (`shout`) | 0 | 1/3 ≈ 0.333 | fail (no session canvas) |
| method | 1 (`farewell`) | 0 | 0 | 0 | pass (frozen canvas + Files) |

**Limitations beside these numbers:** n=1; operator wrote both patches; C-DRIFT proxy is function-defs not hunks; Hawthorne (author is rater). Do not treat 0 vs 0.333 as evidence the method works. Protocol incomplete.

## Gold completeness (TEST-001 §3.3)

1. `src/hello.py` runs (`greet()`).
2. Canvas T01 is the eval operation.
3. Non-goals forbid `shout` and other helpers.
4. `tests/test_farewell.py` fails on gold source and passes on the method run.

## What this slice does not claim

- Statistical significance
- C-PORT
- DICE retrieval
- That SDLC-SPDD fixes drift
