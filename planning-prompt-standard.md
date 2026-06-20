# Planning Prompt Standard

This is the prompt contract for the **planning layer** in SDLC-SPDD: `ROADMAP.md`, `milestone-*.md`, and `session-notes/`. Use it when you need copy-paste prompts for delivery narrative, milestone mapping, daily session capture, and roadmap refresh.

**Not the default.** For day-to-day sessions, start with [Session prompt standard](session-prompt-standard.md). Open this page when your question is specifically about roadmap, milestones, or session notes. See [Which prompt standard?](session-prompt-standard.md#which-prompt-standard) for the full decision guide.

For REASONS Canvas governance, see [SPDD prompt standard](spdd-prompt-standard.md).

## Required Planning Prompt Fields

| Field | Required | Example |
|-------|----------|---------|
| Milestone reference | When work belongs to a milestone | `@milestone-1.md` |
| Roadmap reference | For delivery context | `@ROADMAP.md` |
| Session note reference | When continuing same day | `@session-notes/2026-06-06.md` |
| Work ID | When linking planning to SPDD | `FEAT-001-order-status-api` |
| Roadmap note / summary | At milestone progress | `--roadmap-note "..."` |

## Planning Artifact Roles

| Artifact | Prompt use |
|----------|------------|
| `ROADMAP.md` | Current focus, milestone list, managed SPDD work summary |
| `milestone-*.md` | Goal, scope checklist, linked Work IDs, milestone summaries |
| `requirements/milestones/<WORK-ID>.md` | Milestone-derived requirement stub for plan prompts |
| `session-notes/YYYY-MM-DD.md` | Daily agent-session narrative |

## Milestone → Governed Work

### Map checklist items to Work IDs and draft canvases

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Single item:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --item "Add order status API" --type feature

The script prints **Next SPDD prompts** for each created Work ID.

### Plan with milestone context

    /sdlc-spdd-plan @requirements/<topic>.md @ROADMAP.md @milestone-1.md

Or:

    /sdlc-spdd-plan Jira ABC-123 for milestone-1.md. Link this Work ID to the milestone and update the canvas Metadata.

Metadata prompt:

    For <WORK-ID>, update @spdd/canvas/<WORK-ID>.md Metadata to include Roadmap: ROADMAP.md and Milestone: milestone-1.md.

## Session Start with Planning Context

Generate session brief (includes planning files in resume prompt when present):

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase> --milestone milestone-1.md

Morning status with planning layer:

    For <WORK-ID>, read @agent-context/sessions/current-session.md first.

    For <WORK-ID>, read @spdd/canvas/<WORK-ID>.md and @agent-context/features/<WORK-ID>/progress-log.md. Summarize current status, next operation, and open risks.

    Also read @ROADMAP.md, @milestone-1.md, and @session-notes/YYYY-MM-DD.md if they exist.

    Recommend the next SDLC-SPDD command.

## Session Capture to All Layers

### Full capture with milestone and roadmap

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase <phase> \
      --summary "<completed work>" \
      --validation "<tests or checks>" \
      --milestone milestone-1.md \
      --roadmap-note "<roadmap-level progress>" \
      --next "<next command>"

When `--milestone` is omitted, the script auto-detects the milestone from `milestone-*.md` files containing the Work ID.

### Session note only (skip milestone/roadmap)

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase <phase> \
      --summary "<completed work>" \
      --validation "<tests>" \
      --next "<next command>"

### Skip daily session note

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --summary "<summary>" \
      --no-session-note

### End-of-session planning summary (prompt)

    For <WORK-ID>, summarize completed work, validation, decisions, and next command. Include a one-line milestone update for @milestone-1.md and a roadmap-level note for @ROADMAP.md.

## Roadmap Refresh from SPDD

Sync managed summary from canvas metadata:

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

After sync, review prompt:

    Read @ROADMAP.md. Review the SDLC-SPDD Work Summary table. Does Current Focus match the active Work ID and phase? Suggest updates if not.

Dry-run first:

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target . --dry-run

The managed section is between:

    <!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->
    <!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->

Handwritten roadmap content outside those markers is preserved.

## Import Historical Session Notes

Import all:

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --all

Import one file:

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --file session-notes/2026-06-06.md

After import, review prompt:

    Read @agent-context/memory/session-history.md entries imported from session-notes. Summarize recurring themes, open risks, and Work IDs mentioned.

## Suggested Roadmap Content Prompts

Draft current focus:

    For <WORK-ID>, draft a Current Focus block for @ROADMAP.md with Work ID, active milestone, current phase, and next command.

Draft milestone linked-work row:

    For <WORK-ID>, draft a Linked Work table row for @milestone-1.md with source issue, status, and notes.

## Planning Anti-Patterns

| Bad practice | Why it fails |
|--------------|--------------|
| Putting implementation detail only in chat | Lost when session ends — use session notes |
| Replacing canvas with milestone checklist | Milestones inform; canvases govern |
| Editing roadmap without syncing from SPDD | Summary drifts from canvas metadata |
| Skipping milestone link when Work ID is not in any `milestone-*.md` yet | Milestone story becomes stale — add `--milestone` or link the Work ID in Linked Work first |
| Deleting session notes after capture | Historical narrative lost — import first with summarize script |

## Planning Scripts and Generated Prompts

| Script | Planning output |
|--------|-----------------|
| `start-agent-session.sh` | Resume prompt with `@ROADMAP.md`, `@milestone-*.md`, `@session-notes/` |
| `capture-session-memory.sh` | Writes session notes, milestone, roadmap; suggests full capture command |
| `create-work-from-milestone.sh` | Updates milestone work map; prints SPDD next steps |
| `sync-roadmap-from-spdd.sh` | Refreshes managed roadmap summary; prints review prompt |
| `summarize-session-notes.sh` | Imports notes to memory; prints review prompt |

## Where Planning Prompts Are Defined

| Source | What it standardizes |
|--------|---------------------|
| This page | Roadmap, milestone, and session-note prompts |
| `templates/project-docs/ROADMAP.md` | Roadmap scaffold |
| `templates/project-docs/milestone-1.md` | Milestone scaffold |
| `docs/roadmap-milestones-and-session-notes.md` | Operational planning guide |
| `start-agent-session.sh` | Planning refs in generated resume prompt |

## Read Next

- [What planning brings](what-planning-brings.md) — planning layer value proposition
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md) — file layout and workflows
- [SPDD prompt standard](spdd-prompt-standard.md) — canvas governance prompts
- [Session prompt standard](session-prompt-standard.md) — unified session prompts
