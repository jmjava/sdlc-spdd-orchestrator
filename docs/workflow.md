# Workflow

## Recommended Sequence

1. **Initialize** — `/sdlc-spdd-init` or `./scripts/init-project.sh --target . --cursor --copilot`
2. **Plan** — `/sdlc-spdd-plan @requirements/my-feature.md`
3. **Architect** — `/sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md`
4. **Code** — `/sdlc-spdd-code` for one task at a time
5. **Review** — `/sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md`
6. **Prompt update when intent changes** — `/sdlc-spdd-prompt-update @spdd/canvas/FEAT-001-my-feature.md`
7. **Retro** — `/sdlc-spdd-retro @spdd/canvas/FEAT-001-my-feature.md`
8. **Sync** — `/sdlc-spdd-sync @spdd/canvas/FEAT-001-my-feature.md`

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
