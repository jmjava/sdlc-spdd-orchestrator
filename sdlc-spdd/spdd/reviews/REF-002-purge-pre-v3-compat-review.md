# Review: REF-002-purge-pre-v3-compat

**Work ID:** REF-002-purge-pre-v3-compat  
**Date:** 2026-09-14  
**Result:** Approved With Notes  
**Pull Request:** https://github.com/jmjava/sdlc-spdd-orchestrator/pull/314  
**Merge Commit:** `06ddb23fefd8897da700a0c7e3d251fec36624df`

## Summary

PR #314 implements the approved storage-v3-only contract. Pre-v3 migration,
consolidation, archive, registry, project-home, detect, and runtime fallbacks
are removed. Operator docs and shipped copies describe the same v3-only
behavior. The implementation satisfies all seven behavioral operations; T08
closes the post-merge lifecycle records.

Readiness was **Ready For Coding** when implementation began. Coding did not
proceed ahead of the architecture gate. Readiness is **Complete** after review
and sync.

## Proof

| Check | Result |
|-------|--------|
| PR state | #314 merged as `06ddb23` |
| Merge-commit CI | 25/25 check runs completed successfully |
| Unit tests reported by implementation PR | 284 passed |
| Integration tests reported by implementation PR | 128 passed |
| Research tests reported by implementation PR | 87 passed |
| Playwright reported by implementation PR | 29 passed, 1 skipped |
| Product/shipped doc mirrors | Byte-identical for every touched mirrored document |
| Legacy wording stop rule | No `storage migrate`, `legacy-layout-archive`, or `consolidat` hits in current operator docs |
| Operation-diff scope | PASS for implementation operations T02–T07 |
| Requirement/canvas validators | PASS |

T01's archive-delete contract landed earlier in #308 and was already recorded
Complete in the canvas. T02–T07 landed together in #314.

## Findings

1. **Canvas/intent mismatch, reconciled:** T06 used focused
   `test_project_home.py` coverage plus explicit storage-v3 homes instead of
   the planned shared `conftest.py` fixture. This changes test structure, not
   the approved behavior.
2. **Canvas/intent mismatch, reconciled:** T07 expanded from documentation
   close-out to remaining installer/runtime consumers and CI fixtures. These
   changes enforce the same strict-home contract and are now reflected in the
   operation description and file map.
3. **Process note:** implementation progress had not been captured in the
   lessons ledger, which initially blocked the review gate. A passing
   merge-commit CI receipt was captured before this review.
4. **Process note:** PR #314 merged before the requirement, canvas, milestone,
   roadmap, review, and sync artifacts were closed. T08 performs that
   reconciliation.

## Required Changes

None. The documentation-only T08 close-out resolves the identified lifecycle
drift.

## Safeguards

- `lessons.jsonl` was not truncated or hand-edited; close-out records use the
  capture/accept workflow.
- `registry.jsonl` changes came from lifecycle claim/release commands.
- The v3 rollback path and `SDLC_HOME` override remain.
- The bash workflow twin remains for REF-003; REF-002 only removes its
  pre-v3 paths.
- No Embabel upstream work was created or proposed.

## Optional Improvements

The command guidance examples use the older positional `gate review` form
while the current CLI requires `gate --phase review`. That framework-wide
documentation issue is outside REF-002 and should be handled separately.

## Test Gaps

No acceptance-level gap remains. The PR checklist's manual assistant chat smoke
was not run, but REF-002 changes storage paths rather than assistant UI
interaction; the unit, integration, shell, live-consumer, E2E, and post-merge
CI evidence covers the changed behavior.

## Drift From Canvas

The T06 fixture strategy and T07 runtime/fixture expansion are the only
material drift. Both are non-behavioral or stricter implementations of the
approved v3-only contract. Operation file lists now match the merged commits,
and the machine scope check passes.

## Recommendation

Approve, accept the staged close-out lessons, synchronize all lifecycle
records, and continue Milestone 3 with
`REF-003-retire-bash-workflow-dual-path`.
