# Spring Boot Order API Example

This example demonstrates SDLC-SPDD from requirement through review for a small Spring Boot feature.

## Contents

- `requirements/add-order-status-api.md` — raw requirement
- `spdd/canvas/FEAT-001-order-status-api.md` — REASONS Canvas
- `agent-context/features/FEAT-001-order-status-api/` — feature workspace artifacts

## Command Flow

1. `/sdlc-spdd-plan @requirements/add-order-status-api.md`
2. `/sdlc-spdd-architect @spdd/canvas/FEAT-001-order-status-api.md`
3. `/sdlc-spdd-code` for T01, then T02, then T03
4. `/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md`
5. `/sdlc-spdd-retro @spdd/canvas/FEAT-001-order-status-api.md`
6. `/sdlc-spdd-sync @spdd/canvas/FEAT-001-order-status-api.md`

## Validate Canvas

    ../../scripts/validate-reasons-canvas.sh spdd/canvas/FEAT-001-order-status-api.md
