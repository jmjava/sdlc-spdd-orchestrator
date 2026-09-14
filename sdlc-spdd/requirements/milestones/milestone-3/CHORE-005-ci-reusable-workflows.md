---
work_id: "CHORE-005-ci-reusable-workflows"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Chore"
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
  - "TEST-004-hermetic-unit-suite-and-fixtures"
---

# CHORE-005: Consolidate 26 workflows into ~9 with a reusable setup workflow

**Work ID:** CHORE-005-ci-reusable-workflows  
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
| Related | `TEST-004-hermetic-unit-suite-and-fixtures` | To Do | See milestone-3 |

## User / Business Goal

Setup steps are copy-pasted ~30 times; validators overlap; installer coverage runs twice; Playwright push paths are narrower than PR paths.

## Scope

### IN SCOPE

- workflow_call setup (checkout, python 3.12, engine install, optional node/playwright)
- ci-engine, ci-shell-harness, ci-adapters, ci-docs-boundary, ci-research-p0, ci-guide-experimental, ci-live-consumer, pages
- Align e2e push/PR path filters; drop duplicate installer cov job; merge validate-command-adapters into spec-generation

### NOT IN SCOPE

- Changing what is tested

## Acceptance Criteria

- [ ] ≤ 10 workflow files; one reusable setup
- [ ] Every job that ran before still runs (mapping table in TESTING.md)

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: Consolidate 26 workflows into ~9 with a reusable setup workflow
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

Setup steps are copy-pasted ~30 times; validators overlap; installer coverage runs twice; Playwright push paths are narrower than PR paths.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Consolidate 26 workflows into ~9 with a reusable setup workflow
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/CHORE-005-ci-reusable-workflows.md
