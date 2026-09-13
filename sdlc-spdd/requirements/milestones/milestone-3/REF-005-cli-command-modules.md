---
work_id: "REF-005-cli-command-modules"
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
  - "REF-003-retire-bash-workflow-dual-path"
related: []
---

# REF-005: One module per CLI command with result objects, not prints

**Work ID:** REF-005-cli-command-modules  
**Milestone:** Milestone 3 — One flow on storage v3  
**Status:** To Do  
**Priority / size:** P1 / M  
**Date:** 2026-09-13  
**Beck stage:** make it right (one engine, one persistence model, aligned docs/tests)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-003-retire-bash-workflow-dual-path` | To Do | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

cli_parser imports every handler; handlers print as their API; importing the CLI loads storage, issues, and sunset. Commands need to be importable, testable units.

## Scope

### IN SCOPE

- engine/src/sdlc_engine/commands/<verb>.py with register(subparsers) and run(args) -> CommandResult
- Lazy import of heavy services inside run()
- Consistent exit codes; no SystemExit in library modules (canvas.py)
- Remove cli.py compatibility re-exports and issue_tracker.py shim
- Package __init__ stops importing workflow/registry/archive

### NOT IN SCOPE

- Changing command names or flags

## Acceptance Criteria

- [ ] `python -c 'import sdlc_engine.cli'` imports no Flask, sqlite3, or urllib modules (test)
- [ ] No cmd_* function exceeds CCN 10
- [ ] tests/test-sdlc-engine-shim.sh and unit CLI tests pass

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Refactor
- Summary: One module per CLI command with result objects, not prints
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

cli_parser imports every handler; handlers print as their API; importing the CLI loads storage, issues, and sunset. Commands need to be importable, testable units.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: One module per CLI command with result objects, not prints
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/REF-005-cli-command-modules.md
