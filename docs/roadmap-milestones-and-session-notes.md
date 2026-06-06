# Roadmap, Milestones, and Session Notes

SDLC-SPDD supports a project planning pattern based on:

- root `ROADMAP.md`
- root `milestone-1.md`, `milestone-2.md`, and later milestone files
- root `session-notes/` with daily agent-session summaries

These files are project planning artifacts, not framework-owned prompts. Install and upgrade scripts create missing scaffolding, but preserve existing roadmap and milestone content.

## The Three-Layer Flow

Use this mental model:

    ROADMAP.md / milestone-*.md / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

Do not migrate away from roadmap, milestone, and session-note files. Keep them as the human planning and narrative layer. Use SDLC-SPDD artifacts as the execution and governance layer.

## File Layout

Recommended target-project layout:

    ROADMAP.md
    milestone-1.md
    milestone-2.md
    session-notes/
      2026-06-06.md
      2026-06-07.md
    spdd/canvas/
    agent-context/

## How These Files Fit SDLC-SPDD

| Artifact | Role in SDLC-SPDD |
|----------|-------------------|
| `ROADMAP.md` | milestone-level progress and current focus |
| `milestone-*.md` | milestone goals, scope, linked Work IDs, and milestone summaries |
| `session-notes/YYYY-MM-DD.md` | daily summary of agent sessions |
| `spdd/canvas/<WORK-ID>.md` | SPDD design contract for a work item |
| `agent-context/memory/session-history.md` | durable cross-session memory |

The roadmap and milestones tell the agent why the work matters. The canvas tells the agent what to build and what not to change.

## Mapping Scripts

| Script | Direction | Purpose |
|--------|-----------|---------|
| `create-work-from-milestone.sh` | milestone -> SPDD | Create Work IDs, requirement stubs, feature workspace, and draft canvases from milestone checklist items |
| `sync-roadmap-from-spdd.sh` | SPDD -> roadmap | Update a managed roadmap summary table from `spdd/canvas/*.md` metadata |
| `summarize-session-notes.sh` | session notes -> memory | Import existing daily notes into durable agent memory |
| `capture-session-memory.sh` | session -> all layers | Append to memory, progress log, daily notes, and optionally milestone/roadmap |

## Fresh Install Behavior

If missing, install creates:

- `ROADMAP.md`
- `milestone-1.md` when no `milestone-*.md` files exist
- `session-notes/`

Existing files are preserved.

## Upgrade Behavior

Upgrade creates missing roadmap/milestone/session-notes scaffolding but does not overwrite:

- existing `ROADMAP.md`
- existing `milestone-*.md`
- existing files under `session-notes/`

## Planning with Milestones

When starting work, include milestone context:

    /sdlc-spdd-plan @requirements/order-status-api.md @ROADMAP.md @milestone-1.md

Or:

    /sdlc-spdd-plan Jira ABC-123 for milestone-1.md. Link this Work ID to the milestone and update the canvas Metadata.

Canvas Metadata should include:

    - Roadmap: ROADMAP.md
    - Milestone: milestone-1.md

## Create Work from a Milestone

For a milestone checklist like:

    - [ ] Add order status API
    - [ ] Add order status tests

Create draft SDLC-SPDD work artifacts:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Create one item:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --item "Add order status API" --type feature

This creates:

- `agent-context/features/<WORK-ID>/`
- `agent-context/features/<WORK-ID>/requirement.md`
- `agent-context/features/<WORK-ID>/reasons-canvas.md`
- `agent-context/features/<WORK-ID>/progress-log.md`
- `spdd/canvas/<WORK-ID>.md`
- a generated work map entry in the milestone file

The generated canvas is a draft. Continue with:

    /sdlc-spdd-plan @agent-context/features/<WORK-ID>/requirement.md @milestone-1.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

## Starting a Session

The session-start script includes roadmap, milestone, and today's session-note status in the generated handoff:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code

Then ask:

    For FEAT-001-order-status-api, read @agent-context/sessions/current-session.md, @ROADMAP.md, and @milestone-1.md before continuing.

## Capturing Session Notes

By default, session capture appends to:

    session-notes/YYYY-MM-DD.md

Example:

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id FEAT-001-order-status-api \
      --phase code \
      --summary "Implemented T01 for order status lookup." \
      --validation "mvn test" \
      --milestone milestone-1.md \
      --roadmap-note "FEAT-001 completed its first implementation operation." \
      --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md"

This updates:

- `agent-context/memory/session-history.md`
- `agent-context/features/<WORK-ID>/progress-log.md`
- `session-notes/YYYY-MM-DD.md`
- `milestone-1.md` when `--milestone` is provided
- `ROADMAP.md` when `--roadmap-note` is provided

Skip the daily session note only when needed:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --summary "<summary>" --no-session-note

## Suggested Roadmap Update Pattern

Keep the roadmap high level:

    ## Milestones

    - [ ] [Milestone 1](milestone-1.md)
    - [ ] [Milestone 2](milestone-2.md)

    ## Current Focus

    - Work ID: FEAT-001-order-status-api
    - Active milestone: milestone-1.md
    - Current phase: Review
    - Next command: /sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md

Use session notes for details and the roadmap for progress summaries.

To refresh the roadmap from canvas metadata:

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

This updates only the managed section between:

    <!-- SDLC-SPDD-ROADMAP-SUMMARY:START -->
    <!-- SDLC-SPDD-ROADMAP-SUMMARY:END -->

Your handwritten roadmap content outside those markers is preserved.

## Suggested Milestone Update Pattern

Keep each milestone tied to Work IDs:

    ## Linked Work

    | Work ID | Source issue | Status | Notes |
    |---------|--------------|--------|-------|
    | FEAT-001-order-status-api | ABC-123 | In Review | T01 implemented |

Then link each Work ID to:

- Jira or GitHub issue
- REASONS Canvas
- PR
- current status

## Import Existing Session Notes

If your project already has `session-notes/` from earlier work, import them into durable memory:

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --all

Import one file:

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --file session-notes/2026-06-06.md

This preserves the original note and appends an import entry to:

- `agent-context/memory/session-history.md`
- `agent-context/memory/project-memory.md`

## Read Next

- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Maintaining your project](maintaining-your-project.md)
- [Agent session scripts](agent-session-scripts.md)
