---
work_id: "CHORE-004-lint-and-complexity-gates-real"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Chore"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P0"
size: "M"
blocks: []
depends_on: 
  - "SPIKE-005-architecture-review"
related: 
  - "BUG-001-db-query-undefined-names"
---

# CHORE-004: Make lint, complexity, and shellcheck gates run on the real diff

**Work ID:** CHORE-004-lint-and-complexity-gates-real  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P0 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `SPIKE-005-architecture-review` | In Progress | See milestone-3 |
| Related | `BUG-001-db-query-undefined-names` | To Do | See milestone-3 |

## User / Business Goal

CI only checks F401/F811 and only proves the complexity checker on a synthetic repo; shellcheck never runs. Gates must fail on real regressions.

## Scope

### IN SCOPE

- pyproject ruff select = full pyflakes (F) plus E9; fix fallout (F821, F541)
- Run scripts/check-complexity.py --base origin/main on PR diffs in test-sdlc-engine.yml (fetch-depth 0)
- Shellcheck workflow over scripts/, scripts/lib/, templates/agent-context/, tests/*.sh; fix current errors (SC2066, SC1087, SC2218, SC2144)
- Update test_quality_gates.py to assert the new rule set

### NOT IN SCOPE

- Fixing all 190 broad-rule findings (C901 etc.) — those fall to the REF items
- Adopting a formatter

## Acceptance Criteria

- [ ] CI ruff step uses the pyproject rule set; tree is clean
- [ ] A PR adding a CCN 11 function fails the complexity step (proved once, recorded in TESTING.md)
- [ ] shellcheck -S error passes in CI on all shell paths

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: Make lint, complexity, and shellcheck gates run on the real diff
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

CI only checks F401/F811 and only proves the complexity checker on a synthetic repo; shellcheck never runs. Gates must fail on real regressions.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Make lint, complexity, and shellcheck gates run on the real diff
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/CHORE-004-lint-and-complexity-gates-real.md
