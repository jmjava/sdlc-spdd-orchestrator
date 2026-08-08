# SPIKE-089: Guide projection contract

GitHub: [#89](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/89)  
Status: **orchestrator side shipped (dual-write); Guide dual-read pending merge on `jmjava/guide`**

## Decision

Projection roots include:

1. `spdd/canvas/*.md` (unchanged)  
2. `spdd/memory/context-index.md` (**preferred** lean index)  
3. `agent-context/memory/context-index.md` (**legacy** fallback / merge)

Guide `SpddMarkdownProjectionService.load` reads both when present and dedupes lesson ids.  
Orchestrator still dual-writes during transition.

## Rollout state

| Side | Where | State |
|------|-------|-------|
| Orchestrator dual-write (lean + legacy context-index) | integration branch / PR [#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109) | shipped |
| Guide dual-read (`SpddMarkdownProjectionService.load`) | `jmjava/guide` branch `cursor/spdd-dual-context-index-decf` | implemented, **not merged** to `jmjava/guide` `main` or the tag |

Tag `sdlc-spdd-projection-v1` still reads only the legacy `agent-context/memory/context-index.md`.
That keeps working because the orchestrator dual-writes both indexes, and Guide is
optional/soft-fail — so the pending Guide merge does **not** block orchestrator PR #109.

Hard rule: never PR/push/merge to `embabel/guide`; dogfood uses the `jmjava/guide` fork only.
