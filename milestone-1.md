# Milestone 1 — Make it right

## Goal

Take the framework from its current working state to "right": refactor the
*existing* code and docs for readability, maintainability, and extensibility. No
new features. Ship each refactor as working code.

Prompt optimization — including the ledger and leading indicators that measure it —
is "make it fast" and is deliberately **last**, after the framework is structurally
right.

## Plan (in order)

Make it right (do first):

1. **FEAT-001 — shared `scripts/lib/` for capture/resolve/verify.** Foundational
   maintainability refactor; the other refactors build on it. Start here.
2. **FEAT-002 — single command spec → generated adapters.** Kills hand-maintained
   adapter drift across Cursor/Copilot/Claude.
3. **FEAT-003 — extension/hook manifest.** A clean, documented extension point.
4. **Readability pass — consistent structure, naming, and examples** across code
   and docs.

Make it fast (do last, deferred):

5. **FEAT-004 — prompt-optimization ledger + capture metrics.** Already specced;
   parked until the refactors above land. (`spdd/canvas/FEAT-004-prompt-optimization-ledger.md`.)
6. **FEAT-005 — canvas `readiness:` front matter + leading indicators.**

Work IDs are numbered in execution order. All five now have a requirement stub and a
REASONS Canvas. FEAT-004 (deferred) is at Ready For Coding; the make-it-right
canvases (FEAT-001→003) and FEAT-005 are drafts that each need an analysis pass
(`/sdlc-spdd-analysis` → `/sdlc-spdd-plan` → `/sdlc-spdd-architect`) before coding.

## Constraint

The make-it-work/right/fast posture is how *we* plan the orchestrator. It must not
appear in anything that ships to target projects (`templates/`, shipped docs,
grounding files). This is enforced by `./scripts/check-posture-boundary.sh`.

## Linked Work

| Work ID | Canvas | Requirement | Status | Notes |
|---------|--------|-------------|--------|-------|
| FEAT-001-shared-script-library | spdd/canvas/FEAT-001-shared-script-library.md | requirements/milestones/FEAT-001-shared-script-library.md | Draft — Needs Analysis | Lead make-it-right refactor; plan next |
| FEAT-002-command-spec-generation | spdd/canvas/FEAT-002-command-spec-generation.md | requirements/milestones/FEAT-002-command-spec-generation.md | Draft — Needs Analysis | Make it right (maintainability) |
| FEAT-003-extension-hook-manifest | spdd/canvas/FEAT-003-extension-hook-manifest.md | requirements/milestones/FEAT-003-extension-hook-manifest.md | Draft — Needs Analysis | Make it right (extensibility) |
| FEAT-004-prompt-optimization-ledger | spdd/canvas/FEAT-004-prompt-optimization-ledger.md | requirements/milestones/FEAT-004-prompt-optimization-ledger.md | Ready For Coding — deferred | Make it fast; runs after refactors |
| FEAT-005-canvas-readiness-indicators | spdd/canvas/FEAT-005-canvas-readiness-indicators.md | requirements/milestones/FEAT-005-canvas-readiness-indicators.md | Draft — Needs Analysis | Make it fast; do last |

## Session Updates

Record shipped increments under `session-notes/`.
