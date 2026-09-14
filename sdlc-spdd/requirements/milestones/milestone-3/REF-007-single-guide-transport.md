---
work_id: "REF-007-single-guide-transport"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Refactor"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P1"
size: "S"
blocks: []
depends_on: 
  - "REF-006-storage-records-and-atomic-appends"
related: 
  - "TEST-003-cretrieve-roundtrip"
---

# REF-007: GuideClient is the only Guide HTTP path

**Work ID:** REF-007-single-guide-transport  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P1 / S  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-006-storage-records-and-atomic-appends` | To Do | See milestone-3 |
| Related | `TEST-003-cretrieve-roundtrip` | Complete | See milestone-2 |

## User / Business Goal

Guide HTTP is implemented three times (GuideClient, ContextStore raw urllib, installer guide_compliance/guide_ops); base URL resolution is inlined three times; a Neo4j default password is hardcoded.

## Scope

### IN SCOPE

- ContextStore, guide_compliance, guide_ops call GuideClient
- resolve_guide_base_url used everywhere
- Neo4j password comes from env/config only; no literal in source

### NOT IN SCOPE

- Guide API changes
- Embabel upstream anything

## Acceptance Criteria

- [ ] `grep -rn urllib engine/src/sdlc_engine | grep -v guide_client.py` returns only issues.py
- [ ] TEST-003 C-RETRIEVE suite passes with the mocked client injected once

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: GuideClient is the only Guide HTTP path
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

Guide HTTP is implemented three times (GuideClient, ContextStore raw urllib, installer guide_compliance/guide_ops); base URL resolution is inlined three times; a Neo4j default password is hardcoded.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: GuideClient is the only Guide HTTP path
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-007-single-guide-transport.md
