# SDLC-SPDD Cheat Sheet

**One-page command reference** for print/PDF or a second monitor. For concept definitions (what is a Work ID, operation, sync?), see [Top useful concepts and commands](useful-concepts-and-commands.md). For prompt wording, see [Session prompt standard](session-prompt-standard.md).

`/sdlc-spdd-*` rows below are **AI chat lifecycle commands** (Cursor/Copilot/Claude Code), not terminal commands. `/sdlc-*` workflow commands (`claim`, `shelf`, `advance`, `next`, `team`) are chat wrappers for `sdlc.sh`. `./scripts/...` rows are shell. [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

Export options:

- Open this Markdown file in VS Code preview and print to PDF.
- Print this cheat sheet from a browser (File → Print → Save as PDF).
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

    ./sdlc-spdd/scripts/verify-project-install.sh --target .

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

    ./sdlc-spdd/scripts/sdlc.sh next
    /sdlc-next
    /sdlc-spdd-whereami

Claim and resume:

    ./sdlc-spdd/scripts/sdlc.sh claim <WORK-ID>
    /sdlc-claim <WORK-ID>
    ./sdlc-spdd/scripts/sdlc.sh claim <WORK-ID> --force   # take over after coordinating
    ./sdlc-spdd/scripts/sdlc.sh resume <WORK-ID> [--phase <phase>] [--force]
    ./sdlc-spdd/scripts/sdlc.sh start

Phase transitions:

    ./sdlc-spdd/scripts/sdlc.sh advance
    ./sdlc-spdd/scripts/sdlc.sh advance --force   # override Ready For Coding gate into code
    /sdlc-advance
    ./sdlc-spdd/scripts/sdlc.sh skip <phase> --reason "..."
    ./sdlc-spdd/scripts/sdlc.sh shelf --reason "..."
    /sdlc-shelf [reason]
    ./sdlc-spdd/scripts/sdlc.sh list-shelved
    ./sdlc-spdd/scripts/sdlc.sh sync

Team coordination (commit `spdd/memory/registry.jsonl` after claim/release):

    ./sdlc-spdd/scripts/sdlc.sh team
    /sdlc-team
    ./sdlc-spdd/scripts/sdlc.sh list-work
    ./sdlc-spdd/scripts/sdlc.sh release --reason "..."

Guarded capture (pointer must match Work ID):

    ./sdlc-spdd/scripts/sdlc.sh capture --summary "..." --validation "..." --next "..."

Local state (gitignored): `.sdlc/pointer`, `.sdlc/workflows/`.

In the orchestrator repo, use `./scripts/sdlc.sh` instead of `./sdlc-spdd/scripts/sdlc.sh`.

Assistant workflow commands (`/sdlc-claim`, `/sdlc-shelf`, `/sdlc-advance`, `/sdlc-next`, `/sdlc-team`) wrap the same `sdlc.sh` actions from chat. Lifecycle skills remain `/sdlc-spdd-*`.

## Session Handoff

Start or resume (prefer workflow CLI):

    ./sdlc-spdd/scripts/sdlc.sh resume <WORK-ID> --phase <phase>
    ./sdlc-spdd/scripts/sdlc.sh start

Low-level equivalent:

    ./sdlc-spdd/scripts/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase> [--milestone milestone-1.md]

Paste the Resume Prompt from `.sdlc/sessions/current-session.md`. Load only files listed under **Resolved Context** in that brief; fetch lesson bodies on demand.

Refresh context after adding extensions or `#SkillName` skills:

    ./sdlc-spdd/scripts/resolve-agent-context.sh --target . --phase <phase> --work-id <WORK-ID>
    ./sdlc-spdd/scripts/resolve-agent-context.sh --target . --text "#TDD #java"

Check previous work:

    ./sdlc-spdd/scripts/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

Capture memory (prefer guarded capture):

    ./sdlc-spdd/scripts/sdlc.sh capture --summary "<summary>" --validation "<tests>" --next "<next command>"

Low-level equivalent:

    ./sdlc-spdd/scripts/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --next "<next command>"

Capture milestone progress:

    ./sdlc-spdd/scripts/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --milestone milestone-1.md --roadmap-note "<progress>" --next "<next command>"

Map milestone items:

    ./sdlc-spdd/scripts/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Refresh roadmap:

    ./sdlc-spdd/scripts/sync-roadmap-from-spdd.sh --target .

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

    ./sdlc-spdd/scripts/index-spdd-analysis.sh --target . --work-id <WORK-ID>
    /sdlc-spdd-plan @spdd/analysis/<WORK-ID>-analysis.md

## Invoke Skills

| Need | Command |
|------|---------|
| What now? (orientation) | `/sdlc-next`, `/sdlc-spdd-whereami`, or `./sdlc-spdd/scripts/sdlc.sh next` |
| Claim / shelf / advance / team | `/sdlc-claim`, `/sdlc-shelf`, `/sdlc-advance`, `/sdlc-team` |
| Take over a teammate claim | `/sdlc-claim <WORK-ID> --force` or `sdlc.sh claim <WORK-ID> --force` |
| Initialize repo context | `/sdlc-spdd-init` |
| Analyze requirement + scope code areas | `/sdlc-spdd-analysis @requirements/file.md` |
| Turn analysis into canvas | `/sdlc-spdd-plan @spdd/analysis/WORK-ID-analysis.md` |
| Harden design before coding | `/sdlc-spdd-architect @spdd/canvas/WORK-ID.md` |
| Implement one operation | `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01` |
| Verify with API tests | `/sdlc-spdd-api-test @spdd/canvas/WORK-ID.md` |
| Review implementation | `/sdlc-spdd-review @spdd/canvas/WORK-ID.md` |
| Draft commit message from current changes | `/sdlc-spdd-commit-message [hint] [WORK-ID]` |
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

Use Jira for delivery status; use requirement docs + canvas for design truth. See [Issue sync and branching](issue-sync-and-branching.md).

Create Jira draft in the milestone requirement file:

    requirements/milestones/<WORK-ID>.md   →   ## Jira (Key, Summary, Type, Acceptance, …)

See [requirements/milestones/README.md](../requirements/milestones/README.md). On claim, `./sdlc-spdd/scripts/sdlc.sh claim <WORK-ID>` auto-links the Key into the registry event note.

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
