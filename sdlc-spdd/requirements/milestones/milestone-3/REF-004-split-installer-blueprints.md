---
work_id: "REF-004-split-installer-blueprints"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Refactor"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P1"
size: "M"
blocks: []
depends_on: 
  - "CHORE-004-lint-and-complexity-gates-real"
related: 
  - "REF-008-console-viewer-hardening"
---

# REF-004: Split installer/app.py create_app into Flask blueprints

**Work ID:** REF-004-split-installer-blueprints  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P1 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `CHORE-004-lint-and-complexity-gates-real` | To Do | See milestone-3 |
| Related | `REF-008-console-viewer-hardening` | To Do | See milestone-3 |

## User / Business Goal

create_app is one 1 056-line nested function holding every /api/* route; routes cannot be tested or reviewed in isolation.

## Scope

### IN SCOPE

- One blueprint per console tab (install, persistence, sqlite, guide, issues, adf, templates, dashboard, rollback)
- Shared request/response helpers; SystemExit on missing Flask becomes an ImportError with a hint
- Remove no-op wrapper aliases at installer/app.py:88–119

### NOT IN SCOPE

- Changing API payloads the Vue3 console depends on
- Viewer app (REF-009)

## Acceptance Criteria

- [ ] No function in installer/ exceeds 80 NLOC or CCN 10 (lizard)
- [ ] Integration suite and Vue3 Playwright pass unchanged
- [ ] installer coverage gate stays ≥ 90 %

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Split installer/app.py create_app into Flask blueprints
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

create_app is one 1 056-line nested function holding every /api/* route; routes cannot be tested or reviewed in isolation.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Split installer/app.py create_app into Flask blueprints
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-004-split-installer-blueprints.md
