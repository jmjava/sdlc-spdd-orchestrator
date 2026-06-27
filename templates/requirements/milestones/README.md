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

## Jira issue drafts

Each milestone requirement file is the **natural place to store Jira syntax** before and after
issue creation. Keep copy-paste-ready fields under `## Jira`:

- **Before create** — fill Summary, Description, acceptance criteria, labels, components
- **After create** — set `- Key: ABC-123` and commit
- **On claim** — `./scripts/sdlc.sh claim <WORK-ID>` auto-reads the Key into the team registry
  `jira:` note token (disable with `SDLC_TEAM_AUTO_JIRA=0`)

See [jira-runbook.md](../../docs/jira-runbook.md) for the full create-and-sync flow.

## Relationship to other planning artifacts

| Artifact | Role |
|----------|------|
| `milestone-*.md` | Goal, scope checklist, linked Work IDs |
| `requirements/milestones/` | Per-item requirement stubs + Jira draft syntax |
| `session-notes/` | Daily agent-session narrative |
| `ROADMAP.md` | Milestone progress and current focus |

Ad-hoc requirements (not from a milestone) live directly under `requirements/` instead.
Use the same `## Jira` section there when the work will be tracked in Jira.
