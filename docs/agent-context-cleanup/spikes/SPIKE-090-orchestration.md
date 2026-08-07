# SPIKE-090: Persist fan-out + retrieve assemble

GitHub: [#90](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/90)  
Status: **proposal accepted for implementation**

## Decision

Python `ContextStore` in `sdlc_engine/context_store.py`:

- `persist(event)` → git pointers / lean files (required), SQLite upsert (soft), Guide project (soft)  
- `retrieve(work_id=…, area=…)` → merge stay-set + SQLite + Guide  

CLI: `sdlc-engine context sync|status|retrieve`  
Bash: `scripts/resolve-context-backend.sh` reports `CONTEXT_BACKENDS=git-pointers,sqlite,guide-dice` (set).  
Capture hooks call `context sync` best-effort at end.
