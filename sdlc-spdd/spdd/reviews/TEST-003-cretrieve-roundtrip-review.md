# Review: TEST-003-cretrieve-roundtrip

**Work ID:** TEST-003-cretrieve-roundtrip  
**Date:** 2026-09-06  
**Result:** Approved  

## Summary

T01 adds a named C-RETRIEVE suite a referee can run: persist/accept one pitfall, then require the same id from the git ledger, from SQLite parity when enabled, and from Guide parity when enabled (HTTP mocked so default CI does not need Neo4j). Unreachable Guide is locked as skip, not a pass. Non-claims (RQ1, RQ4, embeddings, DIF) are in the research note.

## Proof

| Check | Result |
|-------|--------|
| Ledger | persist→`context retrieve` / `show` same id; unknown work_id empty |
| SQLite | `context parity` missing/extra empty; `sqlite_graph` contains the id |
| Guide (mocked) | `by-label` parity missing empty |
| Guide (unreachable) | labelled skip/unreachable, not treated as C-RETRIEVE evidence |
| CI | `test-research-p0.yml` runs `tests.research.test_cretrieve` |
| Spec pointer | DOC-001 names TEST-003 / `test_cretrieve` |

## Findings

1. **Note:** Mocked Guide proves HTTP parity wiring, not DICE embeddings.
2. **Safeguard:** This suite is engineering retrievability. It is not RQ4 usefulness and not an RQ1 result.

## Required changes

None.

## Recommendation

Mark Complete. Remaining extras: live Guide e2e, RQ4 two-session protocol, TEST-002 n≥3 (stays on TEST-002).
