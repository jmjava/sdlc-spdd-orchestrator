# Milestone-Derived Requirements

Requirement stubs for Work IDs created from milestone checklists.

## Layout

```text
requirements/milestones/
  README.md
  milestone-1/
    _milestone.yml
    MILESTONE-1.md            # milestone complete — see git history for FEAT-001…013
  milestone-2/                # next planning tranche
    _milestone.yml
    MILESTONE-2.md
    <WORK-ID>.md
```

Flat stubs (`requirements/milestones/<WORK-ID>.md`) remain supported for legacy
installs; prefer `milestone-N/<WORK-ID>.md` for new work.

Completed Milestone 1 stubs and canvases were removed from the working tree;
use git history if you need FEAT-001…013 requirement text.

## Creating new requirements

1. Add or extend a milestone definition (`milestone-N/MILESTONE-N.md`).
2. Run `./scripts/create-work-from-milestone.sh` or copy
   `templates/requirements/requirement-feature-template.md`.
3. Validate: `./scripts/validate-requirements-format.sh --target .`

Use in analysis/plan prompts:

```text
/sdlc-spdd-analysis @requirements/milestones/milestone-2/<WORK-ID>.md
/sdlc-spdd-plan @requirements/milestones/milestone-2/<WORK-ID>.md @ROADMAP.md
```

## Jira drafts

Optional YAML frontmatter + `## Jira` section per
[docs/jira-compatible-requirements-format.md](../../docs/jira-compatible-requirements-format.md).
On claim, `./scripts/sdlc.sh claim <WORK-ID>` reads `- Key:` into the team registry.

## Relationship to other planning artifacts

| Artifact | Role |
|----------|------|
| `ROADMAP.md` | Current focus and milestone progress |
| `requirements/milestones/milestone-N/` | Scoped checklist + linked Work IDs |
| `requirements/` (root) | Ad-hoc requirements not tied to a milestone |
| `session-notes/` | Daily narrative |
| `spdd/canvas/` | REASONS design contracts — removed on `archive` when complete |

See [docs/storage-v3.md](../../docs/storage-v3.md) for the committed ledger model
(`spdd/memory/lessons.jsonl`, `registry.jsonl`).
