# Installing into Your Project

Use this guide to install SDLC-SPDD Orchestrator into an application repository.

## Which Install Path Should I Use?

| Situation | Use |
|-----------|-----|
| New project with no SDLC-SPDD files | `setup-agent-prompts.sh --all` |
| Existing project initialized by an older orchestrator version | `upgrade-project.sh --all` |
| Cursor only | `init-project.sh --cursor` |
| GitHub Copilot only | `init-project.sh --copilot` |
| Both Cursor and Copilot | `setup-agent-prompts.sh --all` |

## Fresh Install

From the orchestrator repository:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

This installs:

- `requirements/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `ROADMAP.md`
- `milestone-1.md` when no `milestone-*.md` exists
- `session-notes/`
- `agent-context/memory/`
- `agent-context/playbooks/`
- `agent-context/features/`
- `agent-context/sessions/`
- `agent-context/harness/`
- `docs/sdlc-spdd/`
- `.cursor/commands/`
- `.github/copilot-instructions.md`
- `.github/prompts/`
- `scripts/sdlc-spdd/`

The target-local `scripts/sdlc-spdd/` folder includes session scripts and mapping tools:

- `start-agent-session.sh`
- `resync-agent-session.sh`
- `capture-session-memory.sh`
- `create-work-from-milestone.sh`
- `sync-roadmap-from-spdd.sh`
- `summarize-session-notes.sh`

## Fresh Install for One Assistant

Cursor:

    ./scripts/init-project.sh --target /path/to/app --cursor

GitHub Copilot:

    ./scripts/init-project.sh --target /path/to/app --copilot

Both:

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot

## Preview Before Installing

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot --dry-run

or:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all --dry-run

## Upgrade an Existing Install

If the project already has SDLC-SPDD files from an older version:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run
    ./scripts/upgrade-project.sh --target /path/to/app --all

The upgrade script updates framework-owned files and preserves:

- application source code.
- requirements.
- canvases.
- feature workspaces.
- reviews.
- sync logs.
- existing memory content.

Backups of overwritten framework files are stored under:

    /path/to/app/.sdlc-spdd-upgrade-backups/<timestamp>/

## After Install

Open `/path/to/app` in Cursor or a Copilot-enabled editor.

Then run:

    /sdlc-spdd-init

Create a first session brief:

    cd /path/to/app
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --phase init

Then ask:

    Read @agent-context/sessions/current-session.md and continue with /sdlc-spdd-init.

## Verify the Install

From the target app:

    test -d agent-context
    test -d spdd/canvas
    test -d docs/sdlc-spdd
    test -d scripts/sdlc-spdd
    test -f ROADMAP.md
    test -d session-notes
    test -x scripts/sdlc-spdd/create-work-from-milestone.sh
    test -x scripts/sdlc-spdd/sync-roadmap-from-spdd.sh
    test -x scripts/sdlc-spdd/summarize-session-notes.sh
    test -f agent-context/memory/project-memory.md
    test -f agent-context/playbooks/session-handoff-playbook.md
    test -f docs/sdlc-spdd/first-day-with-sdlc-spdd.md

For Cursor:

    test -f .cursor/commands/sdlc-spdd-plan.md

For GitHub Copilot:

    test -f .github/copilot-instructions.md
    test -f .github/prompts/sdlc-spdd-plan.prompt.md

## What Not to Edit by Hand

Avoid hand-editing generated framework prompt files unless you intend to keep local customizations:

- `.cursor/commands/sdlc-spdd-*.md`
- `.github/prompts/sdlc-spdd-*.prompt.md`
- `scripts/sdlc-spdd/*.sh`
- `docs/sdlc-spdd/*.md`

Team-specific process guidance should usually live in:

- `agent-context/playbooks/`
- `agent-context/memory/`
- project docs

Keep application-specific documentation outside `docs/sdlc-spdd/` so framework upgrades can refresh SDLC-SPDD docs safely.

## Troubleshooting

If slash commands do not appear:

1. Confirm the files were installed.
2. Reload the editor window.
3. For Copilot, run `Chat: Run Prompt` and choose the prompt file.
4. Confirm the project root is the folder opened in the editor.

If an upgrade overwrote local prompt customizations:

1. Check `.sdlc-spdd-upgrade-backups/<timestamp>/`.
2. Compare the old prompt to the new prompt.
3. Move team-specific guidance into playbooks or memory where possible.

## Read Next

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Agent session scripts](agent-session-scripts.md)
- [Framework upgrade](framework-upgrade.md)
