# Framework Upgrade

Use this guide when a target application was initialized with an older SDLC-SPDD
install and needs the latest framework prompts, harness files, session scripts,
and storage layout.

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
- existing `spdd/memory/lessons.jsonl` content (after migration)

It can update:

- `.cursor/commands/sdlc-spdd-*.md` (includes `sdlc-spdd-whereami`)
- `.cursor/rules/sdlc-spdd.mdc`
- `.github/copilot-instructions.md`
- `.github/prompts/sdlc-spdd-*.prompt.md`
- `.claude/commands/sdlc-spdd-*.md`
- `harness/*.md` and `harness/skills/*.md`
- `docs/sdlc-spdd/*.md`
- `sdlc-spdd/scripts/*.sh` (including `sdlc.sh`)

It can create when missing:

- `ROADMAP.md`
- `milestone-1.md`
- `session-notes/`
- `CLAUDE.md`
- `spdd/memory/lessons.jsonl` and `spdd/memory/registry.jsonl`
- `.github/workflows/validate-sdlc-spdd-adapters.yml`

Existing framework files are backed up before replacement by default. Existing
root `CLAUDE.md` content is preserved. The adapter CI workflow
(`.github/workflows/validate-sdlc-spdd-adapters.yml`) is framework-owned and
refreshed on upgrade (stale copies are backed up). When
Claude Code is installed or upgraded, SDLC-SPDD adds or refreshes only the
managed grounding block inside `CLAUDE.md`:

    <!-- BEGIN SDLC-SPDD MANAGED CLAUDE GROUNDING -->
    ...
    <!-- END SDLC-SPDD MANAGED CLAUDE GROUNDING -->

## Storage migration and consolidation

After upgrading framework files, run the engine storage commands from the target
project root:

```bash
# Detect legacy layouts and show what would change
sdlc-engine storage status

# One-shot: convert legacy memory trees → ledger + registry
sdlc-engine storage migrate [--dry-run]

# Move scattered framework paths into the single sdlc-spdd/ home
./scripts/upgrade-project.sh --target . --all
```

Migration exports converted originals aside; the committed system of record becomes
`spdd/memory/lessons.jsonl` + `spdd/memory/registry.jsonl`. Hot runtime stays
gitignored under `.sdlc/`. Full model: [Storage v3](storage-v3.md).

Verify parity after migration:

```bash
sdlc-engine context parity
sdlc-engine context parity --repair   # rebuild sqlite + re-project Guide from ledger
```

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

    ./sdlc-spdd/scripts/sdlc.sh next

Then invoke:

    /sdlc-spdd-init

For existing work:

    ./sdlc-spdd/scripts/sdlc.sh resume <WORK-ID>
    ./sdlc-spdd/scripts/sdlc.sh start

## What To Review

After upgrade, review:

- assistant prompts if your team customized `.cursor/commands/`, `.github/prompts/`, or `.claude/commands/`
- `.github/copilot-instructions.md` if your project had custom Copilot rules
- `CLAUDE.md` if the upgrade created it for the first time
- `harness/skills/` if your team added custom `#SkillName` files
- SDLC-SPDD docs if your team edited `docs/sdlc-spdd/`
- `spdd/memory/registry.jsonl` claims after template merge
- backup folder for any local framework changes worth reapplying

Do not move application implementation files into the backup folder. The upgrade script never writes application source paths.
