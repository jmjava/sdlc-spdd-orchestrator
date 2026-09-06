---
work_id: "CHORE-003-dogfood-ledger"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Chore"
jira_status: "Complete"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks: []
depends_on:
  - "SPIKE-004-academic-contribution-bar"
related:
  - "FEAT-015-first-class-metrics"
---

# CHORE-003: Keep committed decision memory after archive

**Work ID:** CHORE-003-dogfood-ledger  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** Complete  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `SPIKE-004-academic-contribution-bar` | Complete | See milestone-2 |
| Related | `FEAT-015-first-class-metrics` | Complete | See milestone-2 |

## User / Business Goal

Archive must not leave the orchestrator's lessons ledger empty. A methods project that deletes its own decision memory cannot claim reusable learning.

## Scope

### IN SCOPE

- Policy: which lesson kinds survive canvas/requirement archive
- Seed or restore a minimal committed ledger of Milestone 1 decisions/pitfalls/patterns (from git history if needed)
- Document the policy in storage-v3 / runtime-and-ledger

### NOT IN SCOPE

- Re-adding archived canvases to the working tree
- Changing archive of Complete work IDs' contracts

## Acceptance Criteria

- [x] Working tree has a non-empty lessons.jsonl with at least decision/pitfall/pattern records, or a documented exception
- [x] Archive procedure no longer implies 'no memory left'
- [x] A test or check fails CI if dogfood ledger is accidentally deleted without policy

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Chore
- Summary: Keep committed decision memory after archive
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Archive must not leave the orchestrator's lessons ledger empty. A methods project that deletes its own decision memory cannot claim reusable learning.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Keep committed decision memory after archive
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

Complete. Next Work ID: REF-001-engine-single-source.
