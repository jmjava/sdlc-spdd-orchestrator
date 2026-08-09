# Maintaining Your Project

Use this guide after SDLC-SPDD is installed in an application repository.

Maintenance means keeping the framework, prompts, memory, canvases, and external links useful over time.

Runtime scripts in a target app live at `sdlc-spdd/scripts/`. When developing the orchestrator itself, the same scripts are at `scripts/` in this repository. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Maintenance Checklist

Run these checks regularly:

- [ ] Framework prompts and scripts are current.
- [ ] `spdd/memory/registry.jsonl` reflects active team claims (committed on shared repos).
- [ ] Local pointer and workflow state are sane (`.sdlc/pointer`, `.sdlc/workflows/` — gitignored).
- [ ] `ROADMAP.md` and active `milestone-*.md` files reflect current progress.
- [ ] daily session notes are captured under `session-notes/`.
- [ ] `.sdlc/sessions/current-session.md` reflects the active work.
- [ ] canvas and phase artifacts are in sync for the active Work ID.
- [ ] captures include **areas in session content** (summary/session-notes, parsed at capture) so retrieval stays area-scoped.
- [ ] staged records are accepted at retro/sync gates (`/sdlc-spdd-accept`).
- [ ] Jira or GitHub issue links are current.
- [ ] review and sync logs exist for completed work.
- [ ] old session briefs are kept or archived according to team policy.

## Upgrade Framework Files

From the orchestrator repository:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run
    ./scripts/upgrade-project.sh --target /path/to/app --all

The upgrade preserves application work, requirements, canvases, and the committed
lessons ledger. Legacy layouts are migrated by `sdlc-engine storage migrate` — see
[Framework upgrade](framework-upgrade.md).

Review backups under:

    /path/to/app/.sdlc-spdd-upgrade-backups/<timestamp>/

## Start Every Session from Files

Do not rely on chat history alone.

From the target app:

    ./sdlc-spdd/scripts/sdlc.sh next
    ./sdlc-spdd/scripts/sdlc.sh resume <WORK-ID> [--phase <phase>]
    ./sdlc-spdd/scripts/sdlc.sh start

Optional canvas sync before resuming stale work:

    ./sdlc-spdd/scripts/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

Then **paste the Resume Prompt** from `.sdlc/sessions/current-session.md`. See [Session prompt standard](session-prompt-standard.md).

## Check Canvas Sync

Before resuming work:

    ./sdlc-spdd/scripts/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

If the canonical canvas is correct:

    ./sdlc-spdd/scripts/resync-agent-session.sh --target . --work-id <WORK-ID> --from-canvas --force --phase <phase>

Use sync carefully:

- behavior or acceptance-criteria changes: run `/sdlc-spdd-prompt-update` first.
- accepted implementation drift: run `/sdlc-spdd-sync` after review.

## Capture Session Memory

At the end of meaningful work, capture — prefer guarded capture via the workflow CLI:

    ./sdlc-spdd/scripts/sdlc.sh capture \
      --summary "<what changed; include paths like src/billing or com.acme.order>" \
      --validation "<tests or checks>" \
      --decisions "<decisions, if any>" \
      --pitfalls "<pitfalls, if any>" \
      --patterns "<patterns, if any>" \
      --next "<next command>"

Captures stage lesson records in `.sdlc/staged/lessons.jsonl` — git stays quiet.
At retro/sync, `/sdlc-spdd-accept` promotes keepers into the committed ledger:

    ./sdlc-spdd/scripts/sdlc.sh accept --list
    ./sdlc-spdd/scripts/sdlc.sh accept --work-id <WORK-ID>

Retrieve accepted lessons on demand — never bulk-read the ledger:

    sdlc-engine context retrieve --work-id <WORK-ID> --kind pitfall
    sdlc-engine context show "<record-id>"

See [Storage v3 — stage-then-accept](storage-v3.md#stage-then-accept) and
[Bootstrap and retrieval-based loading](context-loading-and-scaling.md#bootstrap-and-index-based-loading).

To tie a session to roadmap and milestone progress:

    ./sdlc-spdd/scripts/sdlc.sh capture \
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

    SDLC_ENGINE=python ./scripts/sdlc.sh issues push <WORK-ID> --dry-run

See [Jira runbook](jira-runbook.md) and [Issue sync and branching](issue-sync-and-branching.md).

## Keep Roadmap and Milestones Mapped

Create SDLC-SPDD work from milestone checklist items:

    ./sdlc-spdd/scripts/create-work-from-milestone.sh --target . --milestone milestone-1.md --all

Refresh the managed roadmap summary from canvas metadata:

    ./sdlc-spdd/scripts/sync-roadmap-from-spdd.sh --target .

Summarize session notes into staged lesson records (then accept at the gate):

    ./sdlc-spdd/scripts/summarize-session-notes.sh --target . --all

Use this flow:

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + spdd/memory/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

## Keep Prompts and Skills Clean

Use these boundaries:

| Path | Maintenance rule |
|------|------------------|
| `.cursor/commands/` | framework-owned Cursor prompts; update through upgrade script |
| `.cursor/rules/sdlc-spdd.mdc` | framework-owned always-on Cursor operating-model rule; update through upgrade script |
| `.github/prompts/` | framework-owned Copilot prompts; update through upgrade script |
| `.github/copilot-instructions.md` | framework-owned Copilot instructions; update through upgrade script |
| `.claude/commands/` | framework-owned Claude Code commands; update through upgrade script |
| `CLAUDE.md` | project-owned Claude Code memory; SDLC-SPDD manages only the marked grounding block |
| `spdd/memory/registry.jsonl` | team Work ID claims; update via `sdlc.sh claim`/`release`, then commit |
| `spdd/memory/lessons.jsonl` | accepted lessons; written only by `accept` — never hand-edit |
| `sdlc-spdd/scripts/` | framework-owned runtime scripts; update through upgrade script |
| `harness/skills/` | team `#SkillName` files; safe place for process and stack guidance |
| `harness/phase-index.md` | phase-scoped static context index; team may extend |
| `ROADMAP.md` | project-owned milestone progress; preserve and append intentionally |
| `milestone-*.md` | project-owned milestone scope and status; preserve and append intentionally |
| `session-notes/` | project-owned daily session summaries |
| `spdd/canvas/` | design contract; update through SDLC-SPDD skills |

## Archive Completed / Cancelled Work

When a Work ID's canvas `## Final Status` is `Complete` or `Cancelled`, remove its
contract artifacts from the working tree (git history retains them):

```bash
./sdlc-spdd/scripts/sdlc.sh archive <WORK-ID>
./sdlc-spdd/scripts/sdlc.sh archive --all
./sdlc-spdd/scripts/sdlc.sh archive <WORK-ID> --dry-run
```

This removes (when present):

- `spdd/canvas/<WORK-ID>.md`
- matching `spdd/analysis|reviews|sync` artifacts
- matching `.sdlc/sessions/*<WORK-ID>*` briefs (not `current-session.md`)
- `.sdlc/workflows/<WORK-ID>.state`

Left in place: `requirements/milestones/<WORK-ID>.md` (requirement source).
The registry row becomes `archived`.

## Archive Old Sessions

Session briefs accumulate under `.sdlc/sessions/` (gitignored).

Prefer `sdlc.sh archive` for Work IDs that are Complete/Cancelled (removes matching
session briefs automatically). Keep:

- `current-session.md`
- session briefs for active or recently completed work

Rotate timestamped briefs with `--session-limit` on `start` (default 20; older
briefs move to `.sdlc/sessions/archive/`).

## Validate Before Done

Canvas validation:

    ./sdlc-spdd/scripts/validate-reasons-canvas.sh spdd/canvas/<WORK-ID>.md

Review:

    /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

Sync:

    /sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md

Retro:

    /sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md

Accept staged memory at the gate:

    /sdlc-spdd-accept

## Read Next

- [Agent session scripts](agent-session-scripts.md)
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md)
- [Framework upgrade](framework-upgrade.md)
- [Jira runbook](jira-runbook.md)
- [SPDD compliance](spdd-compliance.md)
