# Requirement: FEAT-001-shared-script-library

## Summary

Extract the logic that is currently copy-pasted across the ~23 scripts in
`scripts/` into a small set of sourced helpers under `scripts/lib/`, so there is one
implementation of each shared behavior. This is a pure maintainability refactor — no
new capability, no change to script CLIs or output.

## Source

- Roadmap: ROADMAP.md (make it right — maintainability)
- Milestone: milestone-1.md (item 1, do first)

## Motivation

The same building blocks are re-implemented in nearly every script: `usage()`
printing, target-path resolution (`cd "${TARGET}" && pwd`), `slugify()`,
Work-ID parsing, and `context-index.md` read/append. Duplication means a fix or
convention change must be made in many places and drifts over time. Consolidating
makes the scripts easier to read, change, and extend.

## Acceptance Criteria

- [ ] `scripts/lib/` holds sourced helpers for the shared behaviors (at minimum:
      path/target resolution, logging/usage, slugify, Work-ID parsing, context-index I/O).
- [ ] Consuming scripts source the library instead of re-defining these functions.
- [ ] Every script keeps its exact existing CLI, flags, output, and exit codes
      (behavior-identical refactor — verified by existing tests/validation).
- [ ] No duplicate definitions of the extracted helpers remain in consumers.
- [ ] `tests/` (or the existing validation scripts) cover the shared helpers.

## Non-Goals

- No new script features, flags, or output formats.
- No rename of existing scripts or change to their public interface.

## Next Step

Run:

    /sdlc-spdd-analysis @requirements/milestones/FEAT-001-shared-script-library.md
    /sdlc-spdd-plan @spdd/analysis/FEAT-001-shared-script-library-analysis.md
