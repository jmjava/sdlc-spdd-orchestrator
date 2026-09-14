---
work_id: "REF-002-purge-pre-v3-compat"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Refactor"
jira_status: "In Progress"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P0"
size: "L"
blocks: 
  - "REF-006-storage-records-and-atomic-appends"
depends_on: 
  - "SPIKE-005-architecture-review"
related: 
  - "REF-003-retire-bash-workflow-dual-path"
---

# REF-002: Purge pre-v3 persistence compatibility; one data model

**Work ID:** REF-002-purge-pre-v3-compat  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** In Progress  
**Priority / size:** P0 / L  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `REF-006-storage-records-and-atomic-appends` | To Do | See milestone-3 |
| Depends On | `SPIKE-005-architecture-review` | In Progress | See milestone-3 |
| Related | `REF-003-retire-bash-workflow-dual-path` | To Do | See milestone-3 |

## User / Business Goal

Storage v3 (ledger + registry + .sdlc/ runtime under sdlc-spdd/) is the only persistence model. Legacy layouts, migrations, and archive folders make upgrade harder and fork behavior. Losing pre-v3 context is accepted.

## Scope

### IN SCOPE

- archive deletes artifacts (git history is the record); remove spdd/*/archive/ moves and agent-context/sessions sweeps
- Remove root-layout and agent-context/harness fallbacks in project.py; sdlc-spdd/ is the home
- Remove legacy TSV registry reading in registry.py; registry.jsonl only
- Remove storage_migrate legacy parsers, agent_context_upgrade, context_model legacy markdown paths, installer/rollback legacy-layout archive
- upgrade-project.sh / init-project.sh / framework-install.sh stop consolidating legacy sprawl; no detection or refusal logic either — pre-v3 trees are simply unsupported (owner, 2026-09-14: breaking change accepted)
- Tests and docs (storage-v3.md, TESTING.md, README) describe only v3

### NOT IN SCOPE

- Changing the v3 record schema (REF-006)
- Retiring the bash workflow twin (REF-003)

## Acceptance Criteria

- [x] `engine/src` has no storage-layout `agent-context` / `work-registry`
  path; executable shell fallbacks are gone (`templates/agent-context/`
  remains the install-source directory name)
- [x] archive_work removes canvas/analysis/review/sync/session/state files; no archive/ directories are created; unit + bash tests assert the same contract
- [x] storage migration, layout archive, and duplicate-canvas reconciliation
  code paths are deleted with their tests
- [x] TESTING.md and docs/storage-v3.md describe only storage v3

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Purge pre-v3 persistence compatibility; one data model
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

Storage v3 (ledger + registry + .sdlc/ runtime under sdlc-spdd/) is the only persistence model. Legacy layouts, migrations, and archive folders make upgrade harder and fork behavior. Losing pre-v3 context is accepted.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Purge pre-v3 persistence compatibility; one data model
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-002-purge-pre-v3-compat.md
