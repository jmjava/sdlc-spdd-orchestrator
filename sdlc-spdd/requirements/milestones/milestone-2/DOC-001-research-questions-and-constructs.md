---
work_id: "DOC-001-research-questions-and-constructs"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Documentation"
jira_status: "Complete"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks:
  - "TEST-001-evaluation-protocol"
  - "FEAT-014-semantic-canvas-validation"
  - "FEAT-015-first-class-metrics"
depends_on:
  - "SPIKE-004-academic-contribution-bar"
related:
  - "DOC-002-related-work-map"
---

# DOC-001: Research questions and operationalized constructs

**Work ID:** DOC-001-research-questions-and-constructs  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** Complete  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `TEST-001-evaluation-protocol` | Planned | See milestone-2 |
| Blocks | `FEAT-014-semantic-canvas-validation` | Planned | See milestone-2 |
| Blocks | `FEAT-015-first-class-metrics` | Planned | See milestone-2 |
| Depends On | `SPIKE-004-academic-contribution-bar` | Planned | See milestone-2 |
| Related | `DOC-002-related-work-map` | Planned | See milestone-2 |

## User / Business Goal

Freeze 3–5 research questions and a construct table (drift, governance/compliance, context cost, memory usefulness, portability) with definition, measure, instrument, and failure mode — so later features implement instruments, not vibes.

## Scope

### IN SCOPE

- RQ document under sdlc-spdd/docs/research/ (real research index, distinct from Jira ADF notes)
- Construct table with operational definitions
- Rewrite guidance for README/compliance language that currently says 'fixes' without evidence

### NOT IN SCOPE

- Running the study
- Implementing validators

## Acceptance Criteria

- [x] RQs are numbered and each names a dependent/independent construct
- [x] Every construct has: definition, measure, instrument (file/command), known proxy weakness
- [x] A short 'claims allowed today vs after Milestone 2' table is committed
- [x] README/compliance hedges applied (DOC-001 canvas T02)

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Documentation
- Summary: Research questions and operationalized constructs
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Freeze 3–5 research questions and a construct table (drift, governance/compliance, context cost, memory usefulness, portability) with definition, measure, instrument, and failure mode — so later features implement instruments, not vibes.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Research questions and operationalized constructs
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/DOC-001-research-questions-and-constructs.md
