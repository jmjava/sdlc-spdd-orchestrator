# Workflow

This workflow is hybrid:

- SDLC Agents supplies the role-separated lifecycle: initialize, plan, architect, code, review, retro, and curator-style sync.
- SPDD supplies the governed prompt artifact: the REASONS Canvas and prompt/code synchronization loop.
- Roadmap, milestone, and session-note files supply the project narrative that informs planning and summarizes progress.

For how the three parts connect step by step (including milestone vs ad-hoc entry), see [Three-part operating path](three-part-operating-path.md).

## Three-Layer Flow

    ROADMAP.md / milestone-*.md / requirements/milestones/ / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

## Recommended Sequence

Set `--phase` on `start-agent-session.sh` to the phase you are about to run. Paste the **Resume Prompt** from `current-session.md` — see [Session prompt standard](session-prompt-standard.md).

| Step | Part | Action |
|------|------|--------|
| 1 | SDLC | **Set up prompts and memory** — `./scripts/setup-agent-prompts.sh --target . --all` |
| 2 | SDLC | **Initialize** — `/sdlc-spdd-init` |
| 3 | Planning → SPDD | **Map milestone work when needed** — `./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all` |
| 4 | SDLC | **Start session** — `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>` → paste Resume Prompt |
| 5 | SPDD (+ Planning) | **Plan** — `/sdlc-spdd-plan @requirements/my-feature.md @ROADMAP.md @milestone-1.md` |
| 6 | SPDD | **Architect** — `/sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md` |
| 7 | SDLC + SPDD | **Code** — `/sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01` (one operation at a time) |
| 8 | SPDD | **Review** — `/sdlc-spdd-review @spdd/canvas/<WORK-ID>.md` |
| 9 | SPDD | **Prompt update when intent changes** — `/sdlc-spdd-prompt-update @spdd/canvas/<WORK-ID>.md` |
| 10 | SDLC | **Retro** — `/sdlc-spdd-retro @spdd/canvas/<WORK-ID>.md` |
| 11 | SPDD | **Sync** — `/sdlc-spdd-sync @spdd/canvas/<WORK-ID>.md` |
| 12 | SDLC + Planning | **Capture memory and session notes** — `capture-session-memory.sh` (milestone auto-detected when Work ID is in `milestone-*.md`) |
| 13 | Planning ← SPDD | **Refresh roadmap summary** — `./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .` |

## Work IDs

Use prefixes: FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE.

Example: `FEAT-001-order-status-api`

## Quality Gates

See `agent-context/harness/quality-gates.md`.

## Validation

In your installed project, runtime scripts live under `scripts/sdlc-spdd/`:

    ./scripts/sdlc-spdd/validate-reasons-canvas.sh spdd/canvas/

## Daily Use

Use [initialization-and-invocation.md](initialization-and-invocation.md) for first-time setup, examples for starting work, context-preserving questions, and command invocation in Cursor or GitHub Copilot.

Use [daily-runbook.md](daily-runbook.md) for repeatable daily actions across triage, planning, architecture, coding, review, retro, sync, and handoff.

Use [integration-linking.md](integration-linking.md) to link canvases to Jira-based systems, GitHub issues, pull requests, and GitHub Pages documentation.

Use [jira-runbook.md](jira-runbook.md) to create new Jira issues and keep Jira synchronized with canvas, progress, review, and sync artifacts.

Use [spdd-compliance.md](spdd-compliance.md) to verify the workflow remains compliant with Structured Prompt-Driven Development.

Use [hybrid-model.md](hybrid-model.md) to understand how SDLC Agents lifecycle practices and SPDD prompt governance fit together.

Use [agent-session-scripts.md](agent-session-scripts.md) for runnable setup, resync, session handoff, and memory capture commands.

Use [roadmap-milestones-and-session-notes.md](roadmap-milestones-and-session-notes.md) for the mapping between planning docs and SDLC-SPDD artifacts.
