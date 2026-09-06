# Review: DOC-003-replication-package

**Work ID:** DOC-003-replication-package  
**Date:** 2026-09-06  
**Result:** Approved With Notes  

## Summary

T01 commits a threats-to-validity and replication pack that cites every DOC-001 construct, freezes engine SHA/version/gold paths/commands, restates TEST-001’s chat nondeterminism rule (n≥3 or protocol incomplete), and states that live-consumer jobs do not prove C-DRIFT. Structured checker tests fail a token stub.

## Proof

| Check | Result |
|-------|--------|
| Construct section cites C-DRIFT..C-PORT | required by checker |
| Replication table with freeze + command columns | ≥4 non-stub rows |
| Gold path `tests/live-consumer/seed/src/hello.py` | named and exists |
| TEST-001 n≥3 / protocol incomplete | restated |
| Token stub | fails |
| `prove-p0.sh DOC-003` | must pass |

## Findings

1. **Note:** This pack still collects no study data. TEST-002 owns execution.
2. **Safeguards:** Guide remains optional and fork-only. No Embabel upstream.

## Required changes

None.

## Recommendation

Mark Complete. P1 of Milestone 2 is done. Next is P2 (FEAT-017 or TEST-002), not started here.
