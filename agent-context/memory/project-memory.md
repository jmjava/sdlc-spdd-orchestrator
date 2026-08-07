# Project Memory

This file captures durable project context for SDLC-SPDD agents.

## Project Summary

- Repository: sdlc-spdd-orchestrator
- Purpose: Cursor-first AI software delivery scaffold combining SDLC Agents lifecycle with OpenSPDD REASONS Canvas contracts

## Stack Detection

Run `./scripts/detect-stack.sh --target .` to append detected technologies here.

## Conventions

- Work IDs use prefixes: FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE
- Each unit of work has one primary REASONS Canvas
- Coding agents implement one approved operation at a time

## Recent Learnings

Add retro outputs here over time.

### 2026-07-15T23:05:49Z - FEAT-004-prompt-optimization-ledger

- Phase: code
- Summary: FEAT-004 T02: capture metric flags (--readiness/--review-result/--rework/--context-files) write Kind: metric rows; invalid review-result warns and skips
- Next: /sdlc-spdd-code @spdd/canvas/FEAT-004-prompt-optimization-ledger.md operation T03

### 2026-07-15T23:18:43Z - FEAT-004-prompt-optimization-ledger

- Phase: code
- Summary: FEAT-004 T03-T05: ledger required in prompt-update/retro specs; ledger rotation via capture; docs metric Kind + workflow
- Next: Not recorded

### 2026-07-15T23:19:59Z - FEAT-004-prompt-optimization-ledger

- Phase: retro
- Summary: FEAT-004 retro: ledger measurement landed; fixed next-op Final Status boundary; Approved With Notes
- Next: Not recorded

### 2026-07-15T23:20:00Z - FEAT-004-prompt-optimization-ledger

- Phase: sync
- Summary: FEAT-004 sync: canvas/requirement/milestone aligned; Work ID Complete
- Next: Not recorded

### 2026-07-15T23:21:58Z - FEAT-005-canvas-readiness-indicators

- Phase: code
- Summary: FEAT-005 T01-T04: readiness vocab + validate + cycle metrics + docs
- Next: Not recorded

### 2026-07-15T23:21:59Z - FEAT-005-canvas-readiness-indicators

- Phase: retro
- Summary: FEAT-005 retro complete
- Next: Not recorded

### 2026-07-15T23:21:59Z - FEAT-005-canvas-readiness-indicators

- Phase: sync
- Summary: FEAT-005 sync complete
- Next: Not recorded

### 2026-08-07 — SPIKE-003-embabel-context-graph-absorption

- Phase: review / retro / sync
- Summary: Hybrid absorption recommendation holds after dual-env tip refresh; Guide PR #4 merged; await human accept/reject before git-incremental upstream FEAT
- Next: Human accept/reject of recommendation

### 2026-08-07T21:08:56Z - SPIKE-003-embabel-context-graph-absorption

- Phase: sync
- Summary: SPIKE-003 dual-env: tip refresh Layer D; review Approved With Notes; retro+sync; await human accept/reject
- Next: Human accept/reject of hybrid recommendation; then optional FEAT for git-incremental upstream
