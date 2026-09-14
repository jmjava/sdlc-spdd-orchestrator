---
work_id: "CHORE-006-dogfood-adapters-and-quick-spec"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Chore"
jira_status: "In Progress"
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
  - "DOC-005-grounding-path-map-codegen"
---

# CHORE-006: Regenerate dogfood adapters and give /sdlc-spdd-quick a spec

**Work ID:** CHORE-006-dogfood-adapters-and-quick-spec  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** In Progress  
**Priority / size:** P0 / S  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `SPIKE-005-architecture-review` | In Progress | See milestone-3 |
| Related | `DOC-005-grounding-path-map-codegen` | To Do | See milestone-4 |

## User / Business Goal

This repo's installed command packs (.cursor/commands, .claude/commands, .github/prompts) lag templates — Kasana I1 steps and DIF steps are missing — and /sdlc-spdd-quick has no spec so the generator is not its source of truth.

## Scope

### IN SCOPE

- Regenerate dogfood packs through the same install path-rewrite used for targets
- Add spec/commands/lifecycle-quick.spec.md and generate all three adapters from it
- Extend validate-sdlc-spdd-adapters to compare dogfood against path-rewritten templates so content lag fails CI

### NOT IN SCOPE

- Changing command semantics

## Acceptance Criteria

- [x] Path-rewritten templates diff clean against .cursor/commands, .claude/commands, .github/prompts
- [ ] generate-command-adapters.sh --check covers quick
- [x] CI fails when a dogfood pack is stale

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: Regenerate dogfood adapters and give /sdlc-spdd-quick a spec
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

This repo's installed command packs (.cursor/commands, .claude/commands, .github/prompts) lag templates — Kasana I1 steps and DIF steps are missing — and /sdlc-spdd-quick has no spec so the generator is not its source of truth.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Regenerate dogfood adapters and give /sdlc-spdd-quick a spec
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/CHORE-006-dogfood-adapters-and-quick-spec.md
