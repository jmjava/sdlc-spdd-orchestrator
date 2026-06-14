# Framework Upgrade

Use this guide when a target application was initialized with an older version of SDLC-SPDD Orchestrator and needs the latest framework prompts, playbooks, harness files, and session scripts.

## Safe Upgrade Rule

The upgrade script updates **framework-owned files only**.

It does not overwrite:

- application source code
- application docs outside `docs/sdlc-spdd/`
- existing `ROADMAP.md`
- existing `milestone-*.md`
- existing `session-notes/`
- `requirements/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `agent-context/features/`
- existing `agent-context/memory/*.md` content

It can update:

- `.cursor/commands/sdlc-spdd-*.md`
- `.cursor/rules/sdlc-spdd.mdc`
- `.github/copilot-instructions.md`
- `.github/prompts/sdlc-spdd-*.prompt.md`
- `.claude/commands/sdlc-spdd-*.md`
- `agent-context/playbooks/*.md`
- `agent-context/harness/*.md`
- `agent-context/README.md`
- `docs/sdlc-spdd/*.md`
- `scripts/sdlc-spdd/*.sh`

This includes mapping tools:

- `create-work-from-milestone.sh`
- `sync-roadmap-from-spdd.sh`
- `summarize-session-notes.sh`

It can create when missing:

- `ROADMAP.md`
- `milestone-1.md`
- `session-notes/`
- `CLAUDE.md`
- `.github/workflows/validate-sdlc-spdd-adapters.yml`

Existing framework files are backed up before replacement by default. Existing
root `CLAUDE.md` content and target workflow customizations are preserved. When
Claude Code is installed or upgraded, SDLC-SPDD adds or refreshes only the
managed grounding block inside `CLAUDE.md`:

    <!-- BEGIN SDLC-SPDD MANAGED CLAUDE GROUNDING -->
    ...
    <!-- END SDLC-SPDD MANAGED CLAUDE GROUNDING -->

## Upgrade Command

Run from the SDLC-SPDD orchestrator repository:

    ./scripts/upgrade-project.sh --target /path/to/app --all

For backward compatibility, omitting assistant flags upgrades Cursor and GitHub
Copilot only. Use `--all` or `--claude` when you want Claude Code files.

Upgrade only Cursor prompts:

    ./scripts/upgrade-project.sh --target /path/to/app --cursor

Upgrade only GitHub Copilot prompts:

    ./scripts/upgrade-project.sh --target /path/to/app --copilot

Upgrade only Claude Code commands:

    ./scripts/upgrade-project.sh --target /path/to/app --claude

Preview first:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run

Skip backups only when you are certain the target has no local framework edits:

    ./scripts/upgrade-project.sh --target /path/to/app --all --no-backup

## Backups

By default, changed framework files are copied to:

    /path/to/app/.sdlc-spdd-upgrade-backups/<timestamp>/

Example:

    .sdlc-spdd-upgrade-backups/20260606T004500Z/.cursor/commands/sdlc-spdd-plan.md

Use these backups to recover local customizations or compare old prompts with new prompts.

## After Upgrade

From the target application:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --phase init

Then invoke:

    /sdlc-spdd-init

For existing work:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase resume

## What To Review

After upgrade, review:

- assistant prompts if your team customized `.cursor/commands/`, `.github/prompts/`, or `.claude/commands/`
- `.github/copilot-instructions.md` if your project had custom Copilot rules
- `CLAUDE.md` if the upgrade created it for the first time
- playbooks if your team edited `agent-context/playbooks/`
- SDLC-SPDD docs if your team edited `docs/sdlc-spdd/`
- backup folder for any local framework changes worth reapplying

Do not move application implementation files into the backup folder. The upgrade script never writes application source paths.
