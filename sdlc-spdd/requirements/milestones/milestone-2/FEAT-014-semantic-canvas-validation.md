---
work_id: "FEAT-014-semantic-canvas-validation"
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
  - "FEAT-016-intent-code-traceability"
depends_on:
  - "DOC-001-research-questions-and-constructs"
related:
  - "FEAT-015-first-class-metrics"
---

# FEAT-014: Semantic REASONS canvas validation

**Work ID:** FEAT-014-semantic-canvas-validation  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** To Do  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `FEAT-016-intent-code-traceability` | Planned | See milestone-2 |
| Depends On | `DOC-001-research-questions-and-constructs` | Planned | See milestone-2 |
| Related | `FEAT-015-first-class-metrics` | Planned | See milestone-2 |

## User / Business Goal

Make 'valid canvas' and 'Ready For Coding' mean structured, checkable properties — not heading presence or a regex anywhere in the file.

## Scope

### IN SCOPE

- Structured readiness field (frontmatter or Metadata) as the code-phase gate
- Section content minima (non-empty Requirements, at least one T## operation with status)
- Fail (not warn-only) on unrecognized readiness when a policy flag is set
- Tests that a headings-only canvas is invalid

### NOT IN SCOPE

- LLM-judged canvas quality as a hard gate
- Changing REASONS section names

## Acceptance Criteria

- [x] gate_check(code) uses canonical readiness, not substring search over the whole file
- [x] validate-reasons-canvas.sh (or engine equivalent) fails canvases that have headings and empty bodies
- [x] Unit tests cover false-Ready (phrase in the wrong section) and empty Operations

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Feature
- Summary: Semantic REASONS canvas validation
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Make 'valid canvas' and 'Ready For Coding' mean structured, checkable properties — not heading presence or a regex anywhere in the file.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Semantic REASONS canvas validation
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/FEAT-014-semantic-canvas-validation.md
