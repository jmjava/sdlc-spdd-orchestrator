# SPIKE-088: SQLite schema v2 (relational graph)

GitHub: [#88](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/88)  
Status: **proposal accepted for implementation**

## Decision

Bump `SCHEMA_VERSION` to `2`. Keep regenerable rebuild of `work_items` / `artifacts`, and add relational graph tables:

- `lessons` (id, kind, work_id, area, body, source, ts)  
- `work_areas` (work_id, area)  
- `claims` (id, work_id, owner, status, phase, note, ts)  
- `context_sessions` (id, work_id, phase, path, summary, ts)  
- `pointers` (id, kind, work_id, commit_sha, intent, payload_json, ts)  

Upsert APIs support capture fan-out without requiring a full rebuild for lesson/claim/session rows. Rebuild still refreshes work_items from stay-set + registry.
