---
work_id: "DOC-005-grounding-path-map-codegen"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Documentation"
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
  - "CHORE-006-dogfood-adapters-and-quick-spec"
---

# DOC-005: Generate assistant grounding from one path map

**Work ID:** DOC-005-grounding-path-map-codegen  
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
| Related | `CHORE-006-dogfood-adapters-and-quick-spec` | Complete | See milestone-3 |

## User / Business Goal

Shipped grounding (templates/cursor/rules, templates/claude/CLAUDE.md, copilot-instructions) teaches ./scripts/sdlc-spdd/sdlc.sh and agent-context/harness, paths that do not exist in a target.

## Scope

### IN SCOPE

- spec/grounding.spec.md + path map (orchestrator vs target) → generated .mdc / CLAUDE.md / copilot-instructions
- Dogfood grounding regenerated the same way
- CI --check like command adapters

### NOT IN SCOPE

- Changing grounding content beyond paths

## Acceptance Criteria

- [ ] No `scripts/sdlc-spdd/` or `agent-context/harness` in templates/
- [ ] generate step is idempotent and checked in CI

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Documentation
- Summary: Generate assistant grounding from one path map
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

Shipped grounding (templates/cursor/rules, templates/claude/CLAUDE.md, copilot-instructions) teaches ./scripts/sdlc-spdd/sdlc.sh and agent-context/harness, paths that do not exist in a target.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Generate assistant grounding from one path map
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/DOC-005-grounding-path-map-codegen.md
