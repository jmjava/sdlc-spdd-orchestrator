# REASONS Canvas: FEAT-018-kasana-code-command-overlay — Code-command exit contract

## Metadata

- Work ID: FEAT-018-kasana-code-command-overlay
- Work Type: Feature
- Status: Complete
- Readiness: Complete
- Created: 2026-10-07
- Updated: 2026-10-07
- Owner: ubuntu
- Source System: Local session
- Source Issue: LOCAL-001-kasana-code-command-overlay
- Milestone: milestone-5
- Requirement: `sdlc-spdd/requirements/milestones/FEAT-018-kasana-code-command-overlay.md`
- Analysis: `sdlc-spdd/spdd/analysis/FEAT-018-kasana-code-command-overlay-analysis.md`
- Related local session: .sdlc/local-sessions/LOCAL-001-kasana-code-command-overlay/

## R - Requirements

### User Goal

`/sdlc-spdd-code` refuses to call one approved operation complete until validation runs, failures name the command output and the Norm or Safeguard, the same failure stops on the second occurrence, and changed paths stay in scope.

### Business / Product Goal

Cloud Agents and local chat share one exit contract. The executed verify receipt from pull request 355 stays the machine record. `gate_check` stays enter-phase.

### Acceptance Criteria

- [x] Canonical spec and all three generated packs encode the same four exit checks
- [x] Semantic tests fail if any exit check disappears
- [x] Extra paths are incomplete work, not a warning
- [x] Executed verify receipt and enter-phase `gate_check` stay as they are

### Non-Goals

- Changing `WorkflowEngine.gate_check` or `ENFORCED_GATES`
- Adding a model retry loop
- Hand-editing generated adapters
- Opening a pull request against `embabel/guide`

## E - Entities

- Code-command exit checks (validation, actionable failure, repeated-failure stop, path scope)
- Executed verify receipt (command that ran, observed exit, pass/fail)
- Operation `Files:` plus explicitly allowed test paths

## A - Approach

Edit the shared Required Behavior block. Regenerate adapters. Extend the semantic harness so stripping any of the four phrases fails. Leave the receipt executor in `capture-session-memory.sh` alone.

## S - Structure

### Files to modify

- Canonical spec, generated adapters, installed dogfood copies, semantic tests, adapter validator, quality-gate wording

### Test structure

- Presence locks for the four phrases on the spec and all three packs
- Parity sabotage: drop one phrase from one pack and expect failure
- Existing receipt locks stay

## O - Operations

### T01 - Lock the four code-command exit checks

- Status: Complete
- Description: Encode the four exit checks in the shared code-command spec, regenerate adapters, and fail semantic tests when any check disappears. Extra paths are incomplete work. The executed verify receipt stays, and `gate_check` stays enter-phase.
- Files: `spec/commands/lifecycle-code.spec.md`, `scripts/validate-command-adapters.sh`, `sdlc-spdd/scripts/validate-command-adapters.sh`, `templates/cursor/sdlc-spdd-code.md`, `templates/copilot/prompts/sdlc-spdd-code.prompt.md`, `templates/claude/commands/sdlc-spdd-code.md`, `.cursor/commands/sdlc-spdd-code.md`, `.github/prompts/sdlc-spdd-code.prompt.md`, `.claude/commands/sdlc-spdd-code.md`, `sdlc-spdd/harness/quality-gates.md`, `templates/agent-context/harness/quality-gates.md`, `sdlc-spdd/requirements/milestones/FEAT-018-kasana-code-command-overlay.md`, `sdlc-spdd/spdd/analysis/FEAT-018-kasana-code-command-overlay-analysis.md`, `sdlc-spdd/spdd/canvas/FEAT-018-kasana-code-command-overlay.md`, `sdlc-spdd/spdd/reviews/FEAT-018-kasana-code-command-overlay-review.md`, `sdlc-spdd/spdd/sync/FEAT-018-kasana-code-command-overlay-sync.md`, `sdlc-spdd/spdd/memory/registry.jsonl`, `sdlc-spdd/spdd/memory/lessons.jsonl`, `sdlc-spdd/spdd/memory/context-index.md`
- Tests: `tests/test-command-specs.sh`
- Validation: `./scripts/generate-command-adapters.sh`, `./scripts/generate-command-adapters.sh --check`, `./scripts/validate-command-adapters.sh`, `./tests/test-command-specs.sh`, `./scripts/check-posture-boundary.sh`

## N - Norms

- One approved operation
- Do not hand-edit generated adapters; regenerate them
- Do not add a model retry loop
- Named Validation stays command behavior; the machine record is the executed receipt

## S - Safeguards

- Do not change `WorkflowEngine.gate_check`, `ENFORCED_GATES`, or enter-code semantics
- Do not undo the executed verify receipt
- Do not open a pull request against `embabel/guide`
- Do not merge orchestrator pull request 312
- Extra changed paths are incomplete work

## Review Checklist

- [x] Four exit checks match across Cursor, Copilot, and Claude
- [x] Stripping any one check fails the semantic test
- [x] Receipt still comes from the command that ran
- [x] `gate_check` source is untouched

## Sync Notes

Builds on merged pull request 355. Does not reopen pull request 312.

## Final Status

- Readiness: Complete
- Status: Complete
