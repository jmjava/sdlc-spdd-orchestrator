---
work_id: "TEST-003-cretrieve-roundtrip"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Test"
jira_status: "Complete"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks: []
depends_on:
  - "DOC-001-research-questions-and-constructs"
  - "CHORE-003-dogfood-ledger"
  - "FEAT-017-retrieval-ir-eval"
related:
  - "FEAT-015-first-class-metrics"
---

# TEST-003: C-RETRIEVE round-trip suite

**Work ID:** TEST-003-cretrieve-roundtrip  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** In Progress (T04 context-select)  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Depends On | `DOC-001-research-questions-and-constructs` | Complete | C-RETRIEVE is the academic-review claim |
| Depends On | `CHORE-003-dogfood-ledger` | Complete | Live ledger still non-vacuous |
| Depends On | `FEAT-017-retrieval-ir-eval` | Complete | Lexical retrieve algorithm |
| Related | `FEAT-015-first-class-metrics` | Complete | Queryable metrics |

## User / Business Goal

One CI-backed test suite a referee can run for the frozen claim: stored advice is retrievable from **three storage modes** — git ledger, SQLite, and live Guide/Neo4j graph. Hermetic TEST-003 covers ledger + SQLite + mocked Guide **client**. Live e2e covers the graph.

## Scope

### IN SCOPE

- [x] Persist/accept then find the same lesson id on the git ledger (`context retrieve` / `context show`)
- [ ] T04: retrieve context (work / area / kind / query) returns the matching subset and excludes sibling records; live `work_subgraph` vs `area_lessons` agree
- SQLite enabled: `context parity` missing/extra empty; retrieve `sqlite_graph` includes the id
- Guide enabled: mocked HTTP so CI always exercises the **client** parity success (not only unreachable-skip). This is **not** the graph-store proof.
- [x] Live Guide+Neo4j persist→read (`test_guide_projection_roundtrip.py`, `test_context_store_guide_live.py`) as **required** graph-mode evidence
- [ ] T04 live `test_live_context_selects_right_records` (work vs area context)
- Document what this suite does **not** prove

### NOT IN SCOPE (this review's scope **removed** drift and usefulness)

- RQ4 usefulness / C-MEMORY follow-on rework — **removed from this review**
- Guide embeddings / DICE IR
- RQ1 drift — **removed from this review**
- Re-implementing live Guide+Neo4j from scratch (already in `test_guide_projection_roundtrip.py` / `test-guide-stack-experimental`; T02 strengthens the triple-backend assertions)
- `embabel-dif` (removed from this review; later / other-repo)

## Acceptance Criteria

- [x] `python3 -m unittest tests.research.test_cretrieve -v` is the named suite
- [x] Ledger, SQLite, and mocked-Guide round-trips all fail if the stored id cannot be read back
- [ ] T04 context-select: matching subset, not sibling records
- [x] Research CI runs the suite
- [x] A short research note states non-claims

## Non-Goals

- Expanding product surface
- Upstream PRs to embabel/guide
- Opening a SPIKE

## Next Step

T04 context-select (non-trivial retrieve). Drift and usefulness remain **removed from this review's scope**.
