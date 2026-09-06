# REASONS Canvas: CHORE-003-dogfood-ledger — Dogfood lessons survive archive

## Metadata

- Work ID: CHORE-003-dogfood-ledger
- Work Type: Chore
- Status: Complete
- Readiness: Reviewed
- Created: 2026-09-06
- Updated: 2026-09-06
- Milestone: milestone-2
- Depends on: SPIKE-004-academic-contribution-bar
- Related: FEAT-015-first-class-metrics, TEST-002-assistant-behavior-eval
- Requirement: `sdlc-spdd/requirements/milestones/milestone-2/CHORE-003-dogfood-ledger.md`
- Analysis: `sdlc-spdd/spdd/analysis/CHORE-003-dogfood-ledger-analysis.md`
- Beck stage: make it right (C-MEMORY dogfood precondition)

## R - Requirements

### User Goal

Archive must not leave the orchestrator's lessons ledger empty. A methods project that deletes its own decision memory cannot claim reusable learning.

### Business / Product Goal

RQ4 dogfood retrieve is no longer vacuous: the working tree has decision, pitfall, and pattern records, and archive is documented not to wipe them.

### Acceptance Criteria

- [x] Working tree has a non-empty lessons.jsonl with at least decision/pitfall/pattern records, or a documented exception
- [x] Archive procedure no longer implies 'no memory left'
- [x] A test or check fails CI if dogfood ledger is accidentally deleted without policy

### Non-Goals

- Restoring archived canvases
- Changing archive of Complete work IDs' contracts
- Claiming C-MEMORY usefulness (RQ4 two-session still unrun)
- Embabel upstream

## E - Entities

- Committed lessons ledger (`sdlc-spdd/spdd/memory/lessons.jsonl`)
- Archive leave-ledger policy
- Seed records (decision / pitfall / pattern)
- CI checker

### Files likely affected

- `sdlc-spdd/spdd/memory/lessons.jsonl`
- `engine/src/sdlc_engine/archive.py`
- `templates/agent-context/sdlc-team-registry.sh`
- `sdlc-spdd/docs/storage-v3.md`
- `sdlc-spdd/docs/runtime-and-ledger.md`

## A - Approach

Write policy. Seed via `LessonsLedger.append_accepted` from a fixture (git history of the ledger is empty). Print that archive leaves the ledger in place. Add a structured checker plus an archive regression that the ledger bytes do not change.

## S - Structure

### Files to add

- `sdlc-spdd/docs/research/dogfood-ledger-policy.md`
- `sdlc-spdd/docs/research/check_dogfood_ledger.py`
- `tests/research/test_chore003_ledger.py`
- `tests/research/fixtures/chore003_dogfood_seed.json`

### Files to modify

- archive.py and shell archive
- storage-v3 + runtime-and-ledger (both doc copies)
- MILESTONE-2 / ROADMAP / CHANGELOG

### Test structure

- Empty / token-stub ledger fails the checker
- Live ledger has decision, pitfall, and pattern with real bodies
- Archive of a Complete work ID leaves ledger content unchanged
- `context retrieve --kind pitfall` returns at least one hit on the live ledger

## O - Operations

### T01 - Policy, seed, archive leave-ledger, CI

- Status: Complete
- Description: Document archive-vs-ledger policy; seed decision/pitfall/pattern via the ledger API; make archive print and test that lessons.jsonl is untouched; fail CI on an empty dogfood ledger.
- Files: `sdlc-spdd/spdd/memory/lessons.jsonl`, `engine/src/sdlc_engine/archive.py`, `templates/agent-context/sdlc-team-registry.sh`, `sdlc-spdd/scripts/sdlc-team-registry.sh`, `sdlc-spdd/docs/storage-v3.md`, `docs/storage-v3.md`, `sdlc-spdd/docs/runtime-and-ledger.md`, `docs/runtime-and-ledger.md`, `sdlc-spdd/docs/research/dogfood-ledger-policy.md`, `sdlc-spdd/docs/research/check_dogfood_ledger.py`, `tests/research/test_chore003_ledger.py`, `tests/research/fixtures/chore003_dogfood_seed.json`, `tests/test-archive-work.sh`
- Tests: `python3 -m unittest tests.research.test_chore003_ledger -v`
- Validation: live ledger parses; retrieve pitfall hits; archive regression keeps ledger bytes

## N - Norms

- Cite C-MEMORY
- One operation
- Never hand-edit lessons.jsonl — write through LessonRecord / append_accepted
- Do not claim RQ4 usefulness from a non-empty file

## S - Safeguards

- No Embabel upstream
- Do not restore archived canvases
- Seed records are restore-tagged (`source: chore-003-restore`), not invented M1 session logs
- Python `gate_check` remains the research SUT until REF-001

## Review Checklist

- [x] Non-empty ledger with required kinds
- [x] Archive leave-ledger documented and tested
- [x] Empty/token stub fails CI checker
- [x] Retrieve is non-vacuous for at least one pitfall

## Sync Notes

Follows merged TEST-002 (`3b1719c` / PR #236). Git history cannot restore M1 lessons (file always 0 bytes).

## Final Status

- Readiness: Reviewed
- Status: Complete
