---
work_id: "REF-006-storage-records-and-atomic-appends"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Refactor"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P1"
size: "M"
blocks: []
depends_on: 
  - "REF-002-purge-pre-v3-compat"
related: []
---

# REF-006: Typed storage records and atomic, locked JSONL appends

**Work ID:** REF-006-storage-records-and-atomic-appends  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P1 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-002-purge-pre-v3-compat` | Complete | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

Ledger records are typed but registry events and persist results are ad-hoc dicts; LEDGER_KINDS is defined twice; stage and registry appends are unlocked open-append.

## Scope

### IN SCOPE

- RegistryEvent dataclass; PersistResult dataclass; single LEDGER_KINDS
- io_util.append_jsonl_atomic with fcntl lock used by ledger stage, registry, and any JSONL writer
- io_util.save_json_dict atomic (tmp + replace) and adopted by persistence, integration_config, installer/guide
- Delete context_model dead helpers (iter_code_areas, extract_memory_facts)

### NOT IN SCOPE

- Schema version bump for existing ledgers

## Acceptance Criteria

- [ ] Concurrency test: 20 parallel captures produce 20 valid JSONL lines
- [ ] grep shows one LEDGER_KINDS definition
- [ ] No module writes JSON with bare write_text(json.dumps(...))

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Typed storage records and atomic, locked JSONL appends
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

Ledger records are typed but registry events and persist results are ad-hoc dicts; LEDGER_KINDS is defined twice; stage and registry appends are unlocked open-append.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Typed storage records and atomic, locked JSONL appends
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-006-storage-records-and-atomic-appends.md
