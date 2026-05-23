# Workflow

## Recommended Sequence

1. **Initialize** — `/sdlc-spdd-init` or `./scripts/init-project.sh --target . --cursor`
2. **Plan** — `/sdlc-spdd-plan @requirements/my-feature.md`
3. **Architect** — `/sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md`
4. **Code** — `/sdlc-spdd-code` for one task at a time
5. **Review** — `/sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md`
6. **Retro** — `/sdlc-spdd-retro @spdd/canvas/FEAT-001-my-feature.md`
7. **Sync** — `/sdlc-spdd-sync @spdd/canvas/FEAT-001-my-feature.md`

## Work IDs

Use prefixes: FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE.

Example: `FEAT-001-order-status-api`

## Quality Gates

See `agent-context/harness/quality-gates.md`.

## Validation

    ./scripts/validate-reasons-canvas.sh spdd/canvas/
