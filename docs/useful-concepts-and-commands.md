# Top Useful Concepts and Commands

This page explains **what things mean** (Work ID, canvas, operation, sync, memory). For a dense **command cheat sheet** to print or keep open, use [Cheat sheet](sdlc-spdd-cheat-sheet.md). For copy-paste prompts, use [Session prompt standard](session-prompt-standard.md).

## Top Concepts

### Work ID

A stable identifier for one unit of work.

Examples:

- `FEAT-001-order-status-api`
- `BUG-003-null-discount-checkout`
- `REF-002-split-billing-service`

Use the Work ID in prompts, canvas files, progress logs, reviews, sync logs, branches, commits, and Jira updates.

### REASONS Canvas

The SPDD design contract for a Work ID.

Sections:

- Requirements
- Entities
- Approach
- Structure
- Operations
- Norms
- Safeguards

Canonical path:

    spdd/canvas/<WORK-ID>.md

### Operation

A small, approved implementation step in the canvas.

Example:

    T01 - Add service method
    T02 - Add API endpoint
    T03 - Add tests

Coding should implement one operation at a time.

### Prompt Update

Use prompt update when the intended behavior changes.

Command:

    /sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md

Rule:

    Behavior changes update the canvas before code.

### Sync

Use sync when reviewed implementation reality should be reflected back into the canvas.

Command:

    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Rule:

    Non-behavioral refactors sync the canvas after review.

### Session Brief

A file that lets a new agent session resume work from repository context.

Current session:

    agent-context/sessions/current-session.md

Create one:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

### Durable Memory

Project knowledge that survives chat sessions.

Important files:

- `agent-context/memory/project-memory.md`
- `agent-context/memory/session-history.md`
- `agent-context/memory/architecture-decisions.md`
- `agent-context/memory/known-pitfalls.md`
- `agent-context/memory/reusable-patterns.md`

### Roadmap and Milestones

Project-owned planning files that connect SDLC-SPDD work to larger delivery goals.

Common files:

- `ROADMAP.md`
- `milestone-1.md`
- `milestone-2.md`
- `session-notes/YYYY-MM-DD.md`

Use roadmap and milestone docs to give planning agents delivery context. Use REASONS Canvas files to govern each Work ID.

## Commands and Prompts

`/sdlc-spdd-*` commands run in **AI chat** (Cursor/Copilot/Claude Code), not a terminal. [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

Command list (install, lifecycle, scripts): [Cheat sheet](sdlc-spdd-cheat-sheet.md).

Copy-paste prompts: [Session prompt standard](session-prompt-standard.md) — see [Which prompt standard?](session-prompt-standard.md#which-prompt-standard) when drilling into SPDD or Planning.

## Common Mistakes to Avoid

- Starting code before `/sdlc-spdd-architect`.
- Asking "continue" without a Work ID or session brief.
- Implementing multiple operations in one coding pass.
- Using `/sdlc-spdd-sync` for a new behavior requirement.
- Forgetting to capture memory at the end of a session.
- Editing application behavior after Jira acceptance criteria changed without prompt-update.

## Read Next

- [What SDLC brings](what-sdlc-brings.md)
- [Session prompt standard](session-prompt-standard.md)
- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Daily runbook](daily-runbook.md)
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md)
- [Agent session scripts](agent-session-scripts.md)
- [SPDD compliance](spdd-compliance.md)
