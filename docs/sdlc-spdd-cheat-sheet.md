# SDLC-SPDD Cheat Sheet

PDF-friendly quick reference for daily use.

Export options:

- Open this Markdown file in VS Code preview and print to PDF.
- Publish `docs/` through GitHub Pages and print the page to PDF from a browser.
- Use any Markdown-to-PDF converter approved by your team.

Start here:

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [10,000-foot view](ten-thousand-foot-view.md)
- [Installing into your project](installing-into-your-project.md)
- [Maintaining your project](maintaining-your-project.md)
- [Top useful concepts and commands](useful-concepts-and-commands.md)

## Install

Cursor:

    ./scripts/init-project.sh --target /path/to/app --cursor

GitHub Copilot:

    ./scripts/init-project.sh --target /path/to/app --copilot

Both:

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot

Integrated setup:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

Target-local docs:

    docs/sdlc-spdd/

Project planning:

    ROADMAP.md
    milestone-1.md
    session-notes/

Upgrade older install:

    ./scripts/upgrade-project.sh --target /path/to/app --all

## Session Handoff

Start or resume:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

Check previous work:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

Capture memory:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --next "<next command>"

Capture milestone progress:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --milestone milestone-1.md --roadmap-note "<progress>" --next "<next command>"

## Lifecycle

    Initialize -> Plan -> Architect -> Code -> Review -> Retro -> Sync

## Start Work

Plain requirement:

    /sdlc-spdd-plan Create an endpoint that returns order status by ID.

Requirement file:

    /sdlc-spdd-plan @requirements/order-status-api.md

Jira:

    /sdlc-spdd-plan Jira ABC-123: add order status lookup. Link https://jira.example.com/browse/ABC-123.

GitHub issue:

    /sdlc-spdd-plan GitHub issue https://github.com/org/repo/issues/42.

Bug:

    /sdlc-spdd-plan BUG: checkout fails when an order has no discount. Use BUG-003-null-discount-checkout.

## Invoke Skills

| Need | Command |
|------|---------|
| Initialize repo context | `/sdlc-spdd-init` |
| Turn requirement into canvas | `/sdlc-spdd-plan @requirements/file.md` |
| Harden design before coding | `/sdlc-spdd-architect @spdd/canvas/WORK-ID.md` |
| Implement one task | `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01` |
| Review implementation | `/sdlc-spdd-review @spdd/canvas/WORK-ID.md` |
| Update changed intent | `/sdlc-spdd-prompt-update @spdd/canvas/WORK-ID.md` |
| Capture learnings | `/sdlc-spdd-retro @spdd/canvas/WORK-ID.md` |
| Reconcile drift | `/sdlc-spdd-sync @spdd/canvas/WORK-ID.md` |

## Ask Questions That Keep Context

Use:

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md before answering. <question>

Examples:

    For FEAT-001, what operation should I do next?

    For FEAT-001 T01, does the current diff stay inside the approved operation?

    For BUG-003, what test is required before review?

Avoid:

    What now?
    Continue.
    Fix it.

## One-Operation Coding Loop

    /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Repeat for T02, T03, and later operations.

## External Links

Canvas Metadata should include:

    - Work ID: FEAT-001-order-status-api
    - Source system: Jira
    - Source issue: ABC-123
    - Source URL: https://jira.example.com/browse/ABC-123
    - Docs URL: https://org.github.io/repo/spdd/FEAT-001-order-status-api.html
    - Pull request: TBD

Use Jira for status and ownership. Use GitHub Pages for published docs and runbooks.

Create Jira draft:

    Draft a Jira issue with summary, business value, scope in/out, Given/When/Then acceptance criteria, labels, components, and links.

Sync Jira:

    For <WORK-ID>, draft a Jira update for <JIRA-KEY> from the canvas, progress log, review report, and sync log.

## SPDD Rule

Behavior or requirement change:

    /sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md

Refactor with no behavior change:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md
    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

## End-of-Session Handoff

    For <WORK-ID>, summarize completed work, validation, open risks, and next command from the canvas, progress log, and current git status.
