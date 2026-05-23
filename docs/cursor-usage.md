# Cursor Usage

## Install Commands

From this repository into a target project:

    ./scripts/init-project.sh --target /path/to/your/project --cursor

Or install commands only:

    ./scripts/install-cursor-commands.sh --target /path/to/your/project

Commands are copied to `.cursor/commands/`.

## Available Commands

| Command | Purpose |
|---------|---------|
| `/sdlc-spdd-init` | Bootstrap project folders and memory |
| `/sdlc-spdd-plan` | Create REASONS Canvas from requirement |
| `/sdlc-spdd-architect` | Harden canvas before coding |
| `/sdlc-spdd-code` | Implement one approved operation |
| `/sdlc-spdd-review` | Review changes against canvas |
| `/sdlc-spdd-retro` | Capture learnings into memory |
| `/sdlc-spdd-sync` | Reconcile canvas with code |

## Tips

- Reference files with `@` paths in Cursor prompts.
- Keep planning and architect phases free of application code changes.
- Run review after each coding operation when possible.

See also: [workflow.md](workflow.md)
