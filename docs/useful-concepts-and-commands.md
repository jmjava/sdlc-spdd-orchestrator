# Top Useful Concepts and Commands

This is a quick reference for the SDLC-SPDD ideas and commands you will use most.

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

## Top Commands

### Install into a target project

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

### Upgrade an older install

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run
    ./scripts/upgrade-project.sh --target /path/to/app --all

### Initialize context

    /sdlc-spdd-init

### Start work

    /sdlc-spdd-plan @requirements/<topic>.md

or:

    /sdlc-spdd-plan Jira ABC-123: <summary>. Link https://jira.example.com/browse/ABC-123.

### Harden architecture

    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

### Code one operation

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01

### Review

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

### Update changed intent

    /sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md

### Sync implementation drift

    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

### Capture retro

    /sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md

### Start a new agent session

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

### Check previous work

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

### Capture session memory

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase <phase> \
      --summary "<summary>" \
      --validation "<tests>" \
      --next "<next command>"

### Capture milestone and roadmap progress

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase <phase> \
      --summary "<summary>" \
      --validation "<tests>" \
      --milestone milestone-1.md \
      --roadmap-note "<roadmap-level progress>" \
      --next "<next command>"

### Create work from milestone checklist items

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

### Sync roadmap from SPDD canvases

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

### Import existing session notes into memory

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --all

### Validate a canvas

    ./scripts/sdlc-spdd/validate-reasons-canvas.sh spdd/canvas/<WORK-ID>.md

## Useful Prompt Patterns

### Ask a context-preserving question

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md and @agent-context/sessions/current-session.md before answering. <question>

### Continue interrupted work

    For <WORK-ID>, read the current session, canvas, progress log, review report, sync log, and current diff. Tell me the next SDLC-SPDD command.

### Check scope before coding

    For <WORK-ID> operation T01, inspect the canvas and current diff. Are any changes outside the approved operation?

### Draft a Jira update

    For <WORK-ID>, read the canvas, progress log, review report, and sync log. Draft a Jira update for <JIRA-KEY> with status, validation, risks, and next step.

### Capture handoff

    For <WORK-ID>, summarize completed work, tests, open risks, decisions, pitfalls, reusable patterns, and the next command.

## Common Mistakes to Avoid

- Starting code before `/sdlc-spdd-architect`.
- Asking "continue" without a Work ID or session brief.
- Implementing multiple operations in one coding pass.
- Using `/sdlc-spdd-sync` for a new behavior requirement.
- Forgetting to capture memory at the end of a session.
- Editing application behavior after Jira acceptance criteria changed without prompt-update.

## Read Next

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Daily runbook](daily-runbook.md)
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md)
- [Agent session scripts](agent-session-scripts.md)
- [SPDD compliance](spdd-compliance.md)
