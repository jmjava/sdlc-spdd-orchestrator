---
work_id: "CHORE-008-single-docs-authoring-root"
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
size: "M"
blocks: []
depends_on: 
  - "CHORE-007-doc-links-gate"
related: []
---

# CHORE-008: docs/ is the only authoring root; sdlc-spdd/docs is generated

**Work ID:** CHORE-008-single-docs-authoring-root  
**Milestone:** Milestone 4 — Documentation truth and release hygiene  
**Status:** To Do  
**Priority / size:** P1 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (docs)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `CHORE-007-doc-links-gate` | To Do | See milestone-4 |
| Related | (none) | — | — |

## User / Business Goal

Five shipped docs have diverged from docs/; research trees are split without saying so; one doc is orphaned.

## Scope

### IN SCOPE

- Re-sync sdlc-spdd/docs from docs/ via upgrade; CI drift check
- Both README hubs state the research split explicitly
- Index or archive unattended-iterations.md; add spdd-compliance and sdlc-agents-and-the-framework to the hub

### NOT IN SCOPE

- Moving academic research out of dogfood

## Acceptance Criteria

- [ ] `diff -rq docs sdlc-spdd/docs` differs only in the intended README and research trees
- [ ] No orphan .md under docs/ or sdlc-spdd/docs

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: docs/ is the only authoring root; sdlc-spdd/docs is generated
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

Five shipped docs have diverged from docs/; research trees are split without saying so; one doc is orphaned.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: docs/ is the only authoring root; sdlc-spdd/docs is generated
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/CHORE-008-single-docs-authoring-root.md
