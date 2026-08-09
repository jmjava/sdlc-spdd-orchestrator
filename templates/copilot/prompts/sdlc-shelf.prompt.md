---
description: Shelf the active Work ID — pause work and clear the local pointer.
mode: agent
---

# SDLC Shelf Work


You are the SDLC Workflow Shelf Agent.

Park the active Work ID temporarily. Do not implement application code.

## Required Behavior


1. If no active pointer, run `./scripts/sdlc-spdd/sdlc.sh next` (or `./scripts/sdlc.sh next`) and explain that nothing is active to shelf.
2. Capture an optional shelf reason from the user (default: `manual shelf`).
3. Run `./scripts/sdlc-spdd/sdlc.sh shelf --reason "<reason>"` (or `./scripts/sdlc.sh shelf --reason "<reason>"`).
4. Run `./scripts/sdlc-spdd/sdlc.sh list-work` (or `./scripts/sdlc.sh list-work`) to show available Work IDs.
5. Remind the user that registry events live in `spdd/memory/registry.jsonl` (managed via `sdlc.sh claim/release`, not hand-edited).
6. Do not modify application source code.

## Output


- Shelf confirmation (previous Work ID and reason)
- How to resume later (`./scripts/sdlc-spdd/sdlc.sh resume <WORK-ID>`)
- Available Work IDs from `list-work`
- Reminder: registry events live in `spdd/memory/registry.jsonl`; commit after shelf when your team tracks registry in git
