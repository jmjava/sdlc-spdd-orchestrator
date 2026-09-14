---
work_id: "DOC-007-glossary-and-engine-cli-guide"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Documentation"
jira_status: "To Do"
jira_assignee: ""
jira_due_date: ""
jira_sprint: ""
milestone: "milestone-4"
priority: "P2"
size: "S"
blocks: []
depends_on: 
  - "REF-005-cli-command-modules"
related: []
---

# DOC-007: Glossary and end-to-end 'add a CLI command' guide

**Work ID:** DOC-007-glossary-and-engine-cli-guide  
**Milestone:** Milestone 4 — Documentation truth and release hygiene  
**Status:** To Do  
**Priority / size:** P2 / S  
**Date:** 2026-09-13  
**Beck stage:** make it right (docs)

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | (none) | — | — |
| Depends On | `REF-005-cli-command-modules` | To Do | See milestone-3 |
| Related | (none) | — | — |

## User / Business Goal

Contributors have adapter docs but no glossary and no guide for adding a Python subcommand through parser, tests, docs, and adapters.

## Scope

### IN SCOPE

- docs/glossary.md (Work ID, canvas, ledger, registry, phase, gate, capture/accept, projection, quiet mode)
- docs/contributing-engine-cli.md walking one command end to end

### NOT IN SCOPE

- (none)

## Acceptance Criteria

- [ ] Both docs linked from docs/README.md and CONTRIBUTING.md

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Documentation
- Summary: Glossary and end-to-end 'add a CLI command' guide
- Labels: sdlc-spdd, milestone-4, docs-truth
- Components: framework

### Description

Contributors have adapter docs but no glossary and no guide for adding a Python subcommand through parser, tests, docs, and adapters.

### Acceptance criteria (Given/When/Then)

- Given Documentation truth and release hygiene is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Glossary and end-to-end 'add a CLI command' guide
- Labels: sdlc-spdd, milestone-4, docs-truth
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-4/DOC-007-glossary-and-engine-cli-guide.md
