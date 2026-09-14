---
work_id: "REF-003-retire-bash-workflow-dual-path"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Refactor"
jira_status: "Done"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-3"
priority: "P0"
size: "L"
blocks: 
  - "REF-010-pythonize-session-and-capture"
depends_on: 
  - "REF-002-purge-pre-v3-compat"
related: 
  - "REF-001-engine-single-source"
---

# REF-003: Retire the bash workflow twin; Python engine is the only flow

**Work ID:** REF-003-retire-bash-workflow-dual-path  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** Done (PR #321)  
**Priority / size:** P0 / L  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | `REF-010-pythonize-session-and-capture` | To Do | See milestone-3 |
| Depends On | `REF-002-purge-pre-v3-compat` | Complete | See milestone-3 |
| Related | `REF-001-engine-single-source` | Complete | See milestone-2 |

## User / Business Goal

sdlc-workflow.sh (2 089 LOC) and sdlc-team-registry.sh (981 LOC) reimplement workflow, registry, pointer, and gate. Two engines mean two behaviors. Keep bash only for install/upgrade packaging and as a thin dispatcher.

## Scope

### IN SCOPE

- Delete SDLC_ENGINE=shell and SDLC_GATE_ENGINE=shell; sdlc.sh requires the Python engine and errors with the install hint
- Delete workflow/registry/pointer/gate bash implementations from templates/agent-context; keep sdlc.sh dispatcher and install scripts
- Gate path uses resolve_engine_python (SDLC_PY), never bare python3
- cmd_shell bridges sdlc-spdd/scripts in installed targets
- Bash tests that exercised shell verbs move to pytest or are deleted; live-consumer matrix runs Python-only
- Docs (engine-v2.md, TESTING.md, README) state one engine

### NOT IN SCOPE

- Pythonizing session/capture scripts (REF-010)
- Removing install/upgrade shell

## Acceptance Criteria

- [x] templates/agent-context contains no sdlc-workflow.sh / sdlc-team-registry.sh / sdlc-pointer.sh
- [x] `SDLC_ENGINE=shell ./scripts/sdlc.sh next` exits non-zero with a clear message
- [x] All bash harnesses either pass against the Python-only dispatcher or are removed with a pytest
  replacement. The count of 30 predates REF-002; the inventory was 28 when REF-003 began and is 25
  after `test-sdlc-workflow.sh`, `test-sdlc-pointer.sh`, and `test-archive-work.sh` moved to pytest.
  24 of 25 pass locally; `test-guide-stack-live.sh` needs a live Guide + Neo4j stack.
- [x] Shipped script LOC drops by at least 3 000 (3 100 template LOC; 6 200 with dogfood copies)

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: Retire the bash workflow twin; Python engine is the only flow
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

sdlc-workflow.sh (2 089 LOC) and sdlc-team-registry.sh (981 LOC) reimplement workflow, registry, pointer, and gate. Two engines mean two behaviors. Keep bash only for install/upgrade packaging and as a thin dispatcher.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Retire the bash workflow twin; Python engine is the only flow
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-003-retire-bash-workflow-dual-path.md
