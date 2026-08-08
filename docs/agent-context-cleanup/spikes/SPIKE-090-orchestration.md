# SPIKE-090: Persist fan-out + retrieve assemble

GitHub: [#90](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/90)  
Status: **implemented (fan-out + operator config)**

## Decision

Python `ContextStore` in `sdlc_engine/context_store.py`:

- `persist(event)` → git pointers / lean files (required), SQLite upsert (soft), Guide project (soft)  
- `retrieve(work_id=…, area=…)` → merge stay-set + SQLite + Guide  
- Backends gated by `.sdlc/persistence-config.json` or `CONTEXT_BACKENDS` (`sdlc_engine/persistence.py`)

CLI: `sdlc-engine context persist-lesson|persist-entry|retrieve|coverage|backends`  
Ops console: **Persistence** tab (`/api/persistence/status|save`)  
Bash: `scripts/resolve-context-backend.sh` reports `CONTEXT_BACKENDS=git-pointers,sqlite,guide-dice` (set).
