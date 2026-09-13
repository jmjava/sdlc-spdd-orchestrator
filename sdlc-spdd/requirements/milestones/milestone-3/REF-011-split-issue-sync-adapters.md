---
work_id: "REF-011-split-issue-sync-adapters"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Refactor"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P2"
size: "M"
blocks: []
depends_on: 
  - "REF-005-cli-command-modules"
related: []
---

# REF-011: Split IssueSyncService into Jira and GitHub adapters

**Work ID:** REF-011-split-issue-sync-adapters  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P2 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-005-cli-command-modules` | To Do | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

issues.py is 1 209 LOC covering draft/create/edit/pull/ADF upload/link for two trackers in one class.

## Scope

### IN SCOPE

- IssueTracker protocol; JiraAdapter, GitHubAdapter; shared draft/link logic

### NOT IN SCOPE

- New tracker features

## Acceptance Criteria

- [ ] No function in issues/ exceeds CCN 10
- [ ] Mocked issue tests pass unchanged

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Split IssueSyncService into Jira and GitHub adapters
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

issues.py is 1 209 LOC covering draft/create/edit/pull/ADF upload/link for two trackers in one class.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Split IssueSyncService into Jira and GitHub adapters
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-011-split-issue-sync-adapters.md
