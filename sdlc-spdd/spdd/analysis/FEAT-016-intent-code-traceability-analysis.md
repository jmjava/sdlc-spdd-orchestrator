# Analysis: FEAT-016 — Intent-to-code and review-quality checks

## Metadata

- Work ID: FEAT-016-intent-code-traceability
- Date: 2026-09-06
- Depends on: FEAT-014 (merged)

## Scope Lock

### In Scope

- Empty review must not set safeguards_checked
- Review minima: Result line + safeguards named
- code_maps_to_ops: Files: line per T## (automated) + documented human remainder
- Advisory labels on still-unenforced GATE_LABELS

### NOT in Scope

- Hunk-level C-DRIFT automation
- tests_updated / architect_review enforcement
- LLM review quality
- Embabel upstream

## Recommendation

Enforce review minima on `gate_check(retro)` and `sync()`. Enforce Files: mapping on `gate_check(code)`. Label the rest advisory.
