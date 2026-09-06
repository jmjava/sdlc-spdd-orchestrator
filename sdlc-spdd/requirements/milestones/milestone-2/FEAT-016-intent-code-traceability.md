---
work_id: "FEAT-016-intent-code-traceability"
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
  - "TEST-002-assistant-behavior-eval"
depends_on:
  - "FEAT-014-semantic-canvas-validation"
related:
  - "REF-001-engine-single-source"
---

# FEAT-016: Intent-to-code and review-quality checks

**Work ID:** FEAT-016-intent-code-traceability  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** To Do  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `TEST-002-assistant-behavior-eval` | Planned | See milestone-2 |
| Depends On | `FEAT-014-semantic-canvas-validation` | Planned | See milestone-2 |
| Related | `REF-001-engine-single-source` | Planned | See milestone-2 |

## User / Business Goal

Close the gap where GATE_LABELS list code_maps_to_ops, tests_updated, and safeguards_checked but gate_check does not enforce them, and sync() auto-passes safeguards when a review file exists.

## Scope

### IN SCOPE

- Trace operations (T##) to changed paths or an explicit mapping section
- Review artifact minima (result, section-by-section, safeguards explicit)
- Align phases.gates_for_phase with what gate_check actually runs — or implement the missing checks
- Do not auto-pass safeguards_checked from file existence alone

### NOT IN SCOPE

- Full static analysis of whether code implements acceptance criteria
- Replacing human review

## Acceptance Criteria

- [x] An empty review file does not pass safeguards_checked
- [x] Documented rule for code_maps_to_ops with at least one automated check and one documented remainder for humans
- [x] phases.py and workflow.gate_check no longer advertise unenforced gates without labeling them advisory

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Feature
- Summary: Intent-to-code and review-quality checks
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Close the gap where GATE_LABELS list code_maps_to_ops, tests_updated, and safeguards_checked but gate_check does not enforce them, and sync() auto-passes safeguards when a review file exists.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Intent-to-code and review-quality checks
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/FEAT-016-intent-code-traceability.md
