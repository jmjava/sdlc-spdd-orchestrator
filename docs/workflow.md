# Workflow

This workflow is hybrid:

- SDLC Agents supplies the role-separated lifecycle: initialize, plan, architect, code, review, retro, and curator-style sync.
- SPDD supplies the governed prompt artifact: the REASONS Canvas and prompt/code synchronization loop.
- Roadmap, milestone, and session-note files supply the project narrative that informs planning and summarizes progress.

## Three-Layer Flow

    ROADMAP.md / milestone-*.md / session-notes/
            -> inform and summarize
    spdd/canvas/ + agent-context/
            -> govern and remember
    code / reviews / sync logs
            -> execute and validate

## Recommended Sequence

1. **Set up prompts and memory** — `./scripts/setup-agent-prompts.sh --target . --all`
2. **Initialize** — `/sdlc-spdd-init` or `./scripts/init-project.sh --target . --cursor --copilot`
3. **Map milestone work when needed** — `./scripts/sdlc-spdd/create-work-from-milestone.sh --target . --milestone milestone-1.md --all`
4. **Start session** — `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>`
5. **Plan** — `/sdlc-spdd-plan @requirements/my-feature.md @ROADMAP.md @milestone-1.md`
6. **Architect** — `/sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md`
7. **Code** — `/sdlc-spdd-code` for one task at a time
8. **Review** — `/sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md`
9. **Prompt update when intent changes** — `/sdlc-spdd-prompt-update @spdd/canvas/FEAT-001-my-feature.md`
10. **Retro** — `/sdlc-spdd-retro @spdd/canvas/FEAT-001-my-feature.md`
11. **Sync** — `/sdlc-spdd-sync @spdd/canvas/FEAT-001-my-feature.md`
12. **Capture memory and session notes** — `./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>"`
13. **Refresh roadmap summary** — `./scripts/sdlc-spdd/sync-roadmap-from-spdd.sh --target .`

## Work IDs

Use prefixes: FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE.

Example: `FEAT-001-order-status-api`

## Quality Gates

See `agent-context/harness/quality-gates.md`.

## Validation

    ./scripts/validate-reasons-canvas.sh spdd/canvas/

## Daily Use

Use [initialization-and-invocation.md](initialization-and-invocation.md) for first-time setup, examples for starting work, context-preserving questions, and command invocation in Cursor or GitHub Copilot.

Use [daily-runbook.md](daily-runbook.md) for repeatable daily actions across triage, planning, architecture, coding, review, retro, sync, and handoff.

Use [integration-linking.md](integration-linking.md) to link canvases to Jira-based systems, GitHub issues, pull requests, and GitHub Pages documentation.

Use [jira-runbook.md](jira-runbook.md) to create new Jira issues and keep Jira synchronized with canvas, progress, review, and sync artifacts.

Use [spdd-compliance.md](spdd-compliance.md) to verify the workflow remains compliant with Structured Prompt-Driven Development.

Use [hybrid-model.md](hybrid-model.md) to understand how SDLC Agents lifecycle practices and SPDD prompt governance fit together.

Use [agent-session-scripts.md](agent-session-scripts.md) for runnable setup, resync, session handoff, and memory capture commands.

Use [roadmap-milestones-and-session-notes.md](roadmap-milestones-and-session-notes.md) for the mapping between planning docs and SDLC-SPDD artifacts.
