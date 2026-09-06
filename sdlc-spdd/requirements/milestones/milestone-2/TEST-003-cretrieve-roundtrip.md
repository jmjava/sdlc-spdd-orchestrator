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
**Status:** Complete  
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

One CI-backed test suite a referee can run for the frozen claim: stored advice is retrievable from the ledger and, when enabled, from SQLite and Guide projections.

## Scope

### IN SCOPE

- Persist/accept then find the same lesson id on the git ledger (`context retrieve` / `context show`)
- SQLite enabled: `context parity` missing/extra empty; retrieve `sqlite_graph` includes the id
- Guide enabled: mocked HTTP so CI always exercises parity success (not only unreachable-skip)
- Document what this suite does **not** prove

### NOT IN SCOPE (this review's scope **removed** drift and usefulness)

- RQ4 usefulness / C-MEMORY follow-on rework — **removed from this review**
- Guide embeddings / DICE IR
- RQ1 drift — **removed from this review**
- Re-implementing live Guide+Neo4j (already in `test_guide_projection_roundtrip.py` / `test-guide-stack-experimental`)
- `embabel-dif` (removed from this review; later / other-repo)

## Acceptance Criteria

- [x] `python3 -m unittest tests.research.test_cretrieve -v` is the named suite
- [x] Ledger, SQLite, and mocked-Guide round-trips all fail if the stored id cannot be read back
- [x] Research CI runs the suite
- [x] A short research note states non-claims

## Non-Goals

- Expanding product surface
- Upstream PRs to embabel/guide
- Opening a SPIKE

## Next Step

None. T01 Complete. Live Guide+Neo4j e2e already exists. Drift and usefulness were **removed from this review's scope**.
