# Sync: REF-002-purge-pre-v3-compat

**Work ID:** REF-002-purge-pre-v3-compat  
**Date:** 2026-09-14  
**Readiness After Sync:** Complete  
**Status After Sync:** Complete  
**Pull Request:** https://github.com/jmjava/sdlc-spdd-orchestrator/pull/314  
**Merge Commit:** `06ddb23fefd8897da700a0c7e3d251fec36624df`

## What Changed

- Pre-v3 migration, consolidation, archive, registry, project-home, detect,
  and runtime fallback paths were removed.
- Storage v3 (`SDLC_HOME` or `<root>/sdlc-spdd`) is the only supported layout.
- Product docs and shipped copies describe only that layout.
- Unit, integration, E2E, research, live-consumer, and shell fixtures use
  explicit storage-v3 homes.
- Requirement, canvas, Milestone 3, and roadmap records now mark REF-002
  Complete.
- Review and sync artifacts now record the merged implementation and
  post-merge evidence.

## What Drifted

- T06 used focused `test_project_home.py` coverage and explicit fixture homes
  instead of introducing the planned shared `conftest.py` fixture.
- T07 included the remaining installer/runtime consumers and CI fixtures in
  addition to the planned documentation close-out.
- Implementation progress evidence and lifecycle close-out did not land in
  PR #314, so the initial post-merge review gate was blocked.

## What Was Reconciled

- Canvas operation descriptions and file maps now match the actual T02–T07
  commits.
- T08 explicitly owns post-merge review, retro, accepted lessons, and
  lifecycle documentation sync.
- All acceptance criteria and the full-suite review checkbox are complete.
- The requirement identifies PR #314 and its completion state.
- Milestone 3 and `ROADMAP.md` identify REF-002 as Complete and point to
  REF-003 as the next one-flow item.
- Dependent and blocking relationship tables identify REF-002 as Complete.
- Product/shipped documentation mirrors are byte-identical, and the stale
  migration/consolidation wording stop rule is clean.

## Review and Validation

- Review result: **Approved With Notes**.
- Merge-commit CI: **25/25 successful checks**; none running or failing.
- Operation-diff scope: PASS for merged implementation operations T02–T07.
- Operation-diff scope: PASS for documentation close-out operation T08.
- Requirement and canvas validators: PASS.
- Sync and retro lifecycle gates: PASS.

## Accepted Lessons

- `session:REF-002-purge-pre-v3-compat:scripts/lib:capture`
- `pitfall:REF-002-purge-pre-v3-compat:scripts/lib:capture`
- `pattern:REF-002-purge-pre-v3-compat:scripts/lib:capture`

The Guide projection was unavailable locally, but the resolved sync backend is
the normal file/on-demand mode. Per the sync contract, Guide absence is not a
failure. The ledger records were accepted and the derived context index was
regenerated.

## What Remains Incomplete

Nothing within REF-002. Milestone 3 remains active; REF-003 and later work IDs
retain their existing statuses.

## Follow-Up Tasks

1. Continue Milestone 3 with `REF-003-retire-bash-workflow-dual-path`.
2. Correct the framework command guidance that still shows positional
   `gate review` / `gate sync`; the current CLI requires `gate --phase ...`.
