---
work_id: "SPIKE-005-architecture-review"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Spike"
jira_status: "In Progress"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P0"
size: "M"
blocks: 
  - "REF-002-purge-pre-v3-compat"
  - "REF-003-retire-bash-workflow-dual-path"
  - "BUG-001-db-query-undefined-names"
  - "CHORE-004-lint-and-complexity-gates-real"
depends_on: []
related: 
  - "SPIKE-004-academic-contribution-bar"
---

# SPIKE-005: Full architectural review and Milestone 3/4/5 program

**Work ID:** SPIKE-005-architecture-review  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** In Progress  
**Priority / size:** P0 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `REF-002-purge-pre-v3-compat` | To Do | See milestone-3 |
| Blocks | `REF-003-retire-bash-workflow-dual-path` | To Do | See milestone-3 |
| Blocks | `BUG-001-db-query-undefined-names` | To Do | See milestone-3 |
| Blocks | `CHORE-004-lint-and-complexity-gates-real` | To Do | See milestone-3 |
| Depends On | (none) | — | — |
| Related | `SPIKE-004-academic-contribution-bar` | Complete | See milestone-2 |

## User / Business Goal

Review source, tests, and docs end to end; open governed milestones so consolidation work is Work IDs, not ad-hoc edits.

## Scope

### IN SCOPE

- Measured baseline (tests, coverage, complexity, lint, shellcheck, doc links)
- Four-area review (engine, shell/templates, tests/CI, docs) with file:line evidence
- Milestone 3, 4, 5 definitions, requirement stubs, task lists, Obsidian monthly goals
- ROADMAP pointer and session note

### NOT IN SCOPE

- Implementing the follow-on Work IDs (each has its own stub)
- Research claims (Milestone 2 froze them)

## Acceptance Criteria

- [x] Analysis at spdd/analysis/SPIKE-005-architecture-review-analysis.md with measured baseline
- [x] Milestone 3 and 4 have definitions, _milestone.yml, Linked Work tables; Milestone 5 has an outline
- [x] Each follow-on Work ID has a requirement stub
- [x] Task lists exist under spdd/tasks/ including the Obsidian monthly goals file
- [x] ROADMAP names Milestones 3–5
- [ ] REASONS canvas is the program plan (/sdlc-spdd-plan)

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Spike
- Summary: Full architectural review and Milestone 3/4/5 program
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

Review source, tests, and docs end to end; open governed milestones so consolidation work is Work IDs, not ad-hoc edits.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Full architectural review and Milestone 3/4/5 program
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/SPIKE-005-architecture-review.md
