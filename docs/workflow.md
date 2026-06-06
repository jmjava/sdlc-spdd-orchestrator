# Workflow

This workflow is hybrid:

- SDLC Agents supplies the role-separated lifecycle: initialize, plan, architect, code, review, retro, and curator-style sync.
- SPDD supplies the governed prompt artifact: the REASONS Canvas and prompt/code synchronization loop.

## Recommended Sequence

1. **Set up prompts and memory** — `./scripts/setup-agent-prompts.sh --target . --all`
2. **Initialize** — `/sdlc-spdd-init` or `./scripts/init-project.sh --target . --cursor --copilot`
3. **Start session** — `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>`
4. **Plan** — `/sdlc-spdd-plan @requirements/my-feature.md`
5. **Architect** — `/sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md`
6. **Code** — `/sdlc-spdd-code` for one task at a time
7. **Review** — `/sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md`
8. **Prompt update when intent changes** — `/sdlc-spdd-prompt-update @spdd/canvas/FEAT-001-my-feature.md`
9. **Retro** — `/sdlc-spdd-retro @spdd/canvas/FEAT-001-my-feature.md`
10. **Sync** — `/sdlc-spdd-sync @spdd/canvas/FEAT-001-my-feature.md`
11. **Capture memory** — `./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>"`

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
