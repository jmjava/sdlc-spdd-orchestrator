---
work_id: "BUG-001-db-query-undefined-names"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Bug"
jira_status: "Done"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P0"
size: "S"
blocks: []
depends_on: 
  - "SPIKE-005-architecture-review"
related: 
  - "CHORE-004-lint-and-complexity-gates-real"
---

# BUG-001: Fix undefined names in db_query.py (export_sql NameError)

**Work ID:** BUG-001-db-query-undefined-names  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** Done  
**Priority / size:** P0 / S  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `SPIKE-005-architecture-review` | In Progress | See milestone-3 |
| Related | `CHORE-004-lint-and-complexity-gates-real` | To Do | See milestone-3 |

## User / Business Goal

`sdlc-engine db export` crashes with NameError because db_query.py references NODE_*/REL_* constants and _utc_now without importing them; CI never ran pyflakes' undefined-name check.

## Scope

### IN SCOPE

- Import the db_schema constants and timeutil.utc_now in db_query.py
- Regression tests: export_sql round-trip and context_linked_to_section on a seeded index
- Decide whether context_linked_to_section (no callers) stays; if kept, it must be tested

### NOT IN SCOPE

- Widening the lint gate (CHORE-004)
- SQLite schema changes

## Acceptance Criteria

- [x] `ruff check --select F821 engine/src` is clean
- [x] Unit test calls LocalIndex.export_sql on a temp project and asserts the dump header
- [x] Unit test exercises context_linked_to_section or the method is removed

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Bug
- Summary: Fix undefined names in db_query.py (export_sql NameError)
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

`sdlc-engine db export` crashes with NameError because db_query.py references NODE_*/REL_* constants and _utc_now without importing them; CI never ran pyflakes' undefined-name check.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Fix undefined names in db_query.py (export_sql NameError)
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/BUG-001-db-query-undefined-names.md
