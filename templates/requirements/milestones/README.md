# Milestone-Derived Requirements

This folder holds requirement stubs created from milestone checklist items.

## Purpose

When you run `create-work-from-milestone.sh`, each unchecked milestone item becomes:

- a Work ID
- a requirement file here: `requirements/milestones/<WORK-ID>.md`
- a draft REASONS Canvas under `spdd/canvas/<WORK-ID>.md`
- a **Linked Work** row in the source `milestone-*.md` file

Use these files in plan prompts:

    /sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md

## Relationship to other planning artifacts

| Artifact | Role |
|----------|------|
| `milestone-*.md` | Goal, scope checklist, linked Work IDs |
| `requirements/milestones/` | Per-item requirement stubs derived from milestones |
| `session-notes/` | Daily agent-session narrative |
| `ROADMAP.md` | Milestone progress and current focus |

Ad-hoc requirements (not from a milestone) live directly under `requirements/` instead.
