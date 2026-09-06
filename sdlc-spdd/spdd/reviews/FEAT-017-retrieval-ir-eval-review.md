# Review: FEAT-017-retrieval-ir-eval

**Work ID:** FEAT-017-retrieval-ir-eval  
**Date:** 2026-09-06  
**Result:** Approved With Notes  

## Summary

T01 documents retrieve as two lexical algorithms, adds `--query` title-body ranking, and commits a qrel fixture where exact keyword-list membership misses the relevant pitfall while title-body ranks it first (`precision@1 = 1`). DICE/Guide embeddings are explicitly unmeasured.

## Proof

| Check | Result |
|-------|--------|
| keyword-list precision@1 on fixture | 0 |
| title-body rank-1 id | qrel pitfall |
| title-body precision@1 | 1 |
| `dice_measured` | false |
| Algorithm doc | `sdlc-spdd/docs/research/retrieve-algorithm.md` |

## Findings

1. **Note:** SQLite FTS (`db query --search`) remains a different CLI, not this retrieve path.
2. **Safeguards:** No Neo4j, no Embabel upstream, no DICE-as-result language.

## Required changes

None.

## Recommendation

Mark Complete. Next P2 item is TEST-002 (behavioral slice), not started here.
