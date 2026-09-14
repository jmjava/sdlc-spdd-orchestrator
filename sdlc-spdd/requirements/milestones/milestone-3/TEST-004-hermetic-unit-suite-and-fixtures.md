---
work_id: "TEST-004-hermetic-unit-suite-and-fixtures"
jira_key: ""
github_number: ""
jira_epic: ""
jira_type: "Test"
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
related: 
  - "CHORE-005-ci-reusable-workflows"
---

# TEST-004: Hermetic unit suite, shared installed-target fixture, no grab-bag tests

**Work ID:** TEST-004-hermetic-unit-suite-and-fixtures  
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
| Related | `CHORE-005-ci-reusable-workflows` | To Do | See milestone-3 |

## User / Business Goal

Unit suite is documented as Flask-free but is not; grab-bag files are the only coverage for some modules; unit tests shell out to bash scripts; there is no shared fixture for an installed target.

## Scope

### IN SCOPE

- Move Flask test-client tests to tests_integration
- Dissolve test_hard_review_gaps.py, test_remaining_cleanup_slices.py, test_installer_coverage_gaps.py into per-module tests
- conftest fixture installed_target(tmp_path) used by unit, integration, and research tests
- pytest testpaths lists all three suites with markers; bare pytest does not silently skip
- TESTING.md counts and suite descriptions regenerated from the tree

### NOT IN SCOPE

- New feature coverage

## Acceptance Criteria

- [ ] Unit suite imports no flask (test)
- [ ] No test file named *gaps* or *slices*
- [ ] TESTING.md numbers match `grep -c 'def test_'`

## Non-Goals

- Expanding product surface (ADF, Vue3, Jira UX) under this Work ID
- Upstream PRs to embabel/guide

## Jira

Create the issue manually in Jira UI, then set **Key** (and matching `jira_key` frontmatter) and commit.

- Key: TBD
- Issue type: Test
- Summary: Hermetic unit suite, shared installed-target fixture, no grab-bag tests
- Labels: sdlc-spdd, milestone-3, one-flow
- Components: framework

### Description

Unit suite is documented as Flask-free but is not; grab-bag files are the only coverage for some modules; unit tests shell out to bash scripts; there is no shared fixture for an installed target.

### Acceptance criteria (Given/When/Then)

- Given One flow on storage v3 is the active program, When this Work ID is complete, Then the acceptance criteria above are checked and the analysis/canvas (if any) match implementation.

## GitHub

Create the issue manually in GitHub UI, then set **Number** (and matching `github_number` frontmatter when used) and commit.

- Number: TBD
- Title: Hermetic unit suite, shared installed-target fixture, no grab-bag tests
- Labels: sdlc-spdd, milestone-3, one-flow
- URL:

### Description

See this requirement and `spdd/analysis/SPIKE-005-architecture-review-analysis.md`.

## Next Step

    /sdlc-spdd-analysis @sdlc-spdd/requirements/milestones/milestone-3/TEST-004-hermetic-unit-suite-and-fixtures.md
