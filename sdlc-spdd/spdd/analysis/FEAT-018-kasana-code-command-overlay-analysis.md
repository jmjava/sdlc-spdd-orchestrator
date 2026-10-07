# Analysis: FEAT-018 — Code-command exit contract

## Metadata

- Work ID: FEAT-018-kasana-code-command-overlay
- Date: 2026-10-07
- Depends on: merged pull request 355 (executed verify receipt)

## Scope Lock

### In Scope

- One shared Required Behavior block in `spec/commands/lifecycle-code.spec.md`.
- Regenerate Cursor, Copilot, and Claude adapters, then rewrite this repo's installed copies with the install path rewrite.
- Semantic tests and adapter validation that fail if any of the four exit checks disappears.
- Say that paths outside the active operation `Files:` and explicitly allowed tests are incomplete work, not a warning.
- Describe the PR 355 receipt as an executed `--verify-command` whose observed exit is stored.

### NOT in Scope

- `WorkflowEngine.gate_check`, `ENFORCED_GATES`, or enter-code semantics
- A model retry loop in `sdlc_engine`
- Review-time diff enforcement (that is the existing `check-operation-diff-scope.sh` path)
- Pull requests against `embabel/guide`
- Orchestrator pull request 312

## Domain Keywords

- code-command exit, named validation, repeated failure, path scope
- incomplete work, verify receipt, explicitly allowed tests

## Code Areas

- `spec/commands/lifecycle-code.spec.md`
- `scripts/validate-command-adapters.sh`
- `tests/test-command-specs.sh`
- `sdlc-spdd/harness/quality-gates.md`

## Recommendation

Keep steps 17–19 (run named validation or discover test/lint/typecheck, report the failing Norm or Safeguard, stop on the second identical failure). Tighten step 20 so extra paths are incomplete work. Correct step 21 so it matches the executed receipt without dropping it. Lock each of the four phrases in the semantic harness.
