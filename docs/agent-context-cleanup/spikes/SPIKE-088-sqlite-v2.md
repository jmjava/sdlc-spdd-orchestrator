# SPIKE-088: SQLite relational graph (now schema v4)

GitHub: [#88](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/88)  
Status: **implemented (schema v4) — required before main**

## Decision

`SCHEMA_VERSION` is `4`. The index is the full agent-context graph, not a filename cache and not lessons-only.

### Section nodes (stay in git)

- `requirements` — `requirements/milestones/<WORK-ID>.md`
- `canvases` — REASONS `spdd/canvas/<WORK-ID>.md`

### Context-part nodes

- `areas`, `lessons`, `claims`, `context_sessions`, `pointers`
- `context_entries` — analysis, review, sync, retro, progress, metric, session, memory, prompt, playbook, harness, extension, mirrors, phase_ref, …
- `domain_keywords`, `phase_refs`, `project_facts`
- Convenience join `work_areas`

### Typed edges

work→requirement, work→canvas, requirement→reasons→canvas,  
work|requirement|canvas|entry→area, lesson|entry→about→area|requirement|canvas,  
lesson→recorded_for→work, claim|session|pointer|entry→for_work→work,  
keyword→about→area|entry

### Coverage gate

`LocalIndex.capability_coverage()` must report `complete: true` when the tree includes every kind in `context_model.CONTEXT_KINDS`. Tests: `engine/tests/test_db_graph_v4.py`.

Rebuild ingests stay-set governance, legacy feature mirrors, context/domain/phase indexes, sessions, playbooks/harness/extensions, and memory ledgers.
