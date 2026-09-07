# Review: TEST-003-cretrieve-roundtrip

**Work ID:** TEST-003-cretrieve-roundtrip  
**Date:** 2026-09-07  
**Result:** Approved With Notes  
**Readiness at review:** Reviewed (coding of T01–T05 already on `main`)  
**Readiness after review:** Reviewed / Complete

## Summary

T01–T05 are on `main` (`e716100` / #259). The named hermetic suite covers ledger + SQLite + mocked Guide **client**. Live Guide+Neo4j is required graph-mode evidence (`test-guide-stack-experimental`). Context-select returns the matching subset, not sibling records. Guide-dice enabled + Guide down fails `context parity` (CLI exit 1); slash-command effect verification does not treat that as command-effects drift.

This review's **scope removed** drift (RQ1) and usefulness (RQ4). `embabel-dif` is out of this review. Mocked HTTP is not the graph-store proof.

## Proof

| Check | Result |
|-------|--------|
| Ledger | persist→`context retrieve` / `show` same id; T04 subset/sibling |
| SQLite | `context parity` missing/extra empty; `lessons_for_work` / `lessons_for_area` match subsets |
| Guide (mocked client) | `work_subgraph` parity missing empty |
| Guide (unreachable) | `ok: false`, `unreachable: true`, no `skipped`; CLI exit 1 |
| Guide (live Neo4j) | `test_guide_projection_roundtrip.py` + `test_context_store_guide_live.py` (`test_live_persist_enters_all_backends`, `test_live_context_selects_right_records`) |
| CI | `test-research-p0.yml` hermetic; `test-guide-stack-experimental.yml` graph mode |
| Spec pointer | DOC-001 names TEST-003 / `test_cretrieve` |

## Findings

1. **Note (process):** T05 landed while canvas Metadata still said In Progress and the T05 checklist was unchecked. Close-out is this review. Not a Ready For Coding violation for T01 (Reviewed before code).
2. **Note (system):** Operator/front-door docs still call live Guide optional or skip-on-unreachable. That is **not** a TEST-003 test gap; it is freeze-honesty drift. See `academic-freeze-system-review.md`.
3. **Safeguard:** This review's scope **removed** drift and usefulness. `embabel-dif` is out of this review.

## Required changes

None on TEST-003 operations.

## Optional improvements

Tracked as the system review list (front-door docs, P0 coverage, persist vs parity, console copy).

## Test gaps

None on the TEST-003 bar. Live graph cannot be re-run on a Docker-less agent VM; CI `guide-neo4j-live` on #259 was green.

## Drift from canvas

Requirement and canvas T04/T05 checkboxes were stale vs `main`. Corrected in this close-out.

## Recommended next command

`/sdlc-spdd-sync` is done by this close-out. Do not open a new Work ID unless the human picks an item from `academic-freeze-system-review.md`.
