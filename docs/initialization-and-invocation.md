# Initialization and Invocation

This guide shows how to initialize an application, start work, ask context-preserving questions, and invoke SDLC-SPDD skills from Cursor or GitHub Copilot.

## First-Time Application Setup

From this scaffold repository, install SDLC-SPDD into the target application.

Install the integrated combined system:

    ./scripts/setup-agent-prompts.sh --target /path/to/your/project --all

Install for Cursor:

    ./scripts/init-project.sh --target /path/to/your/project --cursor

Install for GitHub Copilot:

    ./scripts/init-project.sh --target /path/to/your/project --copilot

Install both assistant integrations:

    ./scripts/init-project.sh --target /path/to/your/project --cursor --copilot

Preview changes without writing files:

    ./scripts/init-project.sh --target /path/to/your/project --cursor --copilot --dry-run

Upgrade an existing older installation without overwriting implementation files or accumulated memory:

    ./scripts/upgrade-project.sh --target /path/to/your/project --all

The target application receives:

- `requirements/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `agent-context/memory/`
- `agent-context/features/`
- `agent-context/sessions/`
- `agent-context/playbooks/`
- `agent-context/harness/`
- `.cursor/commands/` when `--cursor` is used
- `.github/copilot-instructions.md` and `.github/prompts/` when `--copilot` is used
- `scripts/sdlc-spdd/` runtime session scripts

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

Expected result:

- Stack markers are detected.
- Memory and harness files are created or preserved.
- Existing application code is not changed.
- The assistant recommends the next SDLC-SPDD skill.

## Start or Resume an Agent Session

Before asking a new agent to continue previous work, create a session brief:

    cd /path/to/your/project
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code

If the work may have drifted between the feature workspace and canonical canvas, resync first:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id FEAT-001-order-status-api --check-only

Then ask the assistant:

    For FEAT-001-order-status-api, read @agent-context/sessions/current-session.md and continue with the recommended SDLC-SPDD command.

## How to Start Work

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

Always include the Work ID and point to the active artifacts. This helps the assistant answer from the design contract instead of from a disconnected chat memory.

Good context-preserving prompts:

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md and @agent-context/features/FEAT-001-order-status-api/progress-log.md. What should I do next?

    For BUG-003, compare @spdd/canvas/BUG-003-null-discount-checkout.md with the current diff. Are we still inside the approved operation?

    Using @agent-context/memory/known-pitfalls.md and @spdd/canvas/FEAT-001-order-status-api.md, what risks should I check before coding T02?

    For FEAT-001, summarize the current state in three bullets: completed operations, open risks, and next command.

Avoid context-losing prompts:

    What now?
    Can you fix it?
    Continue.
    Is this okay?

If you need to ask a quick question, still anchor it:

    For FEAT-001, quick question: does T02 require a repository change or only a service-layer change?

## Invoking the SDLC-SPDD Skills

| Skill | Cursor invocation | Copilot invocation | Use when |
|-------|-------------------|--------------------|----------|
| Initialize | `/sdlc-spdd-init` | `/sdlc-spdd-init` | First time in a target application |
| Plan | `/sdlc-spdd-plan @requirements/file.md` | `/sdlc-spdd-plan @requirements/file.md` | Convert requirement, Jira issue, or GitHub issue into a canvas |
| Architect | `/sdlc-spdd-architect @spdd/canvas/WORK-ID.md` | `/sdlc-spdd-architect @spdd/canvas/WORK-ID.md` | Harden the canvas before coding |
| Code | `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01` | `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01` | Implement one approved operation |
| Review | `/sdlc-spdd-review @spdd/canvas/WORK-ID.md` | `/sdlc-spdd-review @spdd/canvas/WORK-ID.md` | Review changes against the canvas |
| Prompt update | `/sdlc-spdd-prompt-update @spdd/canvas/WORK-ID.md` | `/sdlc-spdd-prompt-update @spdd/canvas/WORK-ID.md` | Update the canvas first when requirements, acceptance criteria, or behavior intent change |
| Retro | `/sdlc-spdd-retro @spdd/canvas/WORK-ID.md` | `/sdlc-spdd-retro @spdd/canvas/WORK-ID.md` | Capture reusable learnings |
| Sync | `/sdlc-spdd-sync @spdd/canvas/WORK-ID.md` | `/sdlc-spdd-sync @spdd/canvas/WORK-ID.md` | Reconcile implementation reality with the canvas |

## Daily Invocation Pattern

For most work, use this sequence:

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
