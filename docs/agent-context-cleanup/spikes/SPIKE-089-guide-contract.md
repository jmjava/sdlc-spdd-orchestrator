# SPIKE-089: Guide projection contract

GitHub: [#89](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/89)  
Status: **complete on both sides** — orchestrator dual-write shipped; Guide dual-read merged on `jmjava/guide`

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
| Orchestrator dual-write (lean + legacy context-index) | `main` / PR [#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109) / tag `v2.0.0a6` | shipped |
| Guide dual-read (`SpddMarkdownProjectionService.load`) | `jmjava/guide` `main` via [PR #7](https://github.com/jmjava/guide/pull/7) (`28bdb5d`) | **merged** |
| Dogfood pin | tag `sdlc-spdd-projection-v2` @ `28bdb5d` | **current** (supersedes `sdlc-spdd-projection-v1`) |

Tag `sdlc-spdd-projection-v1` still reads only the legacy
`agent-context/memory/context-index.md`. Prefer `sdlc-spdd-projection-v2` (or
`main`) so Guide dual-reads the lean stay-set without relying on dual-write alone.

Hard rule: never PR/push/merge to `embabel/guide`; dogfood uses the `jmjava/guide` fork only.
