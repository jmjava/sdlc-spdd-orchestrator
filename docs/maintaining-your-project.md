# Maintaining Your Project

Use this guide after SDLC-SPDD is installed in an application repository.

Maintenance means keeping the framework, prompts, memory, canvases, and external links useful over time.

Runtime scripts in a target app live at `scripts/sdlc-spdd/`. When developing the orchestrator itself, the same scripts are at `scripts/` in this repository. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Maintenance Checklist

Run these checks regularly:

- [ ] Framework prompts and scripts are current.
- [ ] `ROADMAP.md` and active `milestone-*.md` files reflect current progress.
- [ ] daily session notes are captured under `session-notes/`.
- [ ] `agent-context/sessions/current-session.md` reflects the active work.
- [ ] feature workspace canvas and canonical canvas are in sync.
- [ ] memory captures recent decisions, pitfalls, and patterns.
- [ ] Jira or GitHub issue links are current.
- [ ] review and sync logs exist for completed work.
- [ ] old session files are kept or archived according to team policy.

## Upgrade Framework Files

From the orchestrator repository:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run
    ./scripts/upgrade-project.sh --target /path/to/app --all

The upgrade preserves application work and existing memory content.

Review backups under:

    /path/to/app/.sdlc-spdd-upgrade-backups/<timestamp>/

## Start Every Session from Files

Do not rely on chat history alone.

From the target app:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only
    ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

Then **paste the Resume Prompt** from `agent-context/sessions/current-session.md`. See [Session prompt standard](session-prompt-standard.md).

## Check Canvas Sync

Before resuming work:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

If the canonical canvas is correct:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --from-canvas --force --phase <phase>

If the feature workspace copy is correct:

    ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --from-feature --force --phase <phase>

Use sync carefully:

- behavior or acceptance-criteria changes: run `/sdlc-spdd-prompt-update` first.
- accepted implementation drift: run `/sdlc-spdd-sync` after review.

## Capture Session Memory

At the end of meaningful work:

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase <phase> \
      --summary "<what changed>" \
      --validation "<tests or checks>" \
      --decisions "<decisions, if any>" \
      --pitfalls "<pitfalls, if any>" \
      --patterns "<patterns, if any>" \
      --next "<next command>"

Memory is stored in:

- `session-notes/YYYY-MM-DD.md`
- `agent-context/memory/session-history.md`
- `agent-context/memory/project-memory.md`
- `agent-context/memory/architecture-decisions.md`
- `agent-context/memory/known-pitfalls.md`
- `agent-context/memory/reusable-patterns.md`
- `agent-context/features/<WORK-ID>/progress-log.md`

To tie a session to roadmap and milestone progress:

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase <phase> \
      --summary "<what changed>" \
      --validation "<tests or checks>" \
      --milestone milestone-1.md \
      --roadmap-note "<roadmap-level progress note>" \
      --next "<next command>"

## Maintain Jira and GitHub Links

Keep the canvas Metadata current:

    - Work ID:
    - Source System:
    - Source Issue:
    - Source URL:
    - Docs URL:
    - Related PR:

For Jira updates:

    For <WORK-ID>, read the canvas, progress log, review report, and sync log. Draft a Jira update for <JIRA-KEY>.

For public docs:

    For <WORK-ID>, create a public-safe summary suitable for GitHub Pages. Exclude secrets and internal-only details.

## Keep Roadmap and Milestones Mapped

Create SDLC-SPDD work from milestone checklist items:

    ./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Refresh the managed roadmap summary from canvas metadata:

    ./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .

Import existing daily session notes into durable memory:

    ./scripts/sdlc-spdd/summarize-session-notes.sh --target . --all

Use this flow:

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

## Keep Prompts and Playbooks Clean

Use these boundaries:

| Path | Maintenance rule |
|------|------------------|
| `.cursor/commands/` | framework-owned prompts; update through upgrade script |
| `.github/prompts/` | framework-owned Copilot prompts; update through upgrade script |
| `scripts/sdlc-spdd/` | framework-owned runtime scripts; update through upgrade script |
| `agent-context/playbooks/` | team workflow guidance; safe place for team process notes |
| `agent-context/memory/` | durable project knowledge; preserve and append |
| `ROADMAP.md` | project-owned milestone progress; preserve and append intentionally |
| `milestone-*.md` | project-owned milestone scope and status; preserve and append intentionally |
| `session-notes/` | project-owned daily session summaries |
| `spdd/canvas/` | design contract; update through SDLC-SPDD skills |

## Archive Old Sessions

Session files accumulate under:

    agent-context/sessions/

Keep:

- `current-session.md`
- session files for active or recently completed work

Archive or prune old session files according to team policy. Do not delete `agent-context/memory/session-history.md` unless intentionally resetting durable history.

## Validate Before Done

Canvas validation:

    ./scripts/sdlc-spdd/validate-reasons-canvas.sh spdd/canvas/<WORK-ID>.md

Review:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

Sync:

    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Retro:

    /sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md

## Read Next

- [Agent session scripts](agent-session-scripts.md)
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md)
- [Framework upgrade](framework-upgrade.md)
- [Jira runbook](jira-runbook.md)
- [SPDD compliance](spdd-compliance.md)
