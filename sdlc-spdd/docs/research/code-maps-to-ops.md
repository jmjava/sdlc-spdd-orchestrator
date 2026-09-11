# code_maps_to_ops — automated check and human remainder

**Work ID:** FEAT-016-intent-code-traceability  
**Constructs:** C-DRIFT (hunk mapping), C-COMPLY (review minima)

## Automated check (enforced)

### Enter-code (FEAT-016, `gate_check`)

Each canvas operation (`### T##`) must include a `- Files:` line naming at least one path. `gate_check(code)` fails when a T## has no Files mapping.

This is **not** proof that the diff implements the operation. It is a contract that the author named the intended paths.

### Review-time path scope (Kasana I2 / CASP-04)

`/sdlc-spdd-review` runs `scripts/check-operation-diff-scope.sh` (pure helper: `check_operation_diff_scope` in `engine/src/sdlc_engine/canvas.py`). Changed paths from `git diff --name-only HEAD` (uncommitted vs HEAD) plus `git diff --name-only <base>...HEAD` must be a subset of the selected/completed T## `Files:` union (or all T## if none selected) plus allowed test paths. Default `<base>` is the merge-base with `origin/main`, `main`, `origin/master`, or `master`. A missing or invalid `--base` exits non-zero instead of treating the change list as empty. Allowed test paths:

- under `tests/`, `engine/tests_unit/`, `engine/tests_integration/`, or `engine/tests_e2e/`
- or basename `test_*.py` / `*_test.py` / `*.spec.md`

Repo-relative paths only; `..` traversal is rejected. Renames and deletes are the names git reports. Extra production paths: review cannot be **Approved** or **Approved With Notes**.

This is **not** `gate_check(code)` and is not an `ENFORCED_GATES` entry.

## Human remainder (not enforced here)

Path-level scope is automated at review. C-DRIFT still needs a rater (or TEST-002) to map **hunks** to those operations and to catch extra behavior in an “allowed” file. TEST-001 / TEST-002 own that protocol.

`tests_updated`, `operations_task_sized`, `architect_review`, and `canvas_synced` remain **advisory** labels until a later Work ID implements them.
