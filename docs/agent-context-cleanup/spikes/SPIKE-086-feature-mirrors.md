# SPIKE-086: Eliminate agent-context/features mirrors

GitHub: [#86](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/86)  
Status: **implemented (stop new writes + archive path)**

## Decision

Canonical only:

- `requirements/…`  
- `spdd/canvas/…` (+ analysis/review/sync)  
- Lean ledgers under `spdd/memory/entries/`

`ContextStore.persist_context_entry` no longer appends feature mirrors.  
Upgrade (#80) archives `agent-context/features/` under `.sdlc/legacy-export/`.  
Rebuild still ingests existing mirrors as transitional `*_mirror` kinds until archived.
