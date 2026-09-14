---
work_id: "REF-009-adf-codec-and-viewer-assets"
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
  - "REF-004-split-installer-blueprints"
related: []
---

# REF-009: One ADF codec; viewer UI as static assets or Vue tab

**Work ID:** REF-009-adf-codec-and-viewer-assets  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P2 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-004-split-installer-blueprints` | To Do | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

ADF conversion lives in jira_format and again in viewer/adf_html + html_adf; viewer/pages.py is 1 190 lines of HTML in Python strings.

## Scope

### IN SCOPE

- sdlc_engine/adf/codec.py shared by issues, viewer, templates
- Move viewer UI into console-ui (Vue) or static files; delete pages.py

### NOT IN SCOPE

- New ADF node types

## Acceptance Criteria

- [ ] One implementation of GWT list detection
- [ ] viewer/pages.py deleted; Playwright viewer suite passes

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: One ADF codec; viewer UI as static assets or Vue tab
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

ADF conversion lives in jira_format and again in viewer/adf_html + html_adf; viewer/pages.py is 1 190 lines of HTML in Python strings.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: One ADF codec; viewer UI as static assets or Vue tab
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-009-adf-codec-and-viewer-assets.md
