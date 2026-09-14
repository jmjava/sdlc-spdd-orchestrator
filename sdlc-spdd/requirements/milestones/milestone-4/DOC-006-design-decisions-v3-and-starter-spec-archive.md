---
work_id: "DOC-006-design-decisions-v3-and-starter-spec-archive"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Documentation"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-4"
priority: "P1"
size: "M"
blocks: []
depends_on: 
  - "REF-002-purge-pre-v3-compat"
related: []
---

# DOC-006: Rewrite design-decisions for storage v3; archive STARTER-SPEC

**Work ID:** DOC-006-design-decisions-v3-and-starter-spec-archive  
**Milestone:** Milestone 4 — Documentation truth and release hygiene  
**Status:** To Do  
**Priority / size:** P1 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (docs)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-002-purge-pre-v3-compat` | Complete | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

design-decisions.md still describes agent-context/, duplicate canvases, extensions trees (SPIKE-004 M7, unfixed); STARTER-SPEC.md is a 1 881-line fossil with two inbound links.

## Scope

### IN SCOPE

- ADR-style design-decisions.md: ledger-first, single home, one engine, no archive folders, harness/skills
- Move STARTER-SPEC.md to docs/archive/ with a short pointer; update CHANGELOG link

### NOT IN SCOPE

- New decisions

## Acceptance Criteria

- [ ] design-decisions.md mentions no agent-context/ or extensions/
- [ ] Root has no STARTER-SPEC.md; docs hub links the archive

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Documentation
- Summary: Rewrite design-decisions for storage v3; archive STARTER-SPEC
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

design-decisions.md still describes agent-context/, duplicate canvases, extensions trees (SPIKE-004 M7, unfixed); STARTER-SPEC.md is a 1 881-line fossil with two inbound links.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Rewrite design-decisions for storage v3; archive STARTER-SPEC
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/DOC-006-design-decisions-v3-and-starter-spec-archive.md
