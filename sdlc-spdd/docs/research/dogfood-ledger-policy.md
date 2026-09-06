# Dogfood ledger policy (CHORE-003)

**Work ID:** CHORE-003-dogfood-ledger  
**Construct:** C-MEMORY (precondition — memory exists to retrieve)

This is the **archive-vs-ledger** rule for this orchestrator. It is not an RQ4 result.

## What survives archive

`sdlc.sh archive` / `ArchiveService.archive_work` may move or delete **contracts** for a Complete or Cancelled Work ID:

- `spdd/canvas/<WORK-ID>.md` (and analysis / review / sync sidecars)
- matching session briefs under `.sdlc/sessions/` (not `current-session.md`)
- workflow state files

Git history retains those files. Requirements stay in the working tree.

Archive **must not** truncate, filter, rewrite, or delete:

- `spdd/memory/lessons.jsonl` (committed lessons — all kinds)
- `spdd/memory/registry.jsonl` except for the append-only archived event

Lesson kinds `decision`, `pitfall`, `pattern`, `session`, and `analysis` all survive. The dogfood minimum for C-MEMORY retrieve is at least one **decision**, one **pitfall**, and one **pattern** with a real body.

## Why a seed was required

`sdlc-spdd/spdd/memory/lessons.jsonl` has been **0 bytes** since storage v3 introduced it. There is nothing in git history to restore. CHORE-003 therefore **seeded** records through `LessonsLedger.append_accepted` (not a hand-typed JSONL edit), tagged `source: chore-003-restore`.

A non-empty ledger makes dogfood `context retrieve` non-vacuous. It does **not** prove that retrieved lessons reduce C-REWORK on a follow-on task (TEST-001 RQ4).

## CI

`python3 -m unittest tests.research.test_chore003_ledger -v` fails if the live ledger is missing, empty, unparseable, or lacks the three required kinds with non-stub bodies.
