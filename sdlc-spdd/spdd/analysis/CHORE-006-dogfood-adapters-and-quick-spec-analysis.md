# Analysis: CHORE-006-dogfood-adapters-and-quick-spec

## Scope Lock

Complete only the missing canonical specification for
`/sdlc-spdd-quick` and prove that the existing generator owns all three quick
adapters. Do not change quick-lane semantics, path-rewrite behavior, grounding
generation, or other command contracts.

## Current State

- `spec/commands/` contains 19 specs.
- Each adapter template tree contains the additional
  `sdlc-spdd-quick` command, so quick is the only template command without a
  canonical spec.
- `generate-command-adapters.sh` already processes every `*.spec.md`; no
  generator change is required for a new quick spec to participate in
  generation and `--check`.
- Cursor, Copilot, and Claude quick templates already express the same eight
  behaviors with adapter-specific titles/preambles.
- Dogfood adapter parity and installed-mode CI enforcement landed in #308.

## Gap

`generate-command-adapters.sh --check` cannot validate quick because no
`lifecycle-quick.spec.md` exists. Existing inventory tests walk specs toward
templates, so the extra unspecced quick templates are not detected.

## Domain Keywords

- canonical command specification
- generated adapters
- quick lane
- dogfood command packs
- path rewrite
- template parity

## Code Areas

- `spec/commands/`
- `templates/cursor/`
- `templates/copilot/prompts/`
- `templates/claude/commands/`
- `.cursor/commands/`, `.github/prompts/`, `.claude/commands/`
- `scripts/generate-command-adapters.sh`
- `scripts/validate-command-adapters.sh`
- `tests/test-command-specs.sh`

## Proposed Change

1. Add `spec/commands/lifecycle-quick.spec.md` using the existing three quick
   templates as the behavior-preserving source material.
2. Add an explicit quick-spec contract assertion to
   `tests/test-command-specs.sh` so deleting or bypassing the spec fails with a
   clear CHORE-006 signal.
3. Regenerate adapters and require a clean diff; existing template and dogfood
   content should remain unchanged.
4. Close the requirement and Milestone 3 bookkeeping after review.

## Files in Scope

- `spec/commands/lifecycle-quick.spec.md` (new)
- `tests/test-command-specs.sh`
- `sdlc-spdd/requirements/milestones/milestone-3/CHORE-006-dogfood-adapters-and-quick-spec.md`
- `sdlc-spdd/spdd/canvas/CHORE-006-dogfood-adapters-and-quick-spec.md`
- generated lifecycle evidence under `sdlc-spdd/spdd/`

## Validation Plan

- `./scripts/generate-command-adapters.sh`
- `git diff --exit-code -- templates/cursor/sdlc-spdd-quick.md templates/copilot/prompts/sdlc-spdd-quick.prompt.md templates/claude/commands/sdlc-spdd-quick.md`
- `./scripts/generate-command-adapters.sh --check`
- `./tests/test-command-specs.sh`
- `./scripts/validate-command-adapters.sh --mode templates`
- `./scripts/validate-command-adapters.sh --mode installed`
- `./scripts/validate-reasons-canvas.sh`
- `./scripts/validate-requirements-format.sh --target sdlc-spdd`

## Risks

- Formatting the adapter-specific preambles incorrectly would create noisy
  generated diffs despite unchanged semantics.
- A generic inventory assertion could pass without naming quick; the test must
  explicitly require `lifecycle-quick.spec.md`.
- Running generation before the spec exactly represents current adapters could
  overwrite valid dogfood source templates.

## Conclusion

This is one small behavior-preserving operation. The generator and installed
parity checks already exist; the missing source-of-truth spec and an explicit
regression assertion are sufficient.
