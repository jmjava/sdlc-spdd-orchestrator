---
work_id: "FEAT-017-retrieval-ir-eval"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Feature"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-2"
blocks: []
depends_on:
  - "DOC-001-research-questions-and-constructs"
related:
  - "FEAT-015-first-class-metrics"
---

# FEAT-017: Retrieval as information retrieval

**Work ID:** FEAT-017-retrieval-ir-eval  
**Milestone:** Milestone 2 — Academic contribution bar  
**Status:** To Do  
**Date:** 2026-09-06  
**Beck stage:** make it right (research argument / observability)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `DOC-001-research-questions-and-constructs` | Planned | See milestone-2 |
| Related | `FEAT-015-first-class-metrics` | Planned | See milestone-2 |

## User / Business Goal

Replace 'retrieve = exact keyword filter' as the scientific story. Either evaluate retrieval as IR or stop claiming DICE/hybrid retrieval as a contribution until SPIKE-001 resumes with metrics.

## Scope

### IN SCOPE

- Document the actual retrieve algorithm vs docs
- Query set + qrels (even small) over the lessons ledger
- Baselines: keyword-list filter, FTS title/body, optional embedding if SPIKE-001 unshelved
- Precision@k / recall reporting in tests or a recorded eval script

### NOT IN SCOPE

- Requiring Neo4j for the baseline eval
- Claiming Guide embeddings without measuring them

## Acceptance Criteria

- [ ] Written algorithm for context retrieve (what matches, sort key, limits)
- [ ] At least one eval fixture where exact keyword-list miss is a ranked title/body hit
- [ ] Contribution language for DICE is conditional on measured gain or marked non-claim

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Feature
- Summary: Retrieval as information retrieval
- Labels: sdlc-spdd, milestone-2, academic-hardening
- Components: framework

### Description

Replace 'retrieve = exact keyword filter' as the scientific story. Either evaluate retrieval as IR or stop claiming DICE/hybrid retrieval as a contribution until SPIKE-001 resumes with metrics.

### Acceptance criteria (Given/When/Then)

- Given Milestone 2 is the academic program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Retrieval as information retrieval
- Labels: sdlc-spdd, milestone-2
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-004-academic-contribution-bar-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-2/FEAT-017-retrieval-ir-eval.md
