# SPIKE-083: Lean-git lessons learned

GitHub: [#83](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/83)  
Status: **implemented** (lean persist via `ContextStore.persist_lesson` → `spdd/memory/lessons/*` + index row + pointer)

## Decision

Accepted lessons live in the **stay-set** under `spdd/memory/`:

| File | Role |
|------|------|
| `spdd/memory/lessons/decisions.md` | Decision bodies |
| `spdd/memory/lessons/pitfalls.md` | Pitfall bodies |
| `spdd/memory/lessons/patterns.md` | Pattern bodies |
| `spdd/memory/context-index.md` | Area × Kind index (decision/pitfall/pattern only in committed form) |
| `spdd/memory/pointers.jsonl` | Lean provenance (#87) |

Hot Kind=session/metric rows stay in SQLite (and optionally Guide), **not** the committed index.

## Accept flow

1. Capture may stage drafts under `.sdlc/`  
2. Retro/sync **accept** appends lean lesson file + index row + pointer line  
3. Fan-out upserts SQLite lesson row + Guide re-project (#90)

## IDs

Keep Guide-compatible: `{kind}:{workId}:{area}:{source}`

## Legacy

`agent-context/memory/*` exported by upgrade (#80); Guide loader accepts both roots during transition (#89).
