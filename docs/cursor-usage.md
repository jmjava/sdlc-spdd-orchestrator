# Cursor Usage

## Install Commands

From this repository into a target project:

    ./scripts/init-project.sh --target /path/to/your/project --cursor

Or install commands only:

    ./scripts/install-cursor-commands.sh --target /path/to/your/project

Commands are copied to `.cursor/commands/`, and an always-on operating-model rule is installed to `.cursor/rules/sdlc-spdd.mdc`.

The rule (`alwaysApply: true`) gives Cursor persistent grounding in the whole ecosystem — Planning (`ROADMAP.md`, `milestone-*.md`, `session-notes/`), SPDD (`spdd/canvas/`), and SDLC (`.sdlc/sessions/`, the `spdd/memory/lessons.jsonl` ledger) — on every chat, not only when a `/sdlc-spdd-*` command runs. This mirrors GitHub Copilot's `.github/copilot-instructions.md` and Claude Code's `CLAUDE.md`.

To install GitHub Copilot prompt files instead, see [copilot-usage.md](copilot-usage.md). To install Claude Code commands, see [claude-usage.md](claude-usage.md).

## How to Invoke a Command

Open the **target project** in Cursor. Open **Chat** or **Agent**. Type `/` and select a command (for example `sdlc-spdd-init`), or type `/sdlc-spdd-init` and send. These run in chat — not in the terminal. See [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

## Available Commands

### Lifecycle (`/sdlc-spdd-*`)

| Command | Purpose |
|---------|---------|
| `/sdlc-spdd-whereami` | Orient: team registry, active Work ID, phase, gates, next command |
| `/sdlc-spdd-init` | Bootstrap project folders and memory |
| `/sdlc-spdd-analysis` | Fowler Step 3: domain keywords, scoped code scan, analysis artifact |
| `/sdlc-spdd-plan` | Create REASONS Canvas from accepted analysis |
| `/sdlc-spdd-architect` | Harden canvas before coding |
| `/sdlc-spdd-code` | Implement one approved operation |
| `/sdlc-spdd-api-test` | Generate cURL API test script from canvas + implementation |
| `/sdlc-spdd-review` | Review changes against canvas |
| `/sdlc-spdd-commit-message` | Generate a commit message from current changes via `sdlc.sh commit-message` (does not commit) |
| `/sdlc-spdd-prompt-update` | Update canvas first when requirements or behavior intent change |
| `/sdlc-spdd-retro` | Capture learnings into memory |
| `/sdlc-spdd-sync` | Reconcile canvas with code |

### Workflow (`/sdlc-*`)

Chat wrappers for `./scripts/sdlc-spdd/sdlc.sh` — manage Work ID and phase without leaving chat:

| Command | Purpose |
|---------|---------|
| `/sdlc-claim <WORK-ID>` | Claim work (sets pointer + team registry); `--force` to take over |
| `/sdlc-next` | Show next action for current work (same family as `/sdlc-spdd-whereami`) |
| `/sdlc-advance` | Advance to the next phase when gates allow |
| `/sdlc-shelf` | Pause current work |
| `/sdlc-team` | Show the team work registry |

## Tips

- Run `/sdlc-next`, `/sdlc-spdd-whereami`, or `./scripts/sdlc-spdd/sdlc.sh next` at session start for orientation.
- Claim with `/sdlc-claim <WORK-ID>` (or shell `sdlc.sh claim`); commit `spdd/memory/registry.jsonl` on shared repos.
- Reference files with `@` paths in Cursor prompts.
- Keep planning and architect phases free of application code changes.
- Run review after each coding operation when possible.

See also:

- [workflow.md](workflow.md)
- [initialization-and-invocation.md](initialization-and-invocation.md)
- [daily-runbook.md](daily-runbook.md)
