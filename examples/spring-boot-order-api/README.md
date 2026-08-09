# Spring Boot Order API Example

Storage v3 sample: requirement → canvas → review using committed contract paths
only.

## Contents

- `requirements/add-order-status-api.md` — raw requirement
- `spdd/canvas/FEAT-001-order-status-api.md` — REASONS Canvas
- `spdd/reviews/FEAT-001-order-status-api-review.md` — sample review artifact

Memory and session runtime live under `.sdlc/` and `spdd/memory/` in real
projects — not duplicated here.

## Command flow

1. `/sdlc-spdd-plan @requirements/add-order-status-api.md`
2. `/sdlc-spdd-architect @spdd/canvas/FEAT-001-order-status-api.md`
3. `/sdlc-spdd-code` for each canvas operation
4. `/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md`
5. `/sdlc-spdd-retro` then `/sdlc-spdd-sync`
6. `./scripts/sdlc.sh accept --work-id FEAT-001-order-status-api` at the gate

## Validate canvas

```bash
./scripts/validate-reasons-canvas.sh examples/spring-boot-order-api/spdd/canvas/FEAT-001-order-status-api.md
```
