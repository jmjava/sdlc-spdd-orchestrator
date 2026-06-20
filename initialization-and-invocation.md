# Initialization and Invocation

This guide is for **Cursor, Copilot, and Claude Code invocation**: slash commands, `#prompt:` fallbacks, and side-by-side examples per assistant. It does not duplicate install steps, session rhythm, or the canonical prompt library.

| Need | Open |
|------|------|
| Install, upgrade, verify | [Installing into your project](installing-into-your-project.md) |
| Copy-paste prompts | [Session prompt standard](session-prompt-standard.md) |
| Script sequences and checklists | [Daily runbook](daily-runbook.md) |
| **Cursor / Copilot / Claude Code command syntax** | **This page** |

## How to Run Assistant Commands

Lines like `/sdlc-spdd-init` are **not shell commands**. Do not paste them into a terminal. They are **prompts you send in the AI chat** inside your editor (Cursor Chat/Agent, GitHub Copilot Chat, or Claude Code).

### Cursor

1. Open the **target application** folder in Cursor (not the orchestrator repo, unless you are developing the framework itself).
2. Open **Chat** or **Agent** (`Ctrl+L` / `Cmd+L`, or the chat panel).
3. Type `/` and pick `sdlc-spdd-init` from the list, **or** type `/sdlc-spdd-init` and press Enter.

The command runs as a chat message. The agent reads `.cursor/commands/sdlc-spdd-init.md` and follows that skill.

### GitHub Copilot Chat

1. Open the target application in VS Code (or another Copilot-enabled editor).
2. Open **Copilot Chat**.
3. Type `/sdlc-spdd-init` and send.

If slash commands do not appear:

    #prompt:sdlc-spdd-init

Or: **Command Palette** → **Chat: Run Prompt** → choose `sdlc-spdd-init`.

### Claude Code

1. Open the **target application** folder in Claude Code.
2. Type `/` and pick `sdlc-spdd-init` from the list, **or** type `/sdlc-spdd-init` and press Enter.

The command runs as a chat message. Claude Code reads `.claude/commands/sdlc-spdd-init.md` and follows that skill, with `CLAUDE.md` loaded automatically as project memory.

### Shell commands vs assistant commands

| Kind | Example | Where you run it |
|------|---------|------------------|
| **Shell** (terminal) | `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001 --phase plan` | Terminal in the target project |
| **Assistant** (chat) | `/sdlc-spdd-init`, `/sdlc-spdd-plan @requirements/foo.md` | Cursor, Copilot, or Claude Code **chat** input |

All `/sdlc-spdd-*` lines in the docs are **assistant commands** unless they start with `./` or `cd`.

## First-Time Application Setup

Default install (from this orchestrator repo):

    ./scripts/setup-agent-prompts.sh --target /path/to/your/project --all
    ./scripts/verify-project-install.sh --target /path/to/your/project

Full install options, upgrade path, and what gets created: [Installing into your project](installing-into-your-project.md).

## Initialize Context Inside the Application

After the scaffold files are installed, open the target application in your AI coding tool and invoke initialization.

Cursor:

    /sdlc-spdd-init

GitHub Copilot Chat:

    /sdlc-spdd-init

If slash commands are not visible in Copilot Chat, use one of these options:

    #prompt:sdlc-spdd-init

or open the Command Palette and run:

    Chat: Run Prompt

Then choose `sdlc-spdd-init`.

Claude Code:

    /sdlc-spdd-init

Expected result:

- Stack markers are detected.
- Memory and harness files are created or preserved.
- Existing application code is not changed.
- The assistant recommends the next SDLC-SPDD skill.

## Start or Resume an Agent Session

Script sequence and checklists: [Morning or Start-of-Session Check](daily-runbook.md#morning-or-start-of-session-check) in Daily runbook. Resume prompt wording: [Start of session](session-prompt-standard.md#start-of-session) in Session prompt standard.

Before asking a new agent to continue previous work:

1. Check canvas sync (optional, does not create a session brief):

       ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --check-only

2. Create a session brief:

       cd /path/to/your/project
       ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code

3. **Paste the Resume Prompt** from `agent-context/sessions/current-session.md`. Do not paraphrase — the brief embeds **Resolved Context** (phase files, extensions, Work ID artifacts, area-filtered index rows) and the Resume Prompt points at only those files. See [Session prompt standard](session-prompt-standard.md).

To reconcile canvas drift before step 2, use `resync-agent-session.sh --from-canvas --force` or `--from-feature --force`. Default authority: canonical `spdd/canvas/<WORK-ID>.md`.

## How to Start Work

Canonical prompt wording: [Session prompt standard](session-prompt-standard.md) and [Triage](session-prompt-standard.md#triage-no-work-id-yet). Below: **Cursor, Copilot, and Claude Code invocation** examples for common entry points (plain language, files, Jira, GitHub, bugs). The slash-command syntax (`/sdlc-spdd-* @file`) is identical across all three assistants.

Use one Work ID for each unit of work. Good IDs include:

- `FEAT-001-order-status-api`
- `BUG-003-null-order-total`
- `REF-002-split-billing-service`
- `DOC-004-runbook-refresh`

### Start from a plain-language idea

Cursor:

    /sdlc-spdd-plan Create an endpoint that returns the current status for an order by ID.

Copilot Chat:

    /sdlc-spdd-plan Create an endpoint that returns the current status for an order by ID.

Claude Code:

    /sdlc-spdd-plan Create an endpoint that returns the current status for an order by ID.

### Start from a requirement file

Create a requirement document first:

    requirements/order-status-api.md

Then invoke planning:

    /sdlc-spdd-plan @requirements/order-status-api.md

### Start from a Jira issue

Use the Jira key or URL and include the project context that the assistant needs.

    /sdlc-spdd-plan Jira ABC-123: add order status lookup. Link this work to https://jira.example.com/browse/ABC-123 and create the canvas as FEAT-001-order-status-api.

If the issue text is not available to the assistant, paste the acceptance criteria:

    /sdlc-spdd-plan Jira ABC-123

    Acceptance criteria:
    - GET /orders/{id}/status returns the latest status.
    - Unknown orders return 404.
    - The response includes orderId, status, and updatedAt.

### Start from a GitHub issue

    /sdlc-spdd-plan GitHub issue https://github.com/example/orders-api/issues/42. Create a REASONS Canvas and link the issue in Metadata.

### Start from a bug report

    /sdlc-spdd-plan BUG: checkout fails when an order has no discount. Use BUG-003-null-discount-checkout as the Work ID. Identify the likely code path, tests, and safeguards before coding.

### Start from an existing canvas

If a canvas already exists, continue from it instead of starting over.

    /sdlc-spdd-architect @spdd/canvas/FEAT-001-order-status-api.md

or:

    /sdlc-spdd-code @spdd/canvas/FEAT-001-order-status-api.md operation T01

## How to Ask Questions That Keep Context

Always include the Work ID and point to the active artifacts. More examples and anti-patterns: [During session](session-prompt-standard.md#during-session) and [Anti-patterns](session-prompt-standard.md#anti-patterns) in Session prompt standard.

Good (Cursor, Copilot, or Claude Code):

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md and @agent-context/features/FEAT-001-order-status-api/progress-log.md. What should I do next?

Avoid:

    What now? / Continue. / Can you fix it?

## Invoking the SDLC-SPDD Skills

The same `/sdlc-spdd-*` syntax works in Cursor, Copilot, and Claude Code.

| Skill | Invocation (Cursor / Copilot / Claude Code) | Use when |
|-------|---------------------------------------------|----------|
| Initialize | `/sdlc-spdd-init` | First time in a target application |
| Plan | `/sdlc-spdd-plan @requirements/file.md` | Convert requirement, Jira issue, or GitHub issue into a canvas |
| Architect | `/sdlc-spdd-architect @spdd/canvas/WORK-ID.md` | Harden the canvas before coding |
| Code | `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01` | Implement one approved operation |
| Review | `/sdlc-spdd-review @spdd/canvas/WORK-ID.md` | Review changes against the canvas |
| Prompt update | `/sdlc-spdd-prompt-update @spdd/canvas/WORK-ID.md` | Update the canvas first when requirements, acceptance criteria, or behavior intent change |
| Retro | `/sdlc-spdd-retro @spdd/canvas/WORK-ID.md` | Capture reusable learnings |
| Sync | `/sdlc-spdd-sync @spdd/canvas/WORK-ID.md` | Reconcile implementation reality with the canvas |

## Daily Invocation Pattern

Full step order and part ownership: [Workflow](workflow.md). Typical command sequence:

    /sdlc-spdd-plan @requirements/<topic>.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T02
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Use review after each coding operation when the change is risky, touches shared behavior, or changes user-visible behavior.

If the requirement or intended behavior changes midstream, update the canvas before coding:

    /sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md

If a refactor changes only internal structure, review the change and then sync the canvas:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

End each meaningful session by persisting memory:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --next "<next command>"
