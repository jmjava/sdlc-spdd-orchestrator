# Progress Log: FEAT-013-guide-git-incremental-upstream

## 2026-08-07 — Intake after SPIKE-003 accept

- Human **accepted** SPIKE-003 hybrid recommendation.
- Created requirement, analysis (Layer B scope lock), and REASONS Canvas.
- T01 architect complete: readiness `ready-for-coding`; Guide allowlist frozen;
  upstream target `embabel/guide` `main`.
- Next: `/sdlc-spdd-code @spdd/canvas/FEAT-013-guide-git-incremental-upstream.md operation T02`
  on the Guide durable checkout (clean Layer B branch vs upstream).

## 2026-08-08 — T02–T04 + pin successor

- Cut Guide tag `sdlc-spdd-projection-v2` @ `28bdb5d` (dual-read PR #7) and bumped
  orchestrator `GUIDE_GIT_REF` defaults / operator docs.
- T02: Layer B branch `cursor/feat-013-layer-b-upstream-f564` from `embabel/guide`
  `main`; allowlisted files only; no `com.embabel/guide/spdd` paths; commit `0cca348`.
- T03: `GitIncrementalDirectorySupportTest` + `RagMaintenanceControllerWebMvcTest` green.
- T04: **embabel/guide PR blocked** by `.cursor/rules/no-embabel-upstream.mdc`.
  Recorded in Guide `docs/spdd-upstream-absorption.md` (branch
  `cursor/feat-013-absorption-status-f564`). Candidate remains on fork for hand-off.
- SPIKE-089 docs synced: Guide dual-read complete; issue #89 closeable.
