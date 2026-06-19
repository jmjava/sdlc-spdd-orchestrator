# Requirement: FEAT-004-prompt-optimization-ledger

## Summary

Establish a trustworthy, low-friction way to measure prompt-optimization signal:
a markdown **prompt-optimization ledger** plus capture-time metric flags that feed
the existing memory indexes. This is the lead "make it right" item from the
ROADMAP Delivery posture — measurement before optimization.

## Source

- Roadmap: ROADMAP.md (Post-MVP backlog → "Make it right — active foundation")
- Delivery posture: make it right (measurement foundation, not a "make it fast" feature)
- Derived from framework self-improvement (dogfooding)

## Problem

Today the framework improves prompts implicitly (git history, retro, prompt-update,
sync) but never records *whether a prompt change improved an outcome*. There is no
way to answer "did splitting Operation T03 reduce review loops?" from the repo. We
are transitioning from make-it-work to make-it-right, so the measurement must land
before any "make it fast" optimization work.

## Acceptance Criteria

- [ ] A ledger file exists at `agent-context/memory/prompt-optimization-log.md` with a documented row schema (date, Work ID, change, hypothesis, signal, outcome).
- [ ] `capture-session-memory.sh` accepts optional metric flags (`--readiness`, `--review-result`, `--rework`, `--context-files`) without breaking existing capture behavior when omitted.
- [ ] Provided metrics are written as `context-index.md` rows with a new Kind: `metric`, scoped to the resolved code area(s).
- [ ] `/sdlc-spdd-prompt-update` and `/sdlc-spdd-retro` command templates require a ledger entry as part of their output (parity across Cursor, Copilot, Claude Code).
- [ ] Existing capture/index tests still pass; new behavior is covered by a smoke test.
- [ ] Docs updated: `context-loading-and-scaling.md` (new `metric` Kind) and the relevant prompt standards.

## Non-Goals

- No `spdd --metrics` query surface (that is a "make it fast" horizon item).
- No automated prompt optimization or scoring.
- No external analytics, token/cost APIs, or dashboards.

## Resolved Decisions

Open questions were resolved during architect review, choosing the most stable
option in each case (see `spdd/canvas/FEAT-004-prompt-optimization-ledger.md` →
Resolved Decisions):

- Global, index-retrieved ledger (not per-Work-ID), bounded by the existing session-history rotation pattern.
- `--review-result` fixed enum: `pass | fail | mixed | blocked`.
- `--rework` = corrective prompt-update/sync cycles after first `Ready For Coding`.

## Next Step

Canvas is `Ready For Coding`. Run:

    /sdlc-spdd-code @spdd/canvas/FEAT-004-prompt-optimization-ledger.md operation T01
