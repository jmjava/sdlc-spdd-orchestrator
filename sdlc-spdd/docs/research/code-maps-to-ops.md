# code_maps_to_ops — automated check and human remainder

**Work ID:** FEAT-016-intent-code-traceability  
**Constructs:** C-DRIFT (hunk mapping), C-COMPLY (review minima)

## Automated check (enforced)

Each canvas operation (`### T##`) must include a `- Files:` line naming at least one path. `gate_check(code)` fails when a T## has no Files mapping.

This is **not** proof that the diff implements the operation. It is a contract that the author named the intended paths.

## Human remainder (not enforced here)

C-DRIFT still needs a rater (or FEAT-016 later tooling) to map **hunks** to those operations and to catch extra behavior in an “allowed” file. TEST-001 / TEST-002 own that protocol.

`tests_updated`, `operations_task_sized`, `architect_review`, and `canvas_synced` remain **advisory** labels until a later Work ID implements them.
