# Claude Code Usage

SDLC-SPDD can be used from [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with project memory (`CLAUDE.md`) and custom slash commands stored in `.claude/commands/`.

## Install Claude Customizations

From this repository into a target project:

    ./scripts/init-project.sh --target /path/to/your/project --claude

Or install only Claude files:

    ./scripts/install-claude-commands.sh --target /path/to/your/project

This installs:

- `CLAUDE.md` (project memory and operating model, at the project root)
- `.claude/commands/sdlc-spdd-init.md`
- `.claude/commands/sdlc-spdd-analysis.md`
- `.claude/commands/sdlc-spdd-plan.md`
- `.claude/commands/sdlc-spdd-architect.md`
- `.claude/commands/sdlc-spdd-code.md`
- `.claude/commands/sdlc-spdd-api-test.md`
- `.claude/commands/sdlc-spdd-review.md`
- `.claude/commands/sdlc-spdd-prompt-update.md`
- `.claude/commands/sdlc-spdd-retro.md`
- `.claude/commands/sdlc-spdd-sync.md`
- `.claude/commands/sdlc-spdd-whereami.md`

To install Cursor commands or GitHub Copilot prompt files instead, see [cursor-usage.md](cursor-usage.md) and [copilot-usage.md](copilot-usage.md). To install all three at once, use `./scripts/setup-agent-prompts.sh --target /path/to/your/project --all`.

## How to Invoke a Command

Open the **target project** in Claude Code, then type `/` and pick a command (for example `sdlc-spdd-init`), or type `/sdlc-spdd-init` and send. These run in the Claude Code session — not in the terminal as shell commands. See [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

Project-scoped commands installed under `.claude/commands/` are available in any Claude Code session opened in that project. Arguments you type after the command (such as a canvas path) are passed to the command via Claude Code's `$ARGUMENTS` handling.

## Available Commands

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
| `/sdlc-spdd-prompt-update` | Update canvas first when requirements or behavior intent change |
| `/sdlc-spdd-retro` | Capture learnings into memory |
| `/sdlc-spdd-sync` | Reconcile canvas with code |

## Start Work in Claude Code

### From a Jira issue

    /sdlc-spdd-plan Jira ABC-123: add order status lookup. Link the canvas to https://jira.example.com/browse/ABC-123 and preserve these acceptance criteria:
    - GET /orders/{id}/status returns current status.
    - Unknown orders return 404.
    - Response includes orderId, status, and updatedAt.

### From a GitHub issue

    /sdlc-spdd-plan GitHub issue https://github.com/org/repo/issues/42. Create a canvas, link the issue in Metadata, and list the smallest safe operations.

### From a plain request

    /sdlc-spdd-plan Add a customer notification email when an order ships. Create a Work ID and record assumptions.

## Ask Context-Preserving Questions

Use the Work ID and `@` file references.

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md before answering. Which operation is next?

    For FEAT-001 operation T01, inspect the current diff. Are any files unrelated to the approved operation?

    For BUG-003, read @agent-context/memory/known-pitfalls.md. What should I check before review?

## Claude-Specific Notes

- `CLAUDE.md` at the project root is loaded automatically by Claude Code as project memory for every session.
- Custom slash commands live in `.claude/commands/` as Markdown files; the file name (without `.md`) becomes the command name.
- Each command file uses YAML frontmatter (`description`, `argument-hint`) so the command shows useful help in Claude Code's slash-command menu.
- Keep source code changes out of planning, architecture, retro, and sync commands unless explicitly requested.
- Use `@` file references so Claude reads the exact artifact for the current Work ID and phase.

See also:

- [workflow.md](workflow.md)
- [initialization-and-invocation.md](initialization-and-invocation.md)
- [daily-runbook.md](daily-runbook.md)
