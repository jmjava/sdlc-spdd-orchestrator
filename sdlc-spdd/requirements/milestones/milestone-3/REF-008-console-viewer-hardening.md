---
work_id: "REF-008-console-viewer-hardening"
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
size: "M"
blocks: []
depends_on: 
  - "REF-004-split-installer-blueprints"
related: []
---

# REF-008: Threat model and hardening for ops console and ADF viewer

**Work ID:** REF-008-console-viewer-hardening  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P1 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-004-split-installer-blueprints` | To Do | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

Viewer browses the whole filesystem, console shells install/upgrade, and --lan binds 0.0.0.0 with no auth or CSRF.

## Scope

### IN SCOPE

- Write docs/security/local-web-surfaces.md threat model
- --lan requires a one-time token in the URL/header; default stays 127.0.0.1
- Viewer store restricted to an allow-listed root
- CSRF token on mutating POSTs (console + viewer)

### NOT IN SCOPE

- Multi-user auth
- TLS

## Acceptance Criteria

- [ ] Integration test: POST without token is rejected when --lan
- [ ] Integration test: path outside root is rejected by viewer store
- [ ] Threat model doc linked from ops-console.md and adf-viewer.md

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Threat model and hardening for ops console and ADF viewer
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

Viewer browses the whole filesystem, console shells install/upgrade, and --lan binds 0.0.0.0 with no auth or CSRF.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Threat model and hardening for ops console and ADF viewer
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-008-console-viewer-hardening.md
