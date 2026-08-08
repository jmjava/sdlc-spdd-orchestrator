# Roadmap, Milestones, and Session Notes

SDLC-SPDD supports a project planning pattern based on:

- root `ROADMAP.md`
- milestone definitions at **either** root `milestone-N.md` **or** (preferred)
  `requirements/milestones/milestone-N/MILESTONE-N.md` with optional `_milestone.yml`
- `requirements/milestones/` with per-item requirement stubs (flat or under `milestone-N/`)
- root `session-notes/` with daily agent-session summaries

These files are project planning artifacts, not framework-owned prompts. Install and upgrade scripts create missing scaffolding, but preserve existing roadmap and milestone content.

## The Three-Layer Flow

Use this mental model:

    ROADMAP.md / milestone definitions / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

Do not migrate away from roadmap, milestone, and session-note files. Keep them as the human planning and narrative layer. Use SDLC-SPDD artifacts as the execution and governance layer.

## File Layout

Recommended target-project layout (subdirectory milestones):

    ROADMAP.md
    requirements/milestones/
      milestone-1/
        _milestone.yml
        MILESTONE-1.md
        FEAT-001-….md
      milestone-2/
        _milestone.yml
        MILESTONE-2.md
    session-notes/
      2026-06-06.md
    spdd/canvas/
    spdd/memory/          (lessons.jsonl + registry.jsonl)

Legacy root `milestone-1.md` remains supported. See
[MIGRATION-root-to-subdirectories.md](MIGRATION-root-to-subdirectories.md) and
[jira-compatible-requirements-format.md](jira-compatible-requirements-format.md).

## How These Files Fit SDLC-SPDD

| Artifact | Role in SDLC-SPDD |
|----------|-------------------|
| `ROADMAP.md` | milestone-level progress and current focus |
| `milestone-*.md` or `…/milestone-N/MILESTONE-N.md` | milestone goals, scope, linked Work IDs, and milestone summaries |
| `requirements/milestones/<WORK-ID>.md` (or under `milestone-N/`) | milestone-derived requirement stub for analysis/plan prompts |
| `session-notes/YYYY-MM-DD.md` | daily summary of agent sessions |
| `spdd/canvas/<WORK-ID>.md` | SPDD design contract for a work item |
| `spdd/memory/lessons.jsonl` | durable cross-session memory (accepted lesson records — see [Storage v3](storage-v3.md)) |

The roadmap and milestones tell the agent why the work matters. The canvas tells the agent what to build and what not to change.

## Mapping Scripts

| Script | Direction | Purpose |
|--------|-----------|---------|
| `create-work-from-milestone.sh` | milestone -> SPDD | Create Work IDs, requirement stubs, and draft canvases from milestone checklist items |
| `sync-roadmap-from-spdd.sh` | SPDD -> roadmap | Update a managed roadmap summary table from `spdd/canvas/*.md` metadata |
| `summarize-session-notes.sh` | session notes -> memory | Import existing daily notes as staged lesson records |
| `capture-session-memory.sh` | session -> all layers | Stage lesson records, refresh the hot brief, and optionally append milestone/roadmap notes |

## Fresh Install Behavior

If missing, install creates:

- `ROADMAP.md`
- `requirements/milestones/milestone-1/MILESTONE-1.md` and `_milestone.yml` when no
  root `milestone-*.md` and no subdirectory milestone definitions exist
- `session-notes/`

Existing files are preserved.

## Upgrade Behavior

Upgrade creates missing roadmap/milestone/session-notes scaffolding but does not overwrite:

- existing `ROADMAP.md`
- existing root `milestone-*.md` or subdirectory `MILESTONE-N.md`
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

- draft Work IDs and canvases
- `requirements/milestones/<WORK-ID>.md` stubs with a scaffolded `## Jira` section
- **Linked Work** rows in the milestone file
- `spdd/canvas/<WORK-ID>.md`
- a generated work map entry in the milestone file

Claim work and commit the team registry on shared repos:

    ./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>

The generated canvas is a draft. Continue with:

    /sdlc-spdd-plan @requirements/milestones/<WORK-ID>.md @ROADMAP.md @milestone-1.md
    /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md

## Starting a Session

The session-start script includes roadmap, milestone, and today's session-note status in the generated handoff:

    ./scripts/sdlc-spdd/sdlc.sh resume FEAT-001-order-status-api --phase code
    ./scripts/sdlc-spdd/sdlc.sh start

Low-level equivalent:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code

With an explicit milestone:

    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id FEAT-001-order-status-api --phase code --milestone milestone-1.md

When `--milestone` is omitted, the script searches `milestone-*.md` files for the Work ID.

The generated `current-session.md` (under gitignored `.sdlc/sessions/`) includes a **Resume Prompt** that references the canvas, the Related Past Work digest, roadmap, active milestone, and today's session note when those files exist. Paste that prompt at the start of the new agent session.

See [Session prompt standard](session-prompt-standard.md) for the full prompt contract.

## Capturing Session Notes

By default, session capture appends to:

    session-notes/YYYY-MM-DD.md

Example (prefer guarded capture):

    ./scripts/sdlc-spdd/sdlc.sh capture \
      --summary "Implemented T01 for order status lookup." \
      --validation "mvn test" \
      --milestone milestone-1.md \
      --roadmap-note "FEAT-001 completed its first implementation operation." \
      --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md"

This stages lesson records in `.sdlc/staged/lessons.jsonl` (promoted to the
committed ledger at the accept gate) and updates:

- `session-notes/YYYY-MM-DD.md` when `--session-note` is set
- `milestone-1.md` when `--milestone` is provided or auto-detected from `milestone-*.md`
- `ROADMAP.md` when `--roadmap-note` is provided

The daily session note is opt-in:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --summary "<summary>" --session-note

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

    | Work ID | Canvas | Requirement | Status | Notes |
    |---------|--------|-------------|--------|-------|
    | FEAT-001-order-status-api | spdd/canvas/FEAT-001-order-status-api.md | requirements/milestones/FEAT-001-order-status-api.md | In Review | T01 implemented |

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

This preserves the original note and stages an import record in
`.sdlc/staged/lessons.jsonl`; promote it into the committed ledger with
`./scripts/sdlc-spdd/sdlc.sh accept`.

## Read Next

- [What planning brings](what-planning-brings.md)
- [Planning prompt standard](planning-prompt-standard.md)
- [What SDLC brings](what-sdlc-brings.md)
- [What SPDD brings](what-spdd-brings.md)
- [Session prompt standard](session-prompt-standard.md)
- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Maintaining your project](maintaining-your-project.md)
- [Agent session scripts](agent-session-scripts.md)
