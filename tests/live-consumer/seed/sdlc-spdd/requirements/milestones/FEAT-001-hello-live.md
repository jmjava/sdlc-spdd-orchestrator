---
work_id: "FEAT-001-hello-live"
jira_key: ""
jira_epic: ""
jira_type: "Story"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-1"
blocks: []
depends_on: []
related: []
---

# FEAT-001: Hello Live Consumer

**Work ID:** FEAT-001-hello-live  
**Milestone:** Milestone 1  
**Status:** To Do  
**Date:** 2026-07-31

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | (none) | — | — |

## User / Business Goal

Prove SDLC-SPDD install + workflow scripts + Cursor slash commands work in a
fresh consumer repo that is seeded and flushed every run.

## Scope

### IN SCOPE

- Greeting helper returns a deterministic string
- Framework install, claim/next/advance/shelf/archive paths
- Cursor command adapters present and effect-verifiable

### NOT IN SCOPE

- Production deployment
- External SaaS integrations (unless an opt-in scenario enables them)

## Acceptance Criteria

- [ ] `greet()` returns `hello, <name>`
- [ ] Live consumer matrix passes install + shell + effects scenarios

## Non-Goals

- Real product features beyond the seed stub

## Jira

- Key:
- Issue type: Story
- Summary: Hello live consumer matrix
