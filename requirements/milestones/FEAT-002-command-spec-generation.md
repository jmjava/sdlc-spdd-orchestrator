# Requirement: FEAT-002-command-spec-generation

## Summary

Replace the three hand-maintained command adapter sets (Cursor `templates/cursor/*`,
Copilot `templates/copilot/prompts/*`, Claude `templates/claude/commands/*`) with a
single canonical command spec that *generates* all three. This kills adapter drift
at the source. Maintainability refactor — the generated adapters behave the same as
today, but there is now one place to edit.

## Source

- Roadmap: ROADMAP.md (make it right — maintainability, kills drift)
- Milestone: milestone-1.md (item 2)

## Motivation

Each SDLC-SPDD command exists three times, once per assistant, kept in sync by hand
and policed by `validate-command-adapters.sh`. Editing a command means editing three
files and hoping they stay aligned. A single spec → generated adapters makes parity
structural rather than a thing we verify after the fact.

## Acceptance Criteria

- [ ] A single canonical spec format defines each command once (shared content + per-assistant framing).
- [ ] A generator produces the Cursor, Copilot, and Claude adapter files from the spec.
- [ ] Generated adapters are byte-equivalent in intent to today's and pass `validate-command-adapters.sh`.
- [ ] Editing a command is done in the spec only; regeneration updates all three adapters.
- [ ] CI regenerates and fails if checked-in adapters are stale (no manual drift).
- [ ] Generated, shipped adapters stay posture-neutral (pass `check-posture-boundary.sh`).

## Non-Goals

- No new commands or changed command behavior.
- No change to how assistants are installed/consumed.

## Next Step

Run:

    /sdlc-spdd-analysis @requirements/milestones/FEAT-002-command-spec-generation.md
    /sdlc-spdd-plan @spdd/analysis/FEAT-002-command-spec-generation-analysis.md
