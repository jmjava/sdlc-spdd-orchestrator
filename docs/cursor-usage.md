# Cursor Usage

## Install Commands

From this repository into a target project:

    ./scripts/init-project.sh --target /path/to/your/project --cursor

Or install commands only:

    ./scripts/install-cursor-commands.sh --target /path/to/your/project

Commands are copied to `.cursor/commands/`, and an always-on operating-model rule is installed to `.cursor/rules/sdlc-spdd.mdc`.

The rule (`alwaysApply: true`) gives Cursor persistent grounding in the whole ecosystem — Planning (`ROADMAP.md`, `milestone-*.md`, `session-notes/`), SPDD (`spdd/canvas/`), and SDLC (`agent-context/sessions/`, `agent-context/memory/`) — on every chat, not only when a `/sdlc-spdd-*` command runs. This mirrors GitHub Copilot's `.github/copilot-instructions.md` and Claude Code's `CLAUDE.md`.

To install GitHub Copilot prompt files instead, see [copilot-usage.md](copilot-usage.md). To install Claude Code commands, see [claude-usage.md](claude-usage.md).

## How to Invoke a Command

Open the **target project** in Cursor. Open **Chat** or **Agent**. Type `/` and select a command (for example `sdlc-spdd-init`), or type `/sdlc-spdd-init` and send. These run in chat — not in the terminal. See [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

## Available Commands

| Command | Purpose |
|---------|---------|
| `/sdlc-spdd-init` | Bootstrap project folders and memory |
| `/sdlc-spdd-plan` | Create REASONS Canvas from requirement |
| `/sdlc-spdd-architect` | Harden canvas before coding |
| `/sdlc-spdd-code` | Implement one approved operation |
| `/sdlc-spdd-review` | Review changes against canvas |
| `/sdlc-spdd-prompt-update` | Update canvas first when requirements or behavior intent change |
| `/sdlc-spdd-retro` | Capture learnings into memory |
| `/sdlc-spdd-sync` | Reconcile canvas with code |

## Tips

- Reference files with `@` paths in Cursor prompts.
- Keep planning and architect phases free of application code changes.
- Run review after each coding operation when possible.

See also:

- [workflow.md](workflow.md)
- [initialization-and-invocation.md](initialization-and-invocation.md)
- [daily-runbook.md](daily-runbook.md)
