---
work_id: "REF-001-engine-single-source"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Refactor"
jira_status: "Complete"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks: []
depends_on:
  - "SPIKE-004-academic-contribution-bar"
related:
  - "FEAT-016-intent-code-traceability"
---

# REF-001: Single source of truth for gate semantics

**Work ID:** REF-001-engine-single-source  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** Complete  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `SPIKE-004-academic-contribution-bar` | Complete | See milestone-2 |
| Related | `FEAT-016-intent-code-traceability` | Complete | See milestone-2 |

## User / Business Goal

Remove the internal-validity confound of default-shell vs Python engines implementing 'the method' differently. Research claims must name one semantics.

## Scope

### IN SCOPE

- Inventory of gate/workflow behavior that differs or can drift
- Either Python-default with shell shim, or a compatibility suite that fails on semantic drift
- Docs state which engine is the method under evaluation

### NOT IN SCOPE

- Deleting all shell scripts (install/upgrade may stay shell)
- New workflow phases

## Acceptance Criteria

- [x] Documented system-under-test engine for Milestone 2 evaluation
- [x] gate_check semantics live in one place; the other path delegates or is tested equal
- [x] ROADMAP/TESTING mention the chosen SUT

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Single source of truth for gate semantics
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Remove the internal-validity confound of default-shell vs Python engines implementing 'the method' differently. Research claims must name one semantics.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Single source of truth for gate semantics
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

Complete. Milestone 2 P2 backlog is done; journal n≥3 remains TEST-001's stop rule.
