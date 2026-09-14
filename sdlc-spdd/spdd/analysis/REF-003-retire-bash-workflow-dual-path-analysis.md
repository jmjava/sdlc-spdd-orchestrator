# REF-003 Analysis — Retire the bash workflow twin; Python is the only flow

## Metadata

- Work ID: REF-003-retire-bash-workflow-dual-path
- Requirement: `sdlc-spdd/requirements/milestones/milestone-3/REF-003-retire-bash-workflow-dual-path.md`
- Milestone: Milestone 3 — One flow on storage v3 (P0, size L)
- Opened by: `sdlc-spdd/spdd/analysis/SPIKE-005-architecture-review-analysis.md` finding M1
- Timestamp: 2026-09-14
- Beck stage: make it right
- Prior related work: `REF-001-engine-single-source`, `REF-002-purge-pre-v3-compat`
- Context retrieval: no work-specific analysis records; optional Guide backend was unavailable, so file/ledger retrieval remained authoritative.

## Scope Lock

### In Scope for This Work

Remove the duplicate bash implementations of workflow, gate, pointer, and team
registry. Python `sdlc_engine` becomes mandatory for all lifecycle behavior.
Install and upgrade remain bash packaging scripts, and session/capture remain
shell utilities until REF-010, but those utilities must call the Python engine
instead of sourcing retired behavior.

1. **Mandatory dispatcher**: simplify `scripts/sdlc.sh` and its installed
   dogfood copy so every lifecycle command executes `python -m sdlc_engine`
   through `resolve_engine_python`. Remove workflow-script probing and shell
   fallback. `SDLC_ENGINE=shell` and `SDLC_GATE_ENGINE=shell` fail with a clear
   Python-only message. Existing `SDLC_ENGINE=python` callers remain harmless;
   they no longer select different semantics.
2. **Retained shell utilities**: preserve `start-agent-session.sh`,
   `capture-session-memory.sh`, and `accept-lessons.sh`, but remove imports of
   `sdlc-pointer.sh`, `sdlc-workflow.sh`, and `sdlc-team-registry.sh`.
   Pointer/status/next/team/context-accept behavior is obtained through the
   Python CLI. Any Python invocation uses `resolve_engine_python`, never bare
   `python3`.
3. **Installed-target shell bridge**: extend `cmd_shell` to resolve scripts
   from both orchestrator `scripts/` and installed
   `<target>/sdlc-spdd/scripts/`. Preserve argument forwarding and target
   working directory.
4. **Delete the twin**: remove
   `templates/agent-context/sdlc-workflow.sh` (2,046 LOC),
   `sdlc-team-registry.sh` (927 LOC), and `sdlc-pointer.sh` (127 LOC), plus
   their dogfood copies under `sdlc-spdd/scripts/`. The shipped template
   reduction is exactly 3,100 LOC before replacement code.
5. **Install and upgrade**: stop installing the three retired scripts,
   remove them from existing v3 installs during upgrade, and change install
   verification to require their absence while requiring executable
   `sdlc.sh`. Initialization must not recreate them.
6. **Tests and CI**: rewrite dispatcher, pointer, workflow/gate, archive, and
   installed-target tests to exercise Python-only behavior. The repository now
   contains 28 `tests/test-*.sh` harnesses (the requirement's count of 30
   predates REF-002 deleting two consolidation harnesses); all 28 must either
   remain green against the Python-only dispatcher or be replaced by pytest
   coverage in the same operation. Remove CI workflows only when their named
   harness is removed.
7. **Documentation**: update `README.md`, `TESTING.md`, `docs/engine-v2.md`,
   shipped documentation mirrors, template runtime documentation, and
   `CHANGELOG.md` to state that there is one mandatory Python engine and bash
   is retained only for packaging or explicitly named utilities.

### Not in Scope

| Item | Why deferred | Target |
|------|--------------|--------|
| Reimplementing session/capture in Python | Explicit requirement non-goal; wrappers only lose dependencies on the retired twin | REF-010-pythonize-session-and-capture |
| Removing install/upgrade shell | Bash remains the packaging layer | none |
| Typed records and atomic JSONL appends | Storage hardening, not engine consolidation | REF-006-storage-records-and-atomic-appends |
| Splitting issue synchronization | Unrelated service boundary | REF-011-split-issue-sync-adapters |
| Guide changes or upstream contributions | Explicit non-goal and workspace safeguard | none |
| Rewriting historical milestone/canvas/review records | They describe past dual-engine decisions and remain audit evidence | none |

## Domain Keywords

- Python-only engine, mandatory engine, single flow
- workflow, gate, pointer, team registry
- thin dispatcher, shell bridge, installed target
- `SDLC_ENGINE`, `SDLC_GATE_ENGINE`, `SDLC_PY`
- session brief, capture, accept
- init, upgrade, verify install
- shell harness, pytest replacement, LOC reduction

## Code Areas

- Dispatcher and Python resolution: `scripts/sdlc.sh`, `scripts/lib/python.sh`
- Python CLI: `engine/src/sdlc_engine/cli_commands.py`,
  `engine/src/sdlc_engine/cli_parser.py`
- Retained utilities: `scripts/start-agent-session.sh`,
  `scripts/capture-session-memory.sh`, `scripts/accept-lessons.sh`
- Packaging: `scripts/init-project.sh`, `scripts/upgrade-project.sh`,
  `scripts/verify-project-install.sh`
- Retired templates: `templates/agent-context/sdlc-{workflow,team-registry,pointer}.sh`
- Dogfood runtime mirror: `sdlc-spdd/scripts/`
- Tests: `engine/tests_unit/`, `engine/tests_integration/`, `tests/test-*.sh`,
  `tests/live-consumer/`, `.github/workflows/`
- Docs: `README.md`, `TESTING.md`, `docs/engine-v2.md`,
  `templates/agent-context/README.md`, `sdlc-spdd/docs/`, `CHANGELOG.md`

## Existing Concepts

- `scripts/sdlc.sh` currently defaults `SDLC_ENGINE=auto`, probes whether the
  Python package is importable, routes selected commands to Python, and falls
  through to `sdlc-workflow.sh`. `SDLC_ENGINE=shell` bypasses Python except
  for a hard-coded list of Python-only commands.
- `sdlc-workflow.sh` sources pointer and registry implementations and contains
  a second lifecycle phase table, gate table, state machine, artifact scanner,
  capture wrapper, and command parser.
- `start-agent-session.sh` sources all three retired scripts for pointer
  updates, workflow synchronization, recommended commands, and Jira/team
  snippets. It also invokes bare `python3` in database lookup fallbacks.
- `capture-session-memory.sh` already writes v3 staged lesson records itself.
  Its only workflow dependency is a final optional call that records a
  shell-workflow gate marker; Python gates use ledger validation receipts and
  do not need that marker.
- `accept-lessons.sh` contains Python-engine detection plus a pure-shell
  fallback implemented with inline Python. The fallback is a second
  persistence behavior and must disappear; Python already implements
  `context accept`.
- `cmd_shell` currently searches only `<root>/scripts`, which works in this
  orchestrator but not in installed consumers whose helpers live under
  `<root>/sdlc-spdd/scripts`.
- Init/upgrade copy all three retired template files. Verification currently
  requires them to be executable.

## New Concepts

- **Mandatory engine**: importability is a prerequisite, not a routing choice.
  Every lifecycle command has one parser, one state machine, one registry, and
  one gate implementation.
- **Utility bridge**: commands that intentionally remain shell are invoked
  through the Python CLI's `shell` bridge. Their shell implementation is
  packaging/session functionality, not a lifecycle fallback.
- **Retired-file invariant**: fresh installs and upgrades contain
  `sdlc-spdd/scripts/sdlc.sh` but do not contain the three bash twins.
- **Historical-reference boundary**: active operator docs and tests must not
  advertise shell-engine selection; completed canvases/reviews and changelog
  history may retain factual references to the former design.

## Strategic Direction

Implement in dependency order:

1. Make the Python shell bridge support installed targets and add focused unit
   coverage.
2. Convert the dispatcher and retained utilities to mandatory Python behavior
   while the old files still exist, proving there is no runtime dependency.
3. Update packaging and verification, then delete both template and dogfood
   copies of the twin.
4. Convert or remove affected shell harnesses and CI entries, preserving
   equivalent assertions in Python tests.
5. Synchronize current docs and run the complete validation matrix.

Each operation must be independently green and committed separately. Deletion
does not begin until tests prove retained utilities and installed-target
bridging no longer source the old scripts.

## Test Plan

### Automated

- Focused pytest for `cmd_shell` source-checkout and installed-target
  resolution, missing scripts, argument forwarding, and working directory.
- Dispatcher harness tests for unset/default mode, `SDLC_ENGINE=python`,
  explicit rejection of `SDLC_ENGINE=shell` and
  `SDLC_GATE_ENGINE=shell`, missing engine install hint, and resolved
  Python 3.12 execution.
- Session/capture/accept tests proving no retired file is present and all
  persisted state is produced by Python/v3 records.
- Init, upgrade, verification, installer unit/integration, and live-consumer
  tests proving fresh and upgraded targets omit the twin.
- All 28 remaining `tests/test-*.sh` harnesses, full engine unit and
  integration suites, command-spec validation, ShellCheck, and the full local
  CI runner.

### Terminal smoke

Initialize a temporary target, verify its installed layout, and exercise
`claim`, `next`, `status`, `gate`, `pointer`, shell-bridged session capture,
and `context accept`. Confirm the retired scripts are absent and unsupported
engine environment values fail non-zero with the documented message.

## Risks and Gaps

1. **Installed targets may not contain engine source.** The dispatcher must
   emit the existing Python 3.12/setup hint when the package is unavailable;
   it must not silently recover to bash.
2. **Session brief content can regress.** Replacing sourced functions with CLI
   output may alter formatting or omit Jira/recommended-command context.
   Preserve user-visible sections where Python exposes equivalent data and
   cover stable contracts rather than exact incidental prose.
3. **Environment variables are used widely.** Active scripts/tests that set
   `SDLC_ENGINE=python` should continue to work, but shell/auto selection must
   no longer produce alternate behavior. Historical records should not be
   mechanically rewritten.
4. **Upgrade deletion is destructive but intentional.** Restrict deletion to
   the three exact framework-owned paths under `sdlc-spdd/scripts`; never
   remove arbitrary user shell files.
5. **Bare Python calls remain in retained utilities.** Only engine-facing
   calls are mandatory scope, but touched utility paths should use
   `resolve_engine_python` consistently to avoid interpreter drift.
6. **The requirement's harness count is stale.** REF-002 removed two harnesses
   before this work. Validation must use the current inventory of 28 and
   document the reconciliation rather than recreating obsolete tests.

## Recommendation

Proceed to `/sdlc-spdd-plan` and `/sdlc-spdd-architect`. The behavior contract
is sufficiently specific: one mandatory Python lifecycle engine, exact
retired paths, explicit rejection semantics, retained shell utility boundary,
and a measurable 3,100-line shipped-code reduction.
