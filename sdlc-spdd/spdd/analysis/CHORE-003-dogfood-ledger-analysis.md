# Analysis: CHORE-003 — Keep committed decision memory after archive

## Metadata

- Work ID: CHORE-003-dogfood-ledger
- Date: 2026-09-06
- Depends on: SPIKE-004 (program plan); TEST-002 merged (`3b1719c` / PR #236)
- Constructs: C-MEMORY (dogfood retrieve precondition)

## Scope Lock

### In Scope

- Policy: archive moves/removes contracts; it never truncates `lessons.jsonl`
- Seed a minimal committed ledger (decision + pitfall + pattern) because git history of the file is empty (always 0 bytes since storage v3)
- Document the policy in storage-v3 / runtime-and-ledger
- CI that fails if the dogfood ledger is emptied without those kinds

### NOT in Scope

- Re-adding archived Milestone 1 canvases to the working tree
- Changing which Complete work IDs may archive their contracts
- RQ4 two-session usefulness eval (still TEST-001 protocol; this ID only makes retrieve non-vacuous)
- Embabel upstream
- REF-001 (dual engine)

## Recommendation

Git cannot restore Milestone 1 lessons — `sdlc-spdd/spdd/memory/lessons.jsonl` has been 0 bytes since it was introduced. Seed via `LessonsLedger.append_accepted` (not a hand-typed JSONL edit). Archive already does not open the ledger; make that an explicit leave-in-place guarantee plus a regression test.
