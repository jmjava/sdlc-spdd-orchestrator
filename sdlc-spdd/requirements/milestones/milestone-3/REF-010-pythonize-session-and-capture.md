---
work_id: "REF-010-pythonize-session-and-capture"
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
size: "L"
blocks: []
depends_on: 
  - "REF-003-retire-bash-workflow-dual-path"
related: []
---

# REF-010: Session brief, capture, resolve-context, and create-work in Python

**Work ID:** REF-010-pythonize-session-and-capture  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P2 / L  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-003-retire-bash-workflow-dual-path` | To Do | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

start-agent-session.sh, capture-session-memory.sh, resolve-agent-context.sh, create-work-from-milestone.sh (~2 200 LOC) have no Python twin; accept has two verbs.

## Scope

### IN SCOPE

- sdlc-engine session start/resume, capture, accept, resolve, work create-from-milestone
- sdlc.sh routes those verbs to Python; shell scripts deleted
- create-from-milestone uses templates/reasons-canvas, not an inlined body

### NOT IN SCOPE

- Changing the session brief format

## Acceptance Criteria

- [ ] scripts/ contains no *.sh over 200 LOC except install/upgrade
- [ ] One accept verb

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Session brief, capture, resolve-context, and create-work in Python
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

start-agent-session.sh, capture-session-memory.sh, resolve-agent-context.sh, create-work-from-milestone.sh (~2 200 LOC) have no Python twin; accept has two verbs.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Session brief, capture, resolve-context, and create-work in Python
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-010-pythonize-session-and-capture.md
