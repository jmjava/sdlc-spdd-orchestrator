# Jira-Compatible Requirements Format

Embed Jira metadata and dependency links in Markdown requirements so Planning
artifacts stay the local source of truth while remaining board-friendly.

Related: [Jira runbook](jira-runbook.md), [Analysis phase scope validation](analysis-phase-scope-validation.md),
[Migration: root milestones to subdirectories](MIGRATION-root-to-subdirectories.md).

## Goals

- One local artifact per Work ID carries **scope** and **tracker metadata**
- Analysis can read Jira key, epic, status, and Related Work without API calls
- Milestone hierarchies stay navigable as directories grow
- Validation catches missing keys and broken Work ID links (format-only; no Jira API)

## Layout (preferred)

```text
requirements/
  milestones/
    README.md
    milestone-2/
      _milestone.yml                 # milestone metadata
      MILESTONE-2.md                 # goals, scope checklist, Linked Work
      CHORE-DB-001-schema-design.md  # Work ID requirement
      CHORE-API-001-oauth-crud.md
    milestone-3/
      _milestone.yml
      MILESTONE-3.md
```

**Legacy (still supported):**

- Root `milestone-N.md` definitions
- Flat `requirements/milestones/<WORK-ID>.md` stubs

When both root and subdirectory definitions exist for the same number, scripts
prefer the subdirectory and warn.

## YAML frontmatter schema

Place optional YAML frontmatter at the top of each requirement file:

```yaml
---
work_id: "CHORE-DB-001-schema-design"
jira_key: "ORCH-21620"
jira_epic: "ORCH-21000"
jira_type: "Story"
jira_status: "In Progress"
jira_assignee: "team-backend"
jira_due_date: "2026-07-31"
jira_sprint: "Sprint 46"
milestone: "milestone-2"
blocks:
  - "CHORE-API-001-oauth-crud"
  - "CHORE-DB-002-liquibase"
depends_on: []
related:
  - "CHORE-API-002-oauth-internal"
---
```

| Field | Required | Notes |
|-------|----------|-------|
| `work_id` | Recommended | Must match filename stem |
| `jira_key` | When tracked in Jira | `PROJECT-123` format |
| `jira_epic` | Optional | Parent epic key |
| `jira_type` | Optional | Story, Bug, Task, Spike, Chore |
| `jira_status` | Optional | Human status snapshot (manual sync) |
| `jira_assignee` | Optional | Handle or display name |
| `jira_due_date` | Optional | ISO date |
| `jira_sprint` | Optional | Sprint label |
| `milestone` | Recommended | `milestone-N` or path |
| `blocks` / `depends_on` / `related` | Optional | Work ID lists |

Keep the existing `## Jira` Markdown section for **copy-paste create** flows.
Claim auto-link still reads `- Key: ABC-123` under `## Jira`. Prefer setting both
`jira_key` in frontmatter and `- Key:` after issue creation.

## Markdown body template

```markdown
---
work_id: "CHORE-DB-001-schema-design"
jira_key: "ORCH-21620"
jira_status: "In Progress"
milestone: "milestone-2"
blocks:
  - "CHORE-API-001-oauth-crud"
depends_on: []
---

# CHORE-DB-001: OAuth2 Database Schema Design

**Work ID:** CHORE-DB-001-schema-design
**Milestone:** Milestone 2
**Status:** In Progress (from Jira / frontmatter)
**Date:** 2026-07-10

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | CHORE-API-001-oauth-crud | Planned | Validation depends on schema |
| Depends On | (none) | — | — |

## Scope

### IN SCOPE
- …

### NOT IN SCOPE
- … (name deferred Work IDs)

## Acceptance Criteria

- [ ] …

## Jira

- Key: ORCH-21620
- Issue type: Story
- Summary: …
```

Templates in this repo:

- `templates/requirements/requirement-chore-template.md`
- `templates/requirements/requirement-feature-template.md`
- `templates/requirements/milestones/milestone-template.yml`
- `templates/requirements/milestones/milestone-definition.md`

## Milestone `_milestone.yml`

```yaml
name: "Milestone 2 — OAuth2 Database Foundation"
number: 2
start_date: "2026-07-01"
end_date: "2026-07-31"
related_epics:
  - "ORCH-21000"
status: "in_progress"
notes: "Schema + Liquibase + CRUD validation"
```

## Validation

```bash
./scripts/validate-requirements-format.sh --target .
# Installed projects:
./scripts/sdlc-spdd/validate-requirements-format.sh --target .
```

Checks (format-only; does not call Jira):

- Frontmatter present when `--require-frontmatter` is set (optional by default)
- `jira_key` / `## Jira` Key format `PROJECT-NNNN` when present
- `blocks` / `depends_on` / `related` Work IDs resolve to existing requirement files
- Each `requirements/milestones/milestone-N/` directory has `_milestone.yml` (warn if missing)
- Milestone definition file present (`MILESTONE-N.md` or `README.md`)

## Workflow integration

1. Create or link Jira issue (see [jira-runbook.md](jira-runbook.md)).
2. Author or update the requirement with frontmatter + Scope.
3. `/sdlc-spdd-analysis` — read metadata, **lock scope**, do not rewrite Jira keys.
4. Continue architect → code → review as usual.

## Migration guide

### Existing flat requirements

1. Add YAML frontmatter fields (`work_id`, optional `jira_key`, `milestone`).
2. Ensure `## Jira` `- Key:` matches `jira_key` when both exist.
3. Add `## Related Work` / Scope IN/NOT if missing.
4. Run `validate-requirements-format.sh`.

### Existing root milestones

See [MIGRATION-root-to-subdirectories.md](MIGRATION-root-to-subdirectories.md).

### Linking to existing Jira stories

1. Set `jira_key` and `## Jira` `- Key:` to the real key.
2. Leave Summary/Description as the local draft; Jira remains board SoT for status.
3. On claim, registry picks up the Key automatically.

## Open decisions (defaults)

| Question | Default |
|----------|---------|
| Query Jira API from validation? | No — format only |
| Frontmatter vs Markdown only? | Frontmatter + Markdown summary |
| Milestone files vs directories? | Prefer directories; root still works |
| Auto-migrate existing files? | Manual + checklist; optional move script in migration doc |
