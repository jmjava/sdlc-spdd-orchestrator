---
work_id: "CHORE-010-registry-reconciliation"
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
related: 
  - "REF-006-storage-records-and-atomic-appends"
---

# CHORE-010: registry.jsonl is the truth list-work reports

**Work ID:** CHORE-010-registry-reconciliation  
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
| Related | `REF-006-storage-records-and-atomic-appends` | To Do | See milestone-3 |

## User / Business Goal

11 Milestone 2 Work IDs have no claim/release event; SPIKE-004 and DOC-001 are still active; list-work derives done from canvas status, so registry and reality disagree.

## Scope

### IN SCOPE

- Append release/archived events for Milestone 2 IDs via sdlc.sh (never hand-edit)
- list-work shows registry state and canvas state side by side, flags disagreement
- Milestone 2 _milestone.yml status complete with end_date

### NOT IN SCOPE

- Registry schema changes (REF-006)

## Acceptance Criteria

- [ ] Every Work ID with a canvas has a terminal registry event
- [ ] list-work prints a MISMATCH column when they differ

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: registry.jsonl is the truth list-work reports
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

11 Milestone 2 Work IDs have no claim/release event; SPIKE-004 and DOC-001 are still active; list-work derives done from canvas status, so registry and reality disagree.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: registry.jsonl is the truth list-work reports
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/CHORE-010-registry-reconciliation.md
