---
work_id: "CHORE-009-release-version-hygiene"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Chore"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-4"
priority: "P1"
size: "S"
blocks: []
depends_on: 
  - "SPIKE-005-architecture-review"
related: []
---

# CHORE-009: One version string, current README focus, dated CHANGELOG

**Work ID:** CHORE-009-release-version-hygiene  
**Milestone:** Milestone 4 — Documentation truth and release hygiene  
**Status:** To Do  
**Priority / size:** P1 / S  
**Date:** 2026-09-13  
**Beck stage:** make it right (docs)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `SPIKE-005-architecture-review` | In Progress | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

Tags v2.0.0a7/a8 exist while pyproject, __init__, README, and a test pin 2.0.0a6; README Current focus cites past PRs as present; ROADMAP links archived canvases.

## Scope

### IN SCOPE

- Version read from one place (pyproject) by __init__ and README badge check
- Release checklist in CONTRIBUTING (tag ↔ version ↔ CHANGELOG)
- README Current focus points at ROADMAP instead of PR lists; ROADMAP drops dead canvas links

### NOT IN SCOPE

- Cutting a release (human decision)

## Acceptance Criteria

- [ ] test_engine_shared asserts __version__ == pyproject without a literal
- [ ] CHANGELOG top entry is dated and matches the newest tag

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: One version string, current README focus, dated CHANGELOG
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

Tags v2.0.0a7/a8 exist while pyproject, __init__, README, and a test pin 2.0.0a6; README Current focus cites past PRs as present; ROADMAP links archived canvases.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: One version string, current README focus, dated CHANGELOG
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/CHORE-009-release-version-hygiene.md
