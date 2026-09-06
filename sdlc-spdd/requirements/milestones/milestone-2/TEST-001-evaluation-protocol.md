---
work_id: "TEST-001-evaluation-protocol"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Test"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks:
  - "TEST-002-assistant-behavior-eval"
  - "DOC-003-replication-package"
depends_on:
  - "DOC-001-research-questions-and-constructs"
  - "DOC-002-related-work-map"
related: []
---

# TEST-001: Comparative evaluation protocol

**Work ID:** TEST-001-evaluation-protocol  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** To Do  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `TEST-002-assistant-behavior-eval` | Planned | See milestone-2 |
| Blocks | `DOC-003-replication-package` | Planned | See milestone-2 |
| Depends On | `DOC-001-research-questions-and-constructs` | Planned | See milestone-2 |
| Depends On | `DOC-002-related-work-map` | Planned | See milestone-2 |
| Related | (none) | — | — |

## User / Business Goal

Write a replicable protocol that evaluates the *method* (outcomes vs baselines), not only the CLI. Do not collect study data in this Work ID.

## Scope

### IN SCOPE

- Baselines: unstructured chat; canvas-only; lifecycle-only; full SDLC-SPDD
- Task set (gold artifacts), rater protocol, pre-registered metrics from DOC-001
- Nondeterminism plan (multiple model runs, what is held fixed)
- Threats-to-validity draft for DOC-003 to complete after instruments exist

### NOT IN SCOPE

- Executing the study
- Building new engine features except stubs required to record protocol IDs

## Acceptance Criteria

- [ ] Protocol document names tasks, gold files, raters, metrics, stop rules
- [ ] Each RQ in DOC-001 maps to at least one protocol procedure
- [ ] Live-consumer / example gaps (no Java source, Cursor-only) are listed as current blockers with owners

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Test
- Summary: Comparative evaluation protocol
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Write a replicable protocol that evaluates the *method* (outcomes vs baselines), not only the CLI. Do not collect study data in this Work ID.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Comparative evaluation protocol
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/TEST-001-evaluation-protocol.md
