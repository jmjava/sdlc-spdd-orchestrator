# Enhancement: JIRA-Compatible Requirements/Milestones Document Format

**Status:** Implemented (on `cursor/integration-981e`)  
**Date:** 2026-07-13  
**Implemented:** 2026-07-15  
**Framework Area:** Workflow Initialization → Requirements Phase  
**Related Work:** CHORE-DB-001 (OAuth2 Schema), CHORE-API-001 (Validation), CHORE-API-002 (Production), CHORE-DB-002 (Liquibase)

---

## Problem Statement

The current workflow initiates from Markdown requirements documents (`/requirements/milestones/CHORE-*.md`). While functional, these lack formal metadata and cross-linking that JIRA provides:

### Current State (Markdown-Only)

**Limitations:**
- No formal work tracking (cannot link to Jira epics, stories, subtasks)
- No status fields visible in document (embedded as comments)
- No due dates, assignees, or priority metadata
- No dependency tracking between CHOREs
- Milestones are plain Markdown files without hierarchy
- No integration with JIRA reporting/dashboards

**Result:** Parallel tracking required (Markdown + JIRA) → inconsistent source of truth

### Observed Pattern

When coordinating 4 related CHOREs (DB-001, API-001, API-002, DB-002):
- Markdown clearly shows scope and dependencies
- JIRA has different dates, status, assignees
- Questions arise: "Should I check Markdown or JIRA?"
- Risk: Stale metadata in one system

---

## Desired State

**Enhanced Workflow:**

```
START → JIRA (Create/Link Epic/Stories) → Export Requirements (JIRA → Markdown)
        ↓
        Requirements Document (Source of Truth, JIRA-Backed)
        ↓
        /sdlc-spdd-analysis (read requirements, lock scope)
        ↓
        /sdlc-spdd-architect (REASONS Canvas)
        ↓
        /sdlc-spdd-code → /sdlc-spdd-api-test → /sdlc-spdd-review → /sdlc-spdd-retro → /sdlc-spdd-sync
```

**Requirements Document Enhancements:**

1. **JIRA Metadata Headers** (frontmatter or top section)
   ```yaml
   jira_key: PROJ-1234
   jira_epic: PROJ-999
   jira_type: Story
   jira_status: In Progress
   jira_assignee: @team-member
   jira_due_date: 2026-07-31
   jira_sprint: Sprint 45
   ```

2. **Dependency Cross-Links**
   ```markdown
   ## Related Work
   - Blocks: CHORE-API-001 (validation phase depends on DB-001 design)
   - Depends On: (none)
   - Related CHOREs: CHORE-DB-002, CHORE-API-002
   ```

3. **Embedded Status Fields**
   ```markdown
   ## Status
   - Jira Status: In Progress
   - Acceptance Criteria: 8/12 met
   - Last Updated: 2026-07-13
   ```

4. **Milestone Hierarchy**
   ```
   /requirements/
     milestones/
       milestone-2/
         _milestone.yml              # Milestone metadata
         CHORE-DB-001-schema-design.md
         CHORE-API-001-oauth-crud.md
         CHORE-API-002-oauth-internal.md
         CHORE-DB-002-liquibase.md
   ```

---

## Acceptance Criteria

- [x] **Format Specification:** Create `/docs/jira-compatible-requirements-format.md` with:
  - YAML frontmatter schema for JIRA metadata
  - Markdown template for requirements documents
  - Cross-linking conventions (Jira keys, block/depend relationships)
  - Milestone structure and hierarchy

- [x] **Template Files:** Create templates in `/templates/requirements/`:
  - `requirement-chore-template.md` (with JIRA headers, section structure)
  - `requirement-feature-template.md` (with JIRA headers, feature-specific sections)
  - `milestones/milestone-template.yml` (milestone metadata)

- [x] **Validation Script:** Create `scripts/validate-requirements-format.sh`

- [x] **Workflow Integration:** Update analysis command (via `lifecycle-analysis.spec.md`)

- [x] **Migration Guide:** Documented in format spec + `docs/MIGRATION-root-to-subdirectories.md`

- [x] **Documentation:** Updated roadmap/milestones, context-loading, jira-runbook, docs hub

---

## Implementation Plan

### Phase 1: Format & Template Design (2-3 hours)

**Deliverables:**
1. `docs/sdlc-spdd/jira-compatible-requirements-format.md` — Specification
2. `templates/requirement-chore-template.md` — CHORE template with JIRA headers
3. `templates/milestone.yml` — Milestone metadata template

**Example Format:**

```yaml
---
jira_key: "ORCH-21620"
jira_epic: "ORCH-21000"
jira_type: "Story"
jira_status: "In Progress"
jira_assignee: "team-backend"
jira_due_date: "2026-07-31"
jira_sprint: "Sprint 46"
---

# CHORE-DB-001: OAuth2 Database Schema Design

**Work ID:** CHORE-DB-001-schema-design  
**Milestone:** Milestone 2 (OAuth2 Database Foundation)  
**Status:** LOCKED (from JIRA: {{jira_status}})  
**Date:** 2026-07-10

## Related Work

| Relationship | Work ID | Status | Notes |
|--------------|---------|--------|-------|
| Blocks | CHORE-API-001 | Planned | Validation depends on schema design |
| Blocks | CHORE-DB-002 | Planned | Liquibase changesets need DDL reference |
| Depends On | (none) | — | — |

## Scope

IN SCOPE:
- All 4 OAuth2 table schemas (H2 + Oracle)
- UNIQUE constraint design
- Index optimization design
- Architecture decision records (ADRs)

NOT IN SCOPE:
- JPA entity (CHORE-API-001)
- Unit tests (CHORE-API-001)
- Liquibase changesets (CHORE-DB-002)
- OAuth callback integration (later phase)

[... rest of document ...]
```

### Phase 2: Validation Script (1-2 hours)

**Script:** `scripts/validate-requirements-format.sh`

**Checks:**
- All requirements have YAML frontmatter with required fields
- Jira keys are valid format (PROJECT-NNNN)
- Block/depend relationships reference existing CHOREs
- Milestone directories have `_milestone.yml`
- No stale status fields (verify Markdown status matches JIRA status if Jira key is active)

### Phase 3: Workflow Integration (1-2 hours)

**Updates:**
- `sdlc-spdd-analysis.prompt.md` — Add JIRA metadata extraction step
- `CONTRIBUTOR_GUIDE.md` — Document new format for contributors
- `STARTER-SPEC.md` — Include JIRA-compatible template in onboarding

### Phase 4: Migration & Testing (2-3 hours)

**Tasks:**
1. Migrate existing requirements (ORCH-21617, CHORE-DB-001, CHORE-API-001, CHORE-API-002, CHORE-DB-002)
2. Create milestone.yml files for Milestone 1 and Milestone 2
3. Test validation script on migrated requirements
4. Run workflow on migrated requirements (verify analysis phase works)

---

## Benefits

| Benefit | Impact |
|---------|--------|
| **Single Source of Truth** | JIRA metadata embedded in requirements → no parallel tracking |
| **Better Context Loading** | Analysis phase can extract dependencies, assignees, sprint from frontmatter |
| **Dependency Visibility** | Block/depend relationships clear in Markdown; can be visualized in graphs |
| **Status Sync** | Validation script catches stale metadata; workflow can flag mismatches |
| **Report Generation** | Scripts can export JIRA metadata to dashboards, timelines, burn-down charts |
| **Contributor Friction** — Reduction | New team members see both JIRA context AND requirement scope in one artifact |

---

## Open Questions

1. **JIRA API Integration:** Should validation script query JIRA API to verify keys exist and sync status? (Risk: requires auth, adds latency)
   - **Proposed:** Validation checks format only; status sync is manual/optional

2. **Frontmatter vs. Markdown Section:** Should JIRA metadata be YAML frontmatter (cleaner parsing) or inline Markdown headers (more human-readable)?
   - **Proposed:** YAML frontmatter (easier scripting), with inline Markdown summary ("Status", "Related Work" sections)

3. **Milestone Hierarchy:** Should milestones be files (`milestone-2.md`) or directories (`milestone-2/`)?
   - **Proposed:** Directories with `_milestone.yml` + CHOREs inside (cleaner organization for large milestones)

4. **Breaking Changes:** Should existing Markdown requirements be auto-migrated or manually updated?
   - **Proposed:** Migration script + validation checklist; manual review for accuracy

---

## Timeline

- **Phase 1 (Design):** 2-3 hours
- **Phase 2 (Validation):** 1-2 hours
- **Phase 3 (Integration):** 1-2 hours
- **Phase 4 (Migration):** 2-3 hours
- **Total Estimate:** 6-10 hours (1-2 days sprint)

---

## Next Steps

1. ✅ Approve enhancement (or request changes)
2. Start Phase 1 (design format specification)
3. Create `docs/sdlc-spdd/jira-compatible-requirements-format.md`
4. Review templates with team
5. Build validation script
6. Migrate existing requirements as case study
