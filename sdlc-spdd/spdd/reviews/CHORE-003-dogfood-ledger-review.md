# Review: CHORE-003-dogfood-ledger

**Work ID:** CHORE-003-dogfood-ledger  
**Date:** 2026-09-06  
**Result:** Approved With Notes  

## Summary

T01 documents that archive never truncates `lessons.jsonl`, seeds decision/pitfall/pattern records through the ledger API (git history of the file was empty), and adds a structured CI checker plus an archive regression. RQ4 dogfood retrieve is no longer vacuous. This does **not** measure C-MEMORY usefulness.

## Proof

| Check | Result |
|-------|--------|
| Live ledger | parseable JSONL; decision + pitfall + pattern present |
| Retrieve | `--kind pitfall` returns ≥1 hit |
| Archive | ledger bytes unchanged after archiving a Complete work ID |
| Checker | empty / token-stub ledger fails |

## Findings

1. **Note:** Seed records are tagged `source: chore-003-restore`. They are program knowledge, not recovered M1 session captures.
2. **Safeguard:** A non-empty ledger is not RQ4 evidence. Usefulness remains C-REWORK on a follow-on session.

## Required changes

None.

## Recommendation

Mark Complete. Remaining P2: REF-001 (engine single-source).
