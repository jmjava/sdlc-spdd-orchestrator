# Review: REF-003-retire-bash-workflow-dual-path

**Work ID:** REF-003-retire-bash-workflow-dual-path
**Date:** 2026-09-14
**Result:** Approved With Notes
**Pull Request:** https://github.com/jmjava/sdlc-spdd-orchestrator/pull/321
**Reviewed Commit:** `cb19e84e50eda9cf6e68e61ca90415cee7ef8b79`

## Summary

PR #321 implements the approved Python-only lifecycle contract. The bash
workflow, gate, pointer, and team-registry twins are deleted from the shipped
templates and the dogfood copies, `scripts/sdlc.sh` is a thin dispatcher that
requires Python 3.12 and an importable `sdlc_engine`, and the retained
session/capture/accept utilities call the engine rather than reimplementing it.
All six operations T01–T06 are complete and every acceptance criterion is
verified against a run, not inferred.

Readiness was **Ready For Coding** when implementation began; coding did not
precede the architecture gate.

## Proof

| Check | Result |
|-------|--------|
| PR CI | 25/25 check runs successful at `cb19e84` |
| Suite 1 — unit | 288 passed |
| Suite 2 — integration | 151 passed, coverage 91.58% (gate 90%) |
| Research suite | 87 passed |
| Shell harnesses | 24/25 passed; `test-guide-stack-live.sh` skipped (needs a live Guide + Neo4j stack, outside this PR's CI) |
| Live-consumer shell matrix | 113 passed, 0 failed, 1 skipped |
| Installed-target smoke | 45/45 install checks; claim/pointer/next/status/gate/capture/accept exercised against a fresh target |
| ShellCheck | `bash -n` clean; `-S error` clean over `scripts`, `templates/agent-context`, `tests`, `.cursor` |
| Complexity gate | PASS against `origin/main` |
| Canvas / requirements / adapter / diagram validators | PASS |
| Shipped LOC removed | 3,100 template LOC (6,200 including dogfood copies); target was 3,000 |

## Acceptance Criteria

Every criterion was executed; the transcript is in
`/opt/cursor/artifacts/ref003-acceptance.log`.

- Retired twins absent from `templates/agent-context/` and `sdlc-spdd/scripts/`.
- `SDLC_ENGINE=shell` exits 2 with the Python-only message.
- `SDLC_GATE_ENGINE=shell` exits 2 with the same single-engine contract.
- A missing interpreter (`PYTHON=/nonexistent/python`) and a wrong-version
  interpreter (3.11 stub) both exit 1 with the setup hint and no bash fallback.
- No touched utility invokes bare `python3` for engine behavior; all engine
  calls resolve `SDLC_PY`.
- `cmd_shell` resolves helpers in orchestrator `scripts/` and installed
  `sdlc-spdd/scripts/`, proven by unit tests and a live installed-target call.
- Fresh install omits the twins, upgrade backs up then deletes pre-existing
  copies, and install verification asserts their absence.
- Current README, testing, engine, template, and research docs describe one
  mandatory Python engine.

## Safeguards

Each canvas safeguard was checked against the diff or a run.

| Safeguard | Verdict |
|-----------|---------|
| Exact-path deletion only under framework-owned template/install locations | Holds. Upgrade deletes the three named files under `<target>/sdlc-spdd/scripts/` only; no globs or directory sweeps. |
| Upgrade never deletes unrelated user scripts | Holds. A hand-placed `sdlc-workflow.sh` was backed up into `.sdlc-spdd-upgrade-backups/` before removal, and no other file in `scripts/` was touched. |
| Missing Python fails loudly with setup guidance | Holds, and improved. A missing interpreter and a 3.11 interpreter both exit non-zero naming the interpreter and `./scripts/setup-engine-venv.sh`. The truncated `is 3.` message that hid this failure in CI is fixed. |
| Shell-engine requests fail; they never silently switch behavior | Holds. `SDLC_ENGINE=shell` and `SDLC_GATE_ENGINE=shell` exit 2 in both the orchestrator checkout and a fresh installed target. |
| Retained utility output and persisted records receive focused regression coverage before twin deletion | Holds. The verify-receipt, gate-review, gate-advisory, and canvas-readiness harnesses plus `engine/tests_unit/` cover capture staging, receipt refusal, and gate rows. |
| Installed-target smoke proves source-checkout assumptions did not leak | Holds. A fresh target passed 45/45 install checks and ran the full lifecycle, including `sdlc-engine shell` resolving a helper under `sdlc-spdd/scripts/`. |
| Full current harness inventory is measured and run, not inferred from stale requirement prose | Holds. The inventory was counted (25) and run (24 pass, 1 live-stack skip); the stale 30 and 28 are reconciled in the requirement and canvas. |
| Never contribute Guide work upstream to `embabel/guide` | Holds. No Guide or upstream change is in this diff. |

## Findings

1. **Defect found and fixed during review — complexity gate.** Extending
   `cmd_shell` with installed-target lookup raised its CCN from 4 to 6, and the
   gate fails on any rise in a touched function. Candidate enumeration and
   lookup moved into `_shell_script_candidates` and `_resolve_shell_script`.
2. **Defect found and fixed during review — harness Python resolution.** Three
   migrated harnesses passed `PYTHON="${REPO_ROOT}/.venv/bin/python"` to the
   dispatcher, but CI installs the engine into the job interpreter and never
   creates a repo venv, so `test-sdlc-workflow` failed. Resolution now goes
   through one shared `tests/lib/engine-python.sh` helper, which
   `test-integration-merge.sh` and `tests/live-consumer/lib.sh` also use
   instead of their own copies of the same fallback chain.
3. **Defect found and fixed during review — misleading version error.**
   `resolve_engine_python` parsed the interpreter version with
   `read -r major minor <<<"$(...)"`. When the interpreter could not run, the
   here-string still supplied one empty line, so `read` returned 0 and the
   guard printed `is 3.` with an empty minor. It now detects the empty version
   string and reports an unrunnable interpreter, and prints the full
   `major.minor` when the version is simply wrong. Covered in
   `tests/test-scripts-lib.sh`.
4. **Scope addition, reconciled.** T05 extended past the planned doc set to the
   research docs (`engine-sut.md`, `evaluation-protocol.md`,
   `threats-to-validity-and-replication.md`). Their "Defaults" and
   replication-freeze tables still described `SDLC_ENGINE=auto` and a
   `SDLC_GATE_ENGINE=shell` fallback as live knobs, which is no longer true.
   `tests/research/test_ref001_sut.py` pinned the `sdlc_engine=auto` prose, so
   it now asserts the rejection contract instead.
5. **Scope addition, reconciled.** AC5 was not met when review began:
   `start-agent-session.sh` and `capture-session-memory.sh` still shaped
   engine records through bare `python3` heredocs. Both already resolve
   `SDLC_PY` earlier and exit on failure, so the three call sites now use it.
6. **Inventory reconciled.** The requirement's pre-REF-002 count of 30 shell
   harnesses and the canvas's 28 are both stale; retiring the three twin
   harnesses to pytest leaves 25. The canvas records all three numbers.

## Required Changes

None. Findings 1–3 are fixed in this PR; 4–6 are recorded in the canvas and
requirement.

## Not Covered

- `test-guide-stack-live.sh` needs a live Guide + Neo4j stack and was not run.
  It does not exercise the dispatcher contract this Work ID changed.
- Manual chat smoke in Cursor/Copilot/Claude Code was not performed; the
  command adapters changed only in generated prose (removing "even when
  `SDLC_ENGINE=shell`"), and adapter parity plus spec generation are green.
