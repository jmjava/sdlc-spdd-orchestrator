---
work_id: "DOC-003-replication-package"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Documentation"
jira_status: "Complete"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks: []
depends_on:
  - "TEST-001-evaluation-protocol"
  - "FEAT-015-first-class-metrics"
related:
  - "TEST-002-assistant-behavior-eval"
---

# DOC-003: Threats to validity and replication notes

**Work ID:** DOC-003-replication-package  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** Complete  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `TEST-001-evaluation-protocol` | Planned | See milestone-2 |
| Depends On | `FEAT-015-first-class-metrics` | Planned | See milestone-2 |
| Related | `TEST-002-assistant-behavior-eval` | Planned | See milestone-2 |

## User / Business Goal

Give a future referee a threats-to-validity section and a replication appendix that names frozen versions, datasets, and what cannot be automated.

## Scope

### IN SCOPE

- Construct, internal, external, conclusion, reliability threats updated from SPIKE-004 using real instruments
- How to freeze engine+adapter+model versions
- What the live-consumer harness does and does not prove

### NOT IN SCOPE

- Publishing anonymized human-subject data (may be a later IRB step)
- Packaging Guide/Neo4j as required

## Acceptance Criteria

- [x] Committed threats-to-validity doc referencing DOC-001 constructs
- [x] Replication checklist: commands, versions, gold-task locations
- [x] Explicit statement of chat nondeterminism and how TEST-001 handles it

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Documentation
- Summary: Threats to validity and replication notes
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Give a future referee a threats-to-validity section and a replication appendix that names frozen versions, datasets, and what cannot be automated.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Threats to validity and replication notes
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/DOC-003-replication-package.md
