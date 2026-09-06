---
work_id: "SPIKE-004-academic-contribution-bar"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Spike"
jira_status: "Analysis"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks:
  - "DOC-001-research-questions-and-constructs"
  - "DOC-002-related-work-map"
  - "TEST-001-evaluation-protocol"
depends_on: []
related: []
---

# SPIKE-004: Journal-style review and academic hardening program

**Work ID:** SPIKE-004-academic-contribution-bar  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** Analysis  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `DOC-001-research-questions-and-constructs` | Planned | See milestone-2 |
| Blocks | `DOC-002-related-work-map` | Planned | See milestone-2 |
| Blocks | `TEST-001-evaluation-protocol` | Planned | See milestone-2 |
| Depends On | (none) | — | — |
| Related | (none) | — | — |

## User / Business Goal

Review sdlc-spdd-orchestrator as a journal referee would, and open a governed Milestone 2 backlog so the project can iterate toward academic-grade claims.

## Scope

### IN SCOPE

- Journal-style analysis of problem, related work, evaluation, construct validity, reproducibility
- Milestone 2 definition, Work ID requirements, and iteration task list
- ROADMAP pointer to the academic program

### NOT IN SCOPE

- Implementing P1/P2 hardening features
- Writing the paper
- Changing engine/runtime behavior

## Acceptance Criteria

- [ ] Analysis artifact exists at spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md
- [ ] Milestone 2 has a definition, _milestone.yml, and Linked Work table
- [ ] Each follow-on Work ID has a requirement stub under milestone-2/
- [ ] Task list exists at spdd/tasks/milestone-2-academic-hardening.md
- [ ] ROADMAP names Milestone 2 and the P0/P1/P2 Work IDs

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Spike
- Summary: Journal-style review and academic hardening program
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Review sdlc-spdd-orchestrator as a journal referee would, and open a governed Milestone 2 backlog so the project can iterate toward academic-grade claims.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Journal-style review and academic hardening program
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-plan @sdlc-spdd/requirements/milestones/milestone-2/SPIKE-004-academic-contribution-bar.md
