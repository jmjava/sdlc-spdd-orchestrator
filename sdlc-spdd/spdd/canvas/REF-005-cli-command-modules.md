# REASONS Canvas: REF-005-cli-command-modules — CLI CommandResult modules

## Metadata

- Work ID: REF-005-cli-command-modules
- Work Type: Refactor
- Status: In Progress
- Readiness: Ready For Coding
- Created: 2026-10-17
- Updated: 2026-10-17
- Milestone: milestone-3
- Priority / size: P1 / M
- Depends on: REF-003-retire-bash-workflow-dual-path (Complete)
- Blocks: REF-011-split-issue-sync-adapters
- Related: REF-004-split-installer-blueprints, REF-006-storage-records-and-atomic-appends
- Requirement: `sdlc-spdd/requirements/milestones/milestone-3/REF-005-cli-command-modules.md`
- Analysis: `sdlc-spdd/spdd/analysis/REF-005-cli-command-modules-analysis.md`
- Beck stage: make it right
- Branch: `cursor/ref-005-cli-command-modules-b3d3`
- Skills: none requested (`#`/`!` markers absent)

## R - Requirements

### User Goal

`sdlc-engine` commands are importable, testable units. Importing the CLI
does not load storage, issues, Flask, or HTTP stacks. Handlers return
result objects instead of printing.

### Business / Product Goal

Milestone 3 P1: one maintainable engine API. Later work (REF-011, tests,
console split) can depend on command modules instead of a 981-line
print-handler file.

### Acceptance Criteria

- [x] `python -c 'import sdlc_engine.cli'` imports no Flask, sqlite3, or urllib modules (test)
- [x] No `cmd_*` function exceeds CCN 10
- [x] `tests/test-sdlc-engine-shim.sh` and unit CLI tests pass
- [x] Command names and flags unchanged
- [x] `cli.py` has no `cmd_*` re-exports; `issue_tracker.py` is deleted
- [x] Package `__init__.py` does not import workflow/registry/archive
- [x] `canvas.py` library functions do not raise `SystemExit`

### Non-Goals

- Changing command names or flags
- Typed storage / Guide transport / installer blueprints / session pythonize
- Embabel upstream PRs

## E - Entities

- `CommandResult` — `exit_code`, `stdout`, `stderr`
- Command module — `register(subparsers)`, `run(args) -> CommandResult`
- `cli.main` — parse, invoke `run`, emit streams, return exit code
- `cli_parser.build_parser` — assembles subparsers by calling `register`
- Deleted: `cli_commands.py`, `issue_tracker.py`

### Files likely affected

- `engine/src/sdlc_engine/commands/`
- `engine/src/sdlc_engine/cli.py`
- `engine/src/sdlc_engine/cli_parser.py`
- `engine/src/sdlc_engine/cli_commands.py` (delete)
- `engine/src/sdlc_engine/__init__.py`
- `engine/src/sdlc_engine/canvas.py`
- `engine/src/sdlc_engine/issue_tracker.py` (delete)
- `engine/src/sdlc_engine/issues.py`
- `engine/tests_unit/test_cli_import.py` (new)
- `engine/tests_unit/test_engine_shared.py`
- `engine/tests_unit/test_cli.py`, `test_cli_shell.py`
- `docs/engine-v2.md`, `engine/README.md`, `CHANGELOG.md`

## A - Approach

Preserve operator-visible CLI behavior. Introduce `CommandResult` and one
module per top-level verb. `register()` owns argparse; `run()` lazy-imports
services and returns a result. `cli.main` is the only printer.

`import sdlc_engine.cli` loads `cli.py` + `cli_parser.py` + `__init__.py`
version only. Command modules load when `build_parser()` runs. Heavy
services load when that verb's `run()` runs.

Fat verbs (`context`, `issues`, `db`, `local`, `template`) use a dispatch
table plus helpers so no function is a long `if action ==` chain.

`issues.py` imports tracker constants from `integration_config`.
`canvas._resolve_canvas_path` raises `ValueError`; `check_diff_scope_main`
prints and returns 2.

Assumption: `from sdlc_engine.cli import build_parser, main` stays public.
`cmd_*` names are not a supported import surface.

## S - Structure

### Files to add

- `engine/src/sdlc_engine/commands/__init__.py`
- `engine/src/sdlc_engine/commands/result.py`
- `engine/src/sdlc_engine/commands/util.py`
- `engine/src/sdlc_engine/commands/<verb>.py` for each top-level verb
- `engine/tests_unit/test_cli_import.py`
- `sdlc-spdd/spdd/reviews/REF-005-cli-command-modules-review.md` (later)

### Files to delete

- `engine/src/sdlc_engine/cli_commands.py`
- `engine/src/sdlc_engine/issue_tracker.py`

### Files to modify

- `engine/src/sdlc_engine/cli.py`
- `engine/src/sdlc_engine/cli_parser.py`
- `engine/src/sdlc_engine/__init__.py`
- `engine/src/sdlc_engine/canvas.py`
- `engine/src/sdlc_engine/issues.py`
- `engine/tests_unit/test_engine_shared.py`
- `docs/engine-v2.md`, `engine/README.md`, `CHANGELOG.md`
- This canvas, the requirement, `MILESTONE-3.md` when Complete

### Test structure

- Isolated subprocess: `import sdlc_engine.cli` then assert `sys.modules`
  contains none of `flask`, `sqlite3`, `urllib`, `urllib.request`,
  `urllib.error`
- Existing `main([...])` unit tests and `tests/test-sdlc-engine-shim.sh`
- No `cmd_*` def remains with CCN > 10 (lizard or AST walk)
- `check_diff_scope_main` missing-arg path returns 2 without `SystemExit`

## O - Operations

### T01 - CommandResult and per-verb modules

- Status: Complete
- Description: Add `CommandResult` and `commands/<verb>.py` with
  `register`/`run`. Rewrite `cli_parser.build_parser` to call `register`.
  Slim `cli.main` to emit results. Delete `cli_commands.py` and `cli.py`
  handler re-exports. Lazy-import services inside `run()`. Preserve
  command names, flags, stdout/stderr, and exit codes.
- Files: `engine/src/sdlc_engine/commands/`,
  `engine/src/sdlc_engine/cli.py`,
  `engine/src/sdlc_engine/cli_parser.py`,
  `engine/src/sdlc_engine/cli_commands.py`,
  `engine/tests_unit/test_engine_shared.py`,
  `engine/tests_unit/test_cli_import.py`
- Tests: new light-import test; `test_cli.py`, `test_cli_shell.py`,
  `test_engine_shared.py`
- Validation: `python3 -m pytest engine/tests_unit/test_cli.py engine/tests_unit/test_cli_shell.py engine/tests_unit/test_cli_import.py engine/tests_unit/test_engine_shared.py -q`

### T02 - Library SystemExit and shim deletions

- Status: Complete
- Description: `canvas._resolve_canvas_path` raises `ValueError`;
  `check_diff_scope_main` returns 2. Delete `issue_tracker.py`; point
  `issues.py` at `integration_config`. `__init__.py` exports `__version__`
  only.
- Files: `engine/src/sdlc_engine/canvas.py`,
  `engine/src/sdlc_engine/issue_tracker.py`,
  `engine/src/sdlc_engine/issues.py`,
  `engine/src/sdlc_engine/__init__.py`,
  `engine/tests_unit/test_canvas.py`
- Tests: canvas scope tests; import of `sdlc_engine` still exposes version
- Validation: `python3 -m pytest engine/tests_unit/test_canvas.py engine/tests_unit/test_engine_shared.py -q`

### T03 - Docs and acceptance greps

- Status: Complete
- Description: Update engine layout docs and changelog. Confirm no
  `cmd_*` re-exports, no `issue_tracker.py`, and shim test still passes.
- Files: `docs/engine-v2.md`, `engine/README.md`, `CHANGELOG.md`,
  `sdlc-spdd/requirements/milestones/milestone-3/REF-005-cli-command-modules.md`,
  `sdlc-spdd/requirements/milestones/milestone-3/MILESTONE-3.md`,
  this canvas
- Tests: `tests/test-sdlc-engine-shim.sh`
- Validation: `bash tests/test-sdlc-engine-shim.sh`

## N - Norms

- One approved operation per commit
- Do not change command names or flags
- `run()` lazy-imports heavy services
- `cli.main` is the only place command output is printed
- Preserve exact stdout/stderr including `end=""` cases
- Never contribute Guide work upstream to `embabel/guide`

## S - Safeguards

- No new CLI verbs or options
- Do not rewrite `IssueSyncService` (REF-011)
- Do not change installer/viewer HTTP payloads (REF-004 / REF-008)
- Do not change ledger append locking (REF-006)
- Extra files beyond a T## `Files:` list are incomplete work

## Architecture notes

Parser construction is deferred to `build_parser()` so `import
sdlc_engine.cli` stays light. Command modules may import
`CommandResult`, argparse, and `project_from` at module top; they must
not import `ContextStore`, `LocalIndex`, `IssueSyncService`, Flask apps,
or `urllib` at module top.

Installer/console/dashboard remain one `run()` with three `register()`
names. Viewer and installer still fail with the same Flask-missing
stderr when extras are absent.

## Required tests

- Subprocess light-import of `sdlc_engine.cli`
- Existing CLI unit tests and engine shim
- Canvas missing-arg path without `SystemExit` from `_resolve_canvas_path`

## Quality gates

- No `cmd_*` CCN > 10
- `ruff` on touched engine modules
- Shim + focused pytest green before marking a T## complete
