# REASONS Canvas: CHORE-006 — Canonical quick-lane adapter spec

## Metadata

- Work ID: CHORE-006-dogfood-adapters-and-quick-spec
- Work Type: Chore
- Status: Complete
- Readiness: Complete
- Created: 2026-09-14
- Updated: 2026-09-14
- Milestone: milestone-3
- Priority / size: P0 / S
- Depends on: SPIKE-005-architecture-review
- Related: DOC-005-grounding-path-map-codegen
- Requirement: `sdlc-spdd/requirements/milestones/milestone-3/CHORE-006-dogfood-adapters-and-quick-spec.md`
- Analysis: `sdlc-spdd/spdd/analysis/CHORE-006-dogfood-adapters-and-quick-spec-analysis.md`
- Pull Request: https://github.com/jmjava/sdlc-spdd-orchestrator/pull/320
- Beck stage: make it right
- Skills: none requested

## R - Requirements

### User Goal

Every shipped and dogfood `/sdlc-spdd-quick` adapter is generated from the
same canonical spec as the other lifecycle commands.

### Business / Product Goal

Remove the last command adapter that can drift outside
`generate-command-adapters.sh --check`, completing the Milestone 3 dogfood
source-of-truth contract.

### Acceptance Criteria

- [x] Path-rewritten templates match all three dogfood command packs (#308).
- [x] `spec/commands/lifecycle-quick.spec.md` generates the current Cursor,
  Copilot, and Claude quick templates without semantic changes.
- [x] `generate-command-adapters.sh --check` explicitly covers quick.
- [x] Installed-mode CI fails when a dogfood pack is stale (#308).

### Non-Goals

- Changing quick-lane behavior
- Changing install-time path rewrites
- Generating always-on grounding files (DOC-005)
- Embabel upstream work

## E - Entities

- `lifecycle-quick.spec.md`: canonical adapter-independent quick contract plus
  adapter-specific title and preamble blocks.
- `generate-command-adapters.sh`: existing spec-to-template generator.
- Quick templates: Cursor, Copilot, and Claude generated outputs.
- Dogfood quick commands: path-rewritten installed outputs.
- `test-command-specs.sh`: inventory, generation, and semantic regression
  harness.

## A - Approach

Transcribe the existing quick templates into one lifecycle spec, preserving
their adapter-specific presentation and shared eight-step behavior. Run the
existing generator; a clean generated diff is the behavior-preservation proof.
Add a quick-specific assertion to the command-spec harness so future removal of
the spec fails with a named contract rather than relying only on generic
inventory counts.

No generator or validator source change is needed: both already enumerate
specs or compare complete template/dogfood packs.

## S - Structure

### Files to add

- `spec/commands/lifecycle-quick.spec.md`

### Files to modify

- `tests/test-command-specs.sh`
- lifecycle requirement/canvas/review/sync and generated memory records

### Generated files expected unchanged

- `templates/cursor/sdlc-spdd-quick.md`
- `templates/copilot/prompts/sdlc-spdd-quick.prompt.md`
- `templates/claude/commands/sdlc-spdd-quick.md`
- `.cursor/commands/sdlc-spdd-quick.md`
- `.github/prompts/sdlc-spdd-quick.prompt.md`
- `.claude/commands/sdlc-spdd-quick.md`

## O - Operations

### T01 - Put quick under the canonical command-spec generator

- Status: Complete
- Description: Add the lifecycle quick spec, assert its explicit presence and
  shared contract in the command-spec harness, regenerate adapters, and prove
  generated templates plus path-rewritten dogfood outputs remain unchanged.
- Files: `spec/commands/lifecycle-quick.spec.md`, `tests/test-command-specs.sh`
- Files: `sdlc-spdd/requirements/milestones/milestone-3/CHORE-006-dogfood-adapters-and-quick-spec.md`
- Files: `sdlc-spdd/requirements/milestones/milestone-3/MILESTONE-3.md`, `sdlc-spdd/ROADMAP.md`
- Files: `sdlc-spdd/requirements/milestones/milestone-4/DOC-005-grounding-path-map-codegen.md`
- Files: `sdlc-spdd/spdd/tasks/2026-10-monthly-goals.md`
- Files: `sdlc-spdd/spdd/analysis/CHORE-006-dogfood-adapters-and-quick-spec-analysis.md`
- Files: `sdlc-spdd/spdd/canvas/CHORE-006-dogfood-adapters-and-quick-spec.md`
- Files: `sdlc-spdd/spdd/reviews/CHORE-006-dogfood-adapters-and-quick-spec-review.md`
- Files: `sdlc-spdd/spdd/sync/CHORE-006-dogfood-adapters-and-quick-spec-sync.md`
- Files: `sdlc-spdd/spdd/memory/context-index.md`, `sdlc-spdd/spdd/memory/lessons.jsonl`, `sdlc-spdd/spdd/memory/registry.jsonl`
- Tests: generator write plus `--check`; command-spec harness; template and
  installed adapter validators; canvas and requirement validators
- Validation: generated quick templates have no diff; test inventory names
  quick explicitly; dogfood parity remains clean

## N - Norms

- Implement only T01.
- Preserve existing quick semantics and adapter presentation.
- Generate adapters; do not hand-edit generated quick templates.
- Keep templates and dogfood packs byte-stable unless the canonical spec
  exposes a previously hidden difference.
- Capture a passing validation receipt before review.

## S - Safeguards

- Do not alter quick's machine-private/no-lifecycle contract.
- Do not create committed lifecycle artifacts from the quick command itself.
- Do not weaken full-pack dogfood parity or installed-mode CI.
- Do not hand-edit `lessons.jsonl` or `registry.jsonl`.
- No Embabel upstream work.

## Architecture Notes

- Readiness: Ready For Coding.
- Existing generator behavior is sufficient; adding a generator branch would
  duplicate generic `*.spec.md` handling.
- Adapter-specific preambles stay separate blocks; required behavior and output
  are shared blocks.
- Generated-template byte stability is the architecture boundary. Any generated
  diff requires review before acceptance rather than automatic normalization.
- One operation is appropriately task-sized: one canonical spec plus one
  explicit regression assertion.

## Review Checklist

- [x] T01 implementation complete
- [x] Generated quick templates unchanged
- [x] Generator `--check` passes
- [x] Command-spec and adapter validators pass
- [x] Review complete
- [x] Retro and sync complete

## Sync Notes

- #308 completed dogfood pack regeneration and stale-pack CI detection; this
  Work ID only closes the missing canonical quick spec.
- 2026-09-14 — T01 in #320 adds `lifecycle-quick.spec.md`; generator output
  stays byte-identical, 367 command-spec checks and 785 adapter-install checks
  pass, and lifecycle records are reconciled.

## Final Status

- Readiness: Complete
- Status: Complete
- Completed: 2026-09-14
- Pull Request: https://github.com/jmjava/sdlc-spdd-orchestrator/pull/320
