---
work_id: "CHORE-007-doc-links-gate"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Chore"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-4"
priority: "P0"
size: "M"
blocks: []
depends_on: 
  - "DOC-004-install-path-vocabulary"
related: 
  - "CHORE-008-single-docs-authoring-root"
---

# CHORE-007: Zero broken doc links, enforced in CI

**Work ID:** CHORE-007-doc-links-gate  
**Milestone:** Milestone 4 — Documentation truth and release hygiene  
**Status:** To Do  
**Priority / size:** P0 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (docs)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `DOC-004-install-path-vocabulary` | To Do | See milestone-4 |
| Related | `CHORE-008-single-docs-authoring-root` | To Do | See milestone-4 |

## User / Business Goal

verify-doc-links.sh reports 95 broken of 959 and is not in CI; shipped copies link orchestrator-only docs.

## Scope

### IN SCOPE

- Fix in-tree broken links (hub → ROADMAP, agent-context README, milestone files)
- verify-doc-links.sh understands the install boundary (resolve templates/project-docs and sdlc-spdd/docs links against the installed layout)
- Add to ci-docs-boundary workflow

### NOT IN SCOPE

- Rewriting doc content

## Acceptance Criteria

- [ ] verify-doc-links.sh reports 0 broken
- [ ] CI fails on a new broken link (proved once)

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: Zero broken doc links, enforced in CI
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

verify-doc-links.sh reports 95 broken of 959 and is not in CI; shipped copies link orchestrator-only docs.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Zero broken doc links, enforced in CI
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/CHORE-007-doc-links-gate.md
