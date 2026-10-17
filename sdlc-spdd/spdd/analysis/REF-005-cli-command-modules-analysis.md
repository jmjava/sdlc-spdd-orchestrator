# Analysis: REF-005 — CLI command modules with CommandResult

## Metadata

- Work ID: REF-005-cli-command-modules
- Requirement: `sdlc-spdd/requirements/milestones/milestone-3/REF-005-cli-command-modules.md`
- Milestone: Milestone 3 — One flow on storage v3 (P1, size M)
- Opened by: `sdlc-spdd/spdd/analysis/SPIKE-005-architecture-review-analysis.md` finding M5
- Timestamp: 2026-10-17
- Beck stage: make it right
- Prior related work: `REF-003-retire-bash-workflow-dual-path` (Complete; Python is the only engine)
- Context retrieval: no work-specific analysis records; `CONTEXT_BACKEND=files`
- Skills: none requested (`#`/`!` markers absent)

## Scope Lock

### In Scope for This Work

Make `sdlc-engine` a lazy, testable command API. Command names and flags stay
exactly as they are today. Behavior (stdout, stderr, exit codes) is preserved;
only the call shape changes.

1. **CommandResult + per-verb modules**: `engine/src/sdlc_engine/commands/<verb>.py`
   exposes `register(subparsers)` and `run(args) -> CommandResult`. Shared
   helpers live in `commands/result.py` and `commands/util.py`. `cli.main`
   emits `stdout`/`stderr` and returns `exit_code`.
2. **Lazy imports**: `import sdlc_engine.cli` must not load Flask, `sqlite3`, or
   `urllib`. Heavy services (`ContextStore`, `LocalIndex`, `IssueSyncService`,
   viewer/installer Flask apps, Guide HTTP) are imported inside `run()`.
   `cli_parser.build_parser` imports command modules only when the parser is
   built, not at `cli` import time.
3. **Library SystemExit**: `canvas.py` `_resolve_canvas_path` raises a value
   error instead of `SystemExit`. `check_diff_scope_main` returns an exit code.
   The `if __name__ == "__main__"` process boundary may still call
   `SystemExit`.
4. **Delete shims**: remove `cli.py` `cmd_*` re-exports and
   `issue_tracker.py`. `issues.py` imports tracker constants from
   `integration_config`. Package `__init__.py` keeps `__version__` only —
   no eager `WorkflowEngine` / `TeamRegistry` / `ArchiveService` import.
5. **Complexity**: no leftover `cmd_*` handler exceeds CCN 10. Fat verbs
   (`context`, `issues`, `db`, `local`, `template`) dispatch to named helpers.
6. **Regression**: `tests/test-sdlc-engine-shim.sh` and existing unit CLI tests
   (`test_cli.py`, `test_cli_shell.py`, and other `main([...])` callers) stay
   green. `test_engine_shared.py` stops importing `cli_commands`.

### NOT in Scope (Deferred)

| Item | Why deferred | Target |
|------|--------------|--------|
| Changing command names or flags | Explicit non-goal | none |
| Typed storage records / locked JSONL appends | Persistence stability, not CLI shape | REF-006-storage-records-and-atomic-appends |
| GuideClient as sole HTTP path | Transport consolidation | REF-007-single-guide-transport |
| Split installer Flask blueprints | HTTP console structure | REF-004-split-installer-blueprints |
| Console/viewer `--lan` auth | Hardening after the split | REF-008-console-viewer-hardening |
| Pythonize session/capture / one accept verb | Still bash utilities | REF-010-pythonize-session-and-capture |
| Split IssueSyncService adapters | Service internals, not CLI modules | REF-011-split-issue-sync-adapters |
| Hermetic unit suite / CI workflow collapse | Test layout | TEST-004, CHORE-005 |
| Embabel upstream | Workspace safeguard | none |
| installer/viewer `SystemExit` on missing Flask | Named on REF-004 | REF-004 |

### Reference Materials (Context Only, Not Deliverables)

- `SPIKE-005` M5 (CLI-as-monolith) and M14 (issues mega-service stays in REF-011)
- `docs/engine-v2.md` layout list naming `cli_commands.py`
- Current handlers in `engine/src/sdlc_engine/cli_commands.py` (981 LOC, 154 `print`s)

## Domain Keywords

- CommandResult, result object, exit code
- command module, register, run, subparser
- lazy import, heavy service
- cli_parser, cli_commands, compatibility re-export
- issue_tracker shim, integration_config
- SystemExit, library module
- CCN, cyclomatic complexity

## Code Areas

- `engine/src/sdlc_engine/commands/` (new)
- `engine/src/sdlc_engine/cli.py`
- `engine/src/sdlc_engine/cli_parser.py`
- `engine/src/sdlc_engine/cli_commands.py` (delete)
- `engine/src/sdlc_engine/__init__.py`
- `engine/src/sdlc_engine/canvas.py`
- `engine/src/sdlc_engine/issue_tracker.py` (delete)
- `engine/src/sdlc_engine/issues.py` (import path only)
- `engine/tests_unit/` CLI and shared import tests
- `docs/engine-v2.md`, `engine/README.md`, `CHANGELOG.md`

## Existing Concepts

- `sdlc-engine` argparse surface in `cli_parser.build_parser` (33 top-level verbs;
  `context`, `db`, `local`, `work`, `template` use subparsers)
- Handlers as `cmd_*` functions that print and return `int`
- `cli.py` re-exports every `cmd_*` "for compatibility"
- `cli_commands` eagerly imports `ContextStore`, `LocalIndex`, `IssueSyncService`,
  `SunsetService`, ADF libraries
- `issue_tracker.py` re-exports `integration_config`
- `canvas.check_diff_scope_main` is a library CLI that raises `SystemExit` on
  missing canvas arguments
- Package `__init__` re-exports workflow/registry/archive types
- Tests invoke `sdlc_engine.cli.main` and assert stdout via `capsys`

## New Concepts

- `CommandResult` (`exit_code`, `stdout`, `stderr`) as the handler return type
- Per-verb command module with `register` + `run`
- Parser construction as the only place command modules are imported
- Dispatch helpers inside fat verbs so no handler exceeds CCN 10

## Strategic Direction

Keep the operator-facing CLI identical. Move each verb behind a result object
and a lazy `run()`. Do not introduce a plugin loader or change flags. Delete
compatibility re-exports rather than keep a `cli_commands` facade — the
requirement names those deletions as acceptance, and
`test_engine_shared.py` is the only in-repo `cli_commands` import.

Trade-off: ~30 small modules vs. grouping related verbs. The requirement
asks for `commands/<verb>.py`; grouping would hide the contract. Fat verbs
stay one module and split internally.

## Risks and Gaps

- `print(..., end="")` vs `print(...)` must be preserved or `test_cli.py` /
  shim stdout assertions drift
- `import sdlc_engine.cli` also loads `sdlc_engine/__init__.py`; leaving
  workflow imports there may not fail the Flask/sqlite3/urllib test but
  violates the named `__init__` acceptance
- `issues.py` still imports `urllib` for REF-011; that is fine as long as
  `commands/issues.py` imports `IssueSyncService` only inside `run()`
- CCN of a single `run()` that is a long `if action ==` chain will still
  fail the spirit of the gate; dispatch tables are required
- `build_parser` itself is 650+ NLOC today; moving `add_parser` into
  `register()` is what shrinks it. Do not leave a copy of the argparse
  tree in `cli_parser.py`

## Recommendation

Proceed to `/sdlc-spdd-plan`. Scope is locked; REF-003 is complete so the
dependency is satisfied. No clarifying questions.
