# SDLC-SPDD Cheat Sheet

**One-page command reference** for print/PDF or a second monitor. For concept definitions (what is a Work ID, operation, sync?), see [Top useful concepts and commands](useful-concepts-and-commands.md). For prompt wording, see [Session prompt standard](session-prompt-standard.md).

`/sdlc-spdd-*` rows below are **AI chat commands** (Cursor/Copilot/Claude Code), not terminal commands. `./scripts/...` rows are shell. [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

Export options:

- Open this Markdown file in VS Code preview and print to PDF.
- Publish `docs/` through GitHub Pages and print the page to PDF from a browser.
- Use any Markdown-to-PDF converter approved by your team.

Start here (everything else is reference):

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md) — hands-on first session
- [Three-part operating path](three-part-operating-path.md) — Planning → SPDD → SDLC loop
- [Session prompt standard](session-prompt-standard.md) (default) — [Which one?](session-prompt-standard.md#which-prompt-standard)

## Install

From the **orchestrator repo** clone (not your app folder):

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all
    ./scripts/verify-project-install.sh --target /path/to/app

After install, from your **target app** folder:

    ./scripts/sdlc-spdd/verify-project-install.sh --target .

One assistant only (advanced):

    ./scripts/init-project.sh --target /path/to/app --cursor
    ./scripts/init-project.sh --target /path/to/app --copilot
    ./scripts/init-project.sh --target /path/to/app --claude

Target-local docs:

    docs/sdlc-spdd/

Project planning:

    ROADMAP.md
    milestone-1.md
    session-notes/

Layer model:

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
      -> inform and summarize
    spdd/canvas/ + agent-context/
      -> govern and remember
    code / reviews / sync logs
      -> execute and validate

Upgrade older install:

    ./scripts/upgrade-project.sh --target /path/to/app --all

## Workflow CLI (daily rhythm)

Orient first:

    ./scripts/sdlc-spdd/sdlc.sh next
    /sdlc-spdd-whereami

Claim and resume:

    ./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>
    ./scripts/sdlc-spdd/sdlc.sh resume <WORK-ID> [--phase <phase>]
    ./scripts/sdlc-spdd/sdlc.sh start

Phase transitions:

    ./scripts/sdlc-spdd/sdlc.sh advance
    ./scripts/sdlc-spdd/sdlc.sh skip <phase> --reason "..."
    ./scripts/sdlc-spdd/sdlc.sh shelf --reason "..."
    ./scripts/sdlc-spdd/sdlc.sh list-shelved
    ./scripts/sdlc-spdd/sdlc.sh sync

Team coordination (commit `agent-context/work-registry.tsv` after claim/release):

    ./scripts/sdlc-spdd/sdlc.sh team
    ./scripts/sdlc-spdd/sdlc.sh list-work
    ./scripts/sdlc-spdd/sdlc.sh release --reason "..."

Guarded capture (pointer must match Work ID):

    ./scripts/sdlc-spdd/sdlc.sh capture --summary "..." --validation "..." --next "..."

Local state (gitignored): `.sdlc/pointer`, `.sdlc/workflows/`.

In the orchestrator repo, use `./scripts/sdlc.sh` instead of `./scripts/sdlc-spdd/sdlc.sh`.

## Session Handoff

Start or resume (prefer workflow CLI):

    ./scripts/sdlc-spdd/sdlc.sh resume <WORK-ID> --phase <phase>
    ./scripts/sdlc-spdd/sdlc.sh start

Low-level equivalent:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase> [--milestone milestone-1.md]

Paste the Resume Prompt from `agent-context/sessions/current-session.md`. Load only files listed under **Resolved Context** in that brief.

Refresh context after adding extensions or `#SkillName` skills:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase <phase> --work-id <WORK-ID>
    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --text "#TDD #java"

Check previous work:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

Capture memory (prefer guarded capture):

    ./scripts/sdlc-spdd/sdlc.sh capture --summary "<summary>" --validation "<tests>" --next "<next command>"

Low-level equivalent:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --next "<next command>"

Capture milestone progress:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --milestone milestone-1.md --roadmap-note "<progress>" --next "<next command>"

Map milestone items:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Refresh roadmap:

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

## Lifecycle

    Initialize -> Analysis -> Plan -> Architect -> Code -> API Test -> Review -> Retro -> Sync

## Start Work

Begin with `/sdlc-spdd-analysis` (Fowler Step 3). It extracts domain keywords,
scans only the relevant code areas, and writes `spdd/analysis/<WORK-ID>-analysis.md`.
`/sdlc-spdd-plan` requires that artifact and stops if it is missing.

Plain requirement:

    /sdlc-spdd-analysis Create an endpoint that returns order status by ID.

Requirement file:

    /sdlc-spdd-analysis @requirements/order-status-api.md

Jira:

    /sdlc-spdd-analysis Jira ABC-123: add order status lookup. Link https://jira.example.com/browse/ABC-123.

GitHub issue:

    /sdlc-spdd-analysis GitHub issue https://github.com/org/repo/issues/42.

Bug:

    /sdlc-spdd-analysis BUG: checkout fails when an order has no discount. Use BUG-003-null-discount-checkout.

Then index the analysis so domain keywords and code areas feed decision memory,
and continue to planning:

    ./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>
    /sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md

## Invoke Skills

| Need | Command |
|------|---------|
| What now? (orientation) | `/sdlc-spdd-whereami` or `./scripts/sdlc-spdd/sdlc.sh next` |
| Initialize repo context | `/sdlc-spdd-init` |
| Analyze requirement + scope code areas | `/sdlc-spdd-analysis @requirements/file.md` |
| Turn analysis into canvas | `/sdlc-spdd-plan @spdd/analysis/WORK-ID-analysis.md` |
| Harden design before coding | `/sdlc-spdd-architect @spdd/canvas/WORK-ID.md` |
| Implement one operation | `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01` |
| Verify with API tests | `/sdlc-spdd-api-test @spdd/canvas/WORK-ID.md` |
| Review implementation | `/sdlc-spdd-review @spdd/canvas/WORK-ID.md` |
| Update changed intent | `/sdlc-spdd-prompt-update @spdd/canvas/WORK-ID.md` |
| Capture learnings | `/sdlc-spdd-retro @spdd/canvas/WORK-ID.md` |
| Reconcile drift | `/sdlc-spdd-sync @spdd/canvas/WORK-ID.md` |

## Ask Questions That Keep Context

Prompt patterns: [During session](session-prompt-standard.md#during-session) and [Anti-patterns](session-prompt-standard.md#anti-patterns) in Session prompt standard.

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

Create Jira draft in the milestone requirement file:

    requirements/milestones/<WORK-ID>.md   →   ## Jira (Key, Summary, Type, Acceptance, …)

See [requirements/milestones/README.md](../requirements/milestones/README.md). On claim, `./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>` auto-links the Key into `work-registry.tsv`.

Draft for Jira UI:

    Draft a Jira issue from requirements/milestones/<WORK-ID>.md ## Jira. Include summary, business value, scope in/out, Given/When/Then acceptance criteria, labels, components, and links.

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
