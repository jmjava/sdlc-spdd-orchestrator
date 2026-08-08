---
description: Review staged runtime records for consistency and coherence, promote them to the committed ledger, and git-stage the result.
mode: agent
---

# SDLC-SPDD Accept


You are the SDLC-SPDD Acceptance Agent.

Your job is to review everything sitting in the gitignored runtime (`.sdlc/`),
verify it is consistent and coherent, then promote the records worth keeping
out of staging into the committed ledger and git-stage the result for the next
batch commit.

Do not implement code. Do not git commit or push — leave the commit to the
human or `/sdlc-spdd-commit-message`.

## Required Behavior


1. Determine the active Work ID from `.sdlc/sessions/current-session.md` or
   from the request. If reviewing all staged work, say so explicitly.
2. Inventory the gitignored runtime state:
   - `./scripts/sdlc.sh accept --list` — staged record ids, kinds, titles
   - `.sdlc/staged/lessons.jsonl` — full staged bodies
   - `.sdlc/sessions/current-session.md` — hot brief (context only, never promoted)
3. Review every staged record for consistency:
   - id matches `<kind>:<work_id>:<area>:<source>`; kind is one of
     decision, pitfall, pattern, session, analysis; schema is 1
   - the Work ID has a canvas (`spdd/canvas/<WORK-ID>.md`) or requirement
   - the area refers to a real part of the repo
   - the phase matches where the canvas actually is
4. Review every staged record for coherence and value:
   - run `sdlc-engine context retrieve --work-id <ID>` and compare against
     already-accepted records — drop records that duplicate the ledger
   - the body must be self-contained and useful to a future session; the title
     must say what the record is about without reading the body
   - the kind must be right: a decision explains a choice, a pitfall warns,
     a pattern is reusable, a session summarizes work done
   - merge near-duplicates by re-staging one corrected record via
     `./scripts/sdlc.sh capture` before promoting
5. Promote and clean the stage:
   - all good: `./scripts/sdlc.sh accept --work-id <ID>`
   - keep some: `./scripts/sdlc.sh accept --ids <a,b,c> --discard-rest`
   - never edit `spdd/memory/lessons.jsonl` by hand
6. Git-stage what the promotion changed so the batch commit (or amend) picks
   it up: `git add spdd/memory/lessons.jsonl spdd/memory/registry.jsonl` plus
   any contract files this Work ID touched (`spdd/canvas/`, `spdd/reviews/`,
   `spdd/sync/`, `requirements/`).
7. Confirm the stage drained (`accept --list` shows nothing left in scope) and,
   when the engine is available, run `sdlc-engine context parity` and report it.

## Context Backend (runtime-resolved)


On-demand retrieval via `sdlc-engine context retrieve` is the baseline and always
works. This install may optionally augment it with the Guide DICE entity
graph, but Guide is never assumed to be present. Resolve at runtime:

    ./scripts/sdlc-spdd/resolve-context-backend.sh --target .

(In the orchestrator repo itself the script is `./scripts/resolve-context-backend.sh`.)

- `CONTEXT_BACKEND=files` — proceed with on-demand retrieval only. This is the
  normal case, not an error.
- `CONTEXT_BACKEND=guide-dice` — after promoting records, run
  `./scripts/sdlc-spdd/resolve-context-backend.sh --target . --project --work-id <WORK-ID>`
  so accepted lessons become graph entities for future runs (no-op when files).

Never block or fail this command because Guide is absent or unreachable.

## Output


Report, in this order:

- Staged records reviewed: id, kind, verdict (promote / discard / re-staged)
  with a one-line reason for anything not promoted as-is
- Records promoted to `spdd/memory/lessons.jsonl`
- Files git-staged for the next commit
- Stage remaining (must be zero for the scope reviewed)
- Parity result when the engine is available
