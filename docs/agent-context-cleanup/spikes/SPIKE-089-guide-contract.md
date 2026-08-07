# SPIKE-089: Guide projection contract

GitHub: [#89](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/89)  
Status: **implemented (dual-read in jmjava/guide)**

## Decision

Projection roots include:

1. `spdd/canvas/*.md` (unchanged)  
2. `spdd/memory/context-index.md` (**preferred** lean index)  
3. `agent-context/memory/context-index.md` (**legacy** fallback / merge)

Guide `SpddMarkdownProjectionService.load` reads both when present and dedupes lesson ids.  
Orchestrator still dual-writes during transition.
