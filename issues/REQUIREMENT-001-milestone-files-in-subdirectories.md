# REQUIREMENT-001: Support Milestone Files in Subdirectories

**Type:** Framework Enhancement  
**Status:** Implemented (on `cursor/integration-981e`)  
**Priority:** HIGH  
**Reported:** 2026-06-24  
**Implemented:** 2026-07-15  
**Reporter:** example-auth-service project  

---

## Summary

The SDLC-SPDD framework currently requires milestone definition files (`milestone-1.md`, `milestone-2.md`, etc.) to be located at the **project root**. However, to maintain clean project structure with REASONS Canvas organization, milestone **requirement stubs** should be organized in subdirectories (`/requirements/milestones/milestone-1/`, `/requirements/milestones/milestone-2/`, etc.) mirroring the canvas subdirectory structure (`/spdd/canvas/milestone-1/`, `/spdd/canvas/milestone-2/`, etc.).

**Current Framework Limitation:**
- Framework scripts and documentation assume milestone files are at project root: `./milestone-1.md`, `./milestone-2.md`
- This creates a bloated root directory when managing 6+ milestones
- Requirement stubs must now be discovered in `/requirements/milestones/milestone-{N}/` subdirectories

**Desired Behavior:**
- Framework should support **BOTH** root-level milestone files AND subdirectory-based organization
- Milestone index scripts should scan `/requirements/milestones/` for subdirectories
- Canvas discovery should continue to scan `/spdd/canvas/milestone-{N}/` subdirectories (already working)
- Backward compatibility: projects using root-level milestone files should continue to work

---

## Problem Statement

### Current State (Framework Limitation)

The SDLC-SPDD orchestrator scaffold and documentation state that milestone files should be at the project root:

```
project-root/
├── milestone-1.md        ← Framework expects milestone definition here
├── milestone-2.md        ← Framework expects milestone definition here
├── ROADMAP.md
├── requirements/
│   └── milestones/       ← Requirements stubs now located here
│       ├── milestone-1/
│       │   ├── CHORE-001.md
│       │   └── CHORE-002.md
│       └── milestone-2/
│           ├── CHORE-DB-001.md
│           └── CHORE-DB-002.md
└── spdd/
    └── canvas/
        ├── milestone-1/  ← Canvas files already organized here
        │   ├── CHORE-001.md
        │   └── CHORE-002.md
        └── milestone-2/  ← Canvas files already organized here
            ├── CHORE-DB-001.md
            └── CHORE-DB-002.md
```

### Problem

**Inconsistency:** Requirement stubs are organized in `/requirements/milestones/milestone-{N}/` but framework documentation assumes milestone metadata is at root.

**Root Bloat:** With 6+ milestones (M1-M6), the root directory becomes cluttered with 6+ `milestone-*.md` files.

**Discovery Friction:** Scripts and tools need to know to look in two places:
1. Root level for milestone metadata (`./milestone-{N}.md`)
2. Subdirectories for requirement stubs (`./requirements/milestones/milestone-{N}/`)

---

## Solution

### Proposed Approach

**Goal:** Allow both patterns while preferring subdirectory organization for new projects.

### Changes Required

#### 1. **Update SDLC Orchestrator Scaffold**
- When scaffolding a new project, create milestone files in `/requirements/milestones/milestone-{N}/` subdirectories instead of root
- Update templates:
  - `templates/requirement-stub.md` → Include SDLC-SPDD requirement structure
  - `templates/milestone-definition.md` → New template for milestone metadata

#### 2. **Update Documentation**
- Update `docs/sdlc-spdd/sdlc-agents-and-the-framework.md`:
  - Recommend subdirectory organization: `/requirements/milestones/milestone-{N}/MILESTONE-{N}.md`
  - Show example project structure with both canvas and requirement subdirectories
  - Note backward compatibility with root-level files

- Update `docs/directory-structure.md`:
  - Include both patterns (root and subdirectory)
  - Recommend subdirectory for new projects (cleaner root)

#### 3. **Update Framework Scripts**
- `scripts/sdlc-spdd/resolve-agent-context.sh`:
  - Scan `/requirements/milestones/milestone-{N}/` subdirectories for CHORE files
  - Fall back to root level if subdirectory not found
  
- `scripts/sdlc-spdd/index-spdd-analysis.sh`:
  - Index milestone files from both root and subdirectory locations
  - Prefer subdirectory if both exist (with warning)

- `scripts/sdlc-spdd/capture-session-memory.sh`:
  - Discover milestone files in subdirectories
  - Update memory indexes accordingly

#### 4. **Update SDLC Agent Prompt Templates**
- `/CLAUDE.md` (project-level):
  - Update context-loading instructions to scan `/requirements/milestones/milestone-{N}/`
  
- `/github/copilot-instructions.md` (project-level):
  - Update context-loading instructions to scan subdirectories

#### 5. **Add Migration Guide**
- `docs/MIGRATION-root-to-subdirectories.md`:
  - How to move existing root-level milestone files to subdirectories
  - Script to automate migration (optional)
  - Backward compatibility notes

---

## Acceptance Criteria

- [x] Framework scaffold creates milestone files in `/requirements/milestones/milestone-{N}/` subdirectories (new projects)
- [x] Scripts can discover milestone files from both root and subdirectory locations (backward compatibility)
- [x] Documentation updated with both patterns and recommendation
- [x] Agent prompts (CLAUDE.md, copilot-instructions.md, cursor rules) scan subdirectories correctly
- [x] No breaking changes to existing projects using root-level files
- [x] Example layout documented in migration + jira format guides
- [x] Migration guide available for projects transitioning to subdirectories

---

## Affected Projects

**Currently Affected:**
- `example-auth-service` — Milestone files at root, requirement stubs in subdirectories (mixed pattern)

**May Be Affected:**
- Any new projects created after this change should use subdirectory pattern

---

## Implementation Notes

### Key Files to Modify

**Orchestrator:**
- `templates/` — Update or create new milestone templates
- `docs/` — Update directory structure, context loading, and framework guide
- `scripts/sdlc-spdd/` — Update discovery and indexing scripts

**Agent Customization:**
- `.claude/commands/` — Update prompts if they reference milestone files
- `CLAUDE.md` — Update context-loading instructions
- `.github/copilot-instructions.md` — Update context-loading instructions

### Backward Compatibility Strategy

1. **Detection:** Scripts check for milestone files in both locations
2. **Preference:** If file exists in both, prefer subdirectory with warning
3. **No Deletion:** Root-level files are not automatically removed (manual cleanup if needed)
4. **Documentation:** Clear migration path provided for projects wanting to transition

### Example Proposed Structure (After Implementation)

```
new-project-root/
├── milestone-1.md                  ← Optional: can stay at root for quick reference
├── ROADMAP.md
├── requirements/
│   └── milestones/
│       ├── milestone-1/
│       │   ├── README.md            ← M1 overview
│       │   ├── CHORE-001.md
│       │   └── CHORE-002.md
│       └── milestone-2/
│           ├── README.md            ← M2 overview
│           ├── CHORE-DB-001.md
│           └── CHORE-DB-002.md
└── spdd/
    └── canvas/
        ├── milestone-1/
        │   ├── README.md
        │   ├── MILESTONE-1.md
        │   ├── CHORE-001.md
        │   └── CHORE-002.md
        └── milestone-2/
            ├── README.md
            ├── MILESTONE-2.md
            ├── CHORE-DB-001.md
            └── CHORE-DB-002.md
```

---

## Related Issues / Discussions

- **Issue:** Milestone file organization inconsistency
- **Related Feature:** SDLC-SPDD progressive disclosure (context loading by milestone)
- **Design Pattern:** Mirror canvas organization in requirements structure

---

## Questions for Framework Team

1. Should we maintain root-level milestone files as "quick reference" files, or prefer pure subdirectory organization?
2. What's the preferred naming for milestone metadata in subdirectories? 
   - Option A: `MILESTONE-{N}.md` (same as canvas)
   - Option B: `README.md` with milestone metadata
   - Option C: Both (README overview + MILESTONE-{N}.md detailed canvas)
3. Should we provide a script to auto-migrate existing projects from root to subdirectories?

---

## Testing Plan

- [ ] New project scaffold creates milestone files in subdirectories
- [ ] Old project with root-level files still works
- [ ] Mixed project (some root, some subdirectory) resolves correctly
- [ ] Agent context-loading finds milestone files in subdirectories
- [ ] ROADMAP.md links resolve correctly for both patterns
- [ ] Migration script (if created) successfully moves files

---

**Version:** 1.0  
**Last Updated:** 2026-06-24  
**Owner:** Framework Enhancement  
**Impact:** Medium (affects new project scaffolding, no breaking changes)
