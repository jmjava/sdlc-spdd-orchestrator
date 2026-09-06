---
work_id: "FEAT-015-first-class-metrics"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Feature"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks:
  - "DOC-003-replication-package"
depends_on:
  - "DOC-001-research-questions-and-constructs"
related:
  - "FEAT-014-semantic-canvas-validation"
  - "FEAT-017-retrieval-ir-eval"
---

# FEAT-015: First-class queryable process metrics

**Work ID:** FEAT-015-first-class-metrics  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** To Do  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `DOC-003-replication-package` | Planned | See milestone-2 |
| Depends On | `DOC-001-research-questions-and-constructs` | Planned | See milestone-2 |
| Related | `FEAT-014-semantic-canvas-validation` | Planned | See milestone-2 |
| Related | `FEAT-017-retrieval-ir-eval` | Planned | See milestone-2 |

## User / Business Goal

Restore FEAT-004's intent: process metrics are structured, queryable records — not optional flags buried in session body text after kind=metric was dropped.

## Scope

### IN SCOPE

- Schema for metrics (readiness, review-result, rework, context-files, validate/review cycles) aligned to DOC-001 constructs
- Capture → stage → accept path writes queryable fields
- A query surface (engine CLI) that can answer 'rework by phase' without parsing prose

### NOT IN SCOPE

- Prompt-optimization experiments (make it fast)
- Changing Guide projection ontology unless required for parity

## Acceptance Criteria

- [ ] Metrics are not solely free-text in session.body
- [ ] At least one documented query per DOC-001 construct that is supposed to use capture metrics
- [ ] Tests: capture flags round-trip into the query surface

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Feature
- Summary: First-class queryable process metrics
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Restore FEAT-004's intent: process metrics are structured, queryable records — not optional flags buried in session body text after kind=metric was dropped.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: First-class queryable process metrics
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/FEAT-015-first-class-metrics.md
