# Migration: Root Milestone Files → Subdirectories

Move from root-level `milestone-N.md` files to
`requirements/milestones/milestone-N/` without breaking existing scripts.

Related: [Jira-compatible requirements format](jira-compatible-requirements-format.md),
[Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md).

## Why migrate

- Keeps the project root small when you have many milestones
- Co-locates milestone definition, `_milestone.yml`, and Work ID requirements
- Mirrors `spdd/canvas/milestone-N/` organization when you use canvas subdirs

## Target layout

```text
requirements/milestones/
  milestone-1/
    _milestone.yml
    MILESTONE-1.md          # was ./milestone-1.md
    FEAT-001-….md           # was requirements/milestones/FEAT-001-….md (optional move)
  milestone-2/
    _milestone.yml
    MILESTONE-2.md
```

Root `milestone-N.md` may remain as a short pointer, or be removed after Linked
Work and prompts are updated.

## Manual steps

1. Create the directory:

   ```bash
   mkdir -p requirements/milestones/milestone-1
   ```

2. Move (or copy) the definition:

   ```bash
   git mv milestone-1.md requirements/milestones/milestone-1/MILESTONE-1.md
   ```

3. Add milestone metadata:

   ```bash
   cp path/to/orchestrator/templates/requirements/milestones/milestone-template.yml \
     requirements/milestones/milestone-1/_milestone.yml
   # edit name, dates, related_epics
   ```

4. Optionally move Work ID stubs that belong to this milestone into the same
   directory. Update **Linked Work** Requirement column paths in `MILESTONE-1.md`.

5. Update references in `ROADMAP.md`, session notes, and canvases from
   `milestone-1.md` to `requirements/milestones/milestone-1/MILESTONE-1.md`.

6. Verify discovery:

   ```bash
   # From a shell with scripts/lib sourced, or via session start:
   ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --dry-run
   # or capture with auto milestone detect
   ```

7. Run requirements validation:

   ```bash
   ./scripts/sdlc-spdd/validate-requirements-format.sh --target .
   ```

## Optional one-liner move (definition only)

```bash
N=1
mkdir -p "requirements/milestones/milestone-${N}"
if [[ -f "milestone-${N}.md" ]]; then
  git mv "milestone-${N}.md" "requirements/milestones/milestone-${N}/MILESTONE-${N}.md"
fi
```

Copy `_milestone.yml` from the template after the move.

## Backward compatibility

| Scenario | Behavior |
|----------|----------|
| Root only | Scripts find `milestone-N.md` |
| Subdirectory only | Scripts find `MILESTONE-N.md` / `README.md` |
| Both present | Prefer subdirectory; warn on stderr |
| Flat + nested requirement stubs | Prefer nested; warn |

No automatic deletion of root files.

## Naming choices

| Option | Use |
|--------|-----|
| `MILESTONE-N.md` | Preferred detailed definition (checklist + Linked Work) |
| `README.md` | Allowed overview; discovery accepts it |
| Root `milestone-N.md` | Legacy / optional quick pointer |

## After migration

- New work from `create-work-from-milestone.sh --milestone requirements/milestones/milestone-N/MILESTONE-N.md`
  writes requirement stubs into that subdirectory.
- `/sdlc-spdd-analysis` and plan prompts should `@`-mention the new paths.
