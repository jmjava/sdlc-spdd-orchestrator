---
work_id: "DOC-004-install-path-vocabulary"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Documentation"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-4"
priority: "P0"
size: "S"
blocks: []
depends_on: 
  - "SPIKE-005-architecture-review"
related: 
  - "DOC-005-grounding-path-map-codegen"
---

# DOC-004: Docs describe the layout init actually creates

**Work ID:** DOC-004-install-path-vocabulary  
**Milestone:** Milestone 4 — Documentation truth and release hygiene  
**Status:** To Do  
**Priority / size:** P0 / S  
**Date:** 2026-09-13  
**Beck stage:** make it right (docs)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `SPIKE-005-architecture-review` | In Progress | See milestone-3 |
| Related | `DOC-005-grounding-path-map-codegen` | To Do | See milestone-4 |

## User / Business Goal

init writes sdlc-spdd/docs/ but guides say docs/sdlc-spdd/; first-day requires a legacy agent-context/ folder; CONTRIBUTING cites work-registry.tsv; workflow step counts disagree.

## Scope

### IN SCOPE

- Replace docs/sdlc-spdd/ with sdlc-spdd/docs/ in installing, README hub, CONTRIBUTING
- first-day success criteria match init output
- work-registry.tsv → registry.jsonl; engine default = auto → single engine after REF-003
- One workflow step count

### NOT IN SCOPE

- Restructuring docs trees (CHORE-008)

## Acceptance Criteria

- [ ] `grep -rn 'docs/sdlc-spdd' docs README.md CONTRIBUTING.md` is empty
- [ ] first-day checklist verified against a fresh init in /tmp

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Documentation
- Summary: Docs describe the layout init actually creates
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

init writes sdlc-spdd/docs/ but guides say docs/sdlc-spdd/; first-day requires a legacy agent-context/ folder; CONTRIBUTING cites work-registry.tsv; workflow step counts disagree.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Docs describe the layout init actually creates
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/DOC-004-install-path-vocabulary.md
