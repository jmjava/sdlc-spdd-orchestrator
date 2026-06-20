# GitHub Copilot Usage

SDLC-SPDD can be used from GitHub Copilot Chat with workspace instructions and reusable prompt files.

To install Cursor commands or Claude Code commands instead, see [cursor-usage.md](cursor-usage.md) and [claude-usage.md](claude-usage.md).

## Install Copilot Customizations

From this repository:

    ./scripts/init-project.sh --target /path/to/your/project --copilot

Or install only Copilot files:

    ./scripts/install-copilot-prompts.sh --target /path/to/your/project

This installs:

- `.github/copilot-instructions.md`
- `.github/prompts/sdlc-spdd-init.prompt.md`
- `.github/prompts/sdlc-spdd-analysis.prompt.md`
- `.github/prompts/sdlc-spdd-plan.prompt.md`
- `.github/prompts/sdlc-spdd-architect.prompt.md`
- `.github/prompts/sdlc-spdd-code.prompt.md`
- `.github/prompts/sdlc-spdd-api-test.prompt.md`
- `.github/prompts/sdlc-spdd-review.prompt.md`
- `.github/prompts/sdlc-spdd-prompt-update.prompt.md`
- `.github/prompts/sdlc-spdd-retro.prompt.md`
- `.github/prompts/sdlc-spdd-sync.prompt.md`

## Invoke SDLC-SPDD Skills

Run these in **Copilot Chat** — not in a terminal. See [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

In GitHub Copilot Chat, invoke prompt files with slash commands:

    /sdlc-spdd-init
    /sdlc-spdd-analysis @requirements/order-status-api.md
    /sdlc-spdd-plan @spdd/analysis/FEAT-001-order-status-api-analysis.md
    /sdlc-spdd-architect @spdd/canvas/FEAT-001-order-status-api.md
    /sdlc-spdd-code @spdd/canvas/FEAT-001-order-status-api.md operation T01
    /sdlc-spdd-api-test @spdd/canvas/FEAT-001-order-status-api.md
    /sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md
    /sdlc-spdd-prompt-update @spdd/canvas/FEAT-001-order-status-api.md
    /sdlc-spdd-retro @spdd/canvas/FEAT-001-order-status-api.md
    /sdlc-spdd-sync @spdd/canvas/FEAT-001-order-status-api.md

If slash commands are not listed, reference a prompt file directly:

    #prompt:sdlc-spdd-plan

or run:

    Chat: Run Prompt

from the Command Palette and select the prompt.

## Start Work in Copilot

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

Use the Work ID and file references.

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md before answering. Which operation is next?

    For FEAT-001 operation T01, inspect the current diff. Are any files unrelated to the approved operation?

    For BUG-003, read @agent-context/memory/known-pitfalls.md. What should I check before review?

## Copilot-Specific Notes

- `.github/copilot-instructions.md` is applied automatically by supported Copilot Chat clients.
- Prompt files live in `.github/prompts/` and use the `*.prompt.md` extension.
- Prompt files are manually invoked; they do not run on every chat request.
- Keep source code changes out of planning, architecture, retro, and sync prompts unless explicitly requested.
- Use `@` file references when your Copilot client supports them; otherwise paste the relevant file path and ask Copilot to read it.
