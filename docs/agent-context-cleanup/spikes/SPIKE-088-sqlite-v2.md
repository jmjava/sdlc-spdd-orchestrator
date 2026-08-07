# SPIKE-088: SQLite schema (relational graph → full section graph)

GitHub: [#88](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/88)  
Status: **implemented (schema v3)**

## Decision

`SCHEMA_VERSION` is `3`. Keep regenerable rebuild of `work_items` / `artifacts`, and model the **entire stay-set + context graph**:

### Section nodes (stay in git)

- `requirements` — `requirements/milestones/<WORK-ID>.md`
- `canvases` — REASONS `spdd/canvas/<WORK-ID>.md`

### Context-part nodes

- `areas`, `lessons`, `claims`, `context_sessions`, `pointers`
- Convenience join `work_areas` (work↔area) kept for fast queries

### Typed edges (`edges` table)

| Edge | Meaning |
|------|---------|
| work —`requirement`→ requirement | Work has requirement section |
| work —`canvas`→ canvas | Work has REASONS canvas |
| requirement —`reasons`→ canvas | Requirement linked to REASONS |
| work\|requirement\|canvas —`area`→ area | Sections linked to context areas |
| lesson —`about`→ area\|requirement\|canvas | Lesson about context / sections |
| lesson —`recorded_for`→ work | Lesson recorded for work |
| claim\|session\|pointer —`for_work`→ work | Hot-path context parts |

Upsert APIs (`upsert_requirement`, `upsert_canvas`, `upsert_lesson`, `sync_stay_set`, …) support capture fan-out without a full rebuild. Rebuild refreshes work_items **and** requirement/canvas nodes + stay-set edges from disk.

## Prior step

v2 added lessons/areas/claims/sessions/pointers only. v3 adds first-class requirements, REASONS canvases, `areas` nodes, and the typed `edges` table so requirement↔REASONS↔context is queryable (`graph_for_work`, `context_linked_to_section`).
