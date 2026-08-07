# SPIKE-089: Guide projection contract

GitHub: [#89](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/89)  
Status: **proposal accepted for implementation**

## Decision

During transition, projection roots include:

1. `spdd/canvas/*.md` (unchanged)  
2. `spdd/memory/context-index.md` (**preferred** lean index)  
3. `agent-context/memory/context-index.md` (**legacy** fallback)

Orchestrator fan-out calls existing `POST …/spdd-projection/load` with repo root (Guide scans both index paths once loader is updated; until Guide ships dual-read, orchestrator may copy/symlink lean index into legacy path on project — avoid when possible).

Chunk ingest (leg 2) remains a separate optional step from entity project (leg 3).
