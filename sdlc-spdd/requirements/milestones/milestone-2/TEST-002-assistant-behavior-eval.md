---
work_id: "TEST-002-assistant-behavior-eval"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Test"
jira_status: "Complete"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks: []
depends_on:
  - "TEST-001-evaluation-protocol"
  - "FEAT-016-intent-code-traceability"
related:
  - "DOC-003-replication-package"
---

# TEST-002: Multi-assistant behavioral evaluation slice

**Work ID:** TEST-002-assistant-behavior-eval  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** Complete (protocol incomplete; n=1)  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `TEST-001-evaluation-protocol` | Complete | See milestone-2 |
| Depends On | `FEAT-016-intent-code-traceability` | Complete | See milestone-2 |
| Related | `DOC-003-replication-package` | Complete | See milestone-2 |

## User / Business Goal

Execute one small protocol slice across assistants so 'parity' means behavior, not generated markdown adapters.

## Scope

### IN SCOPE

- One gold task (replace or extend the Spring Boot example so it has real source)
- Record compliance + outcome for Cursor and at least one other assistant, or document why only one API is available
- Compare to unstructured-chat baseline on the same task

### NOT IN SCOPE

- A full user study (N developers)
- Claiming statistical significance from n=1 task

## Acceptance Criteria

- [x] Gold task has source + canvas + expected operations
- [x] A recorded run (logs or review artifacts) for the method vs unstructured baseline
- [x] Limitations of n and model version are written next to any numbers

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Test
- Summary: Multi-assistant behavioral evaluation slice
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Execute one small protocol slice across assistants so 'parity' means behavior, not generated markdown adapters.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Multi-assistant behavioral evaluation slice
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

Complete as a protocol-incomplete n=1 slice. Next Work ID: CHORE-003-dogfood-ledger.
