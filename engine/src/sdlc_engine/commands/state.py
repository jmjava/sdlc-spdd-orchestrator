"""Workflow state commands: next/status/advance/gate/pointer/shell."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from .. import __version__
from ..local_sessions import LocalSessionService
from ..phases import GATE_LABELS, advisory_gates_for_phase, format_advisory_gate_rows
from ..pointer import PointerError, PointerStore
from ..project import Project
from ..workflow import WorkflowEngine


def _project(args: argparse.Namespace) -> Project:
    return Project.resolve(getattr(args, "root", None))


def cmd_next(args: argparse.Namespace) -> int:
    print(WorkflowEngine(_project(args)).next_text(), end="")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    eng = WorkflowEngine(_project(args))
    if args.json:
        print(eng.status_json(args.work_id))
    else:
        wid = args.work_id or eng.pointer.get() or "(none)"
        print(f"Pointer: {eng.pointer.get() or '(none)'}")
        print(f"Work ID: {wid}")
        if eng.pointer.get() or args.work_id:
            print(eng.status_json(args.work_id))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    state = WorkflowEngine(_project(args)).resume(args.work_id, phase=args.phase, force=args.force)
    print(f"Resumed {state.work_id} at phase: {state.phase}")
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    try:
        state = WorkflowEngine(_project(args)).advance(
            to=args.to, force=getattr(args, "force", False)
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Advanced to phase: {state.phase}")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    eng = WorkflowEngine(_project(args))
    work_id = args.work_id or eng.pointer.get()
    if not work_id:
        print(
            "gate: no Work ID (pass --work-id or set the pointer via claim/resume)",
            file=sys.stderr,
        )
        return 2
    try:
        ok, failures = eng.gate_check(work_id, args.phase)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    advisory = [
        {"gate": name, "label": GATE_LABELS[name], "ran": False}
        for name in advisory_gates_for_phase(args.phase)
    ]
    advisory_rows = format_advisory_gate_rows(args.phase)
    if args.json:
        print(
            json.dumps(
                {
                    "work_id": work_id,
                    "phase": args.phase,
                    "ok": ok,
                    "failures": failures,
                    "advisory": advisory,
                },
                indent=2,
            )
        )
    else:
        if ok:
            print(f"gate {args.phase}: OK for {work_id}")
            for row in advisory_rows:
                print(row)
        else:
            print(f"gate {args.phase}: BLOCKED for {work_id}", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            for row in advisory_rows:
                print(row, file=sys.stderr)
    return 0 if ok else 1


def cmd_skip(args: argparse.Namespace) -> int:
    state = WorkflowEngine(_project(args)).skip(args.phase, reason=args.reason)
    print(f"Skipped {args.phase}; now at {state.phase}")
    return 0


def cmd_shelf(args: argparse.Namespace) -> int:
    project = _project(args)
    eng = WorkflowEngine(project)
    wid = eng.pointer.get()
    if wid and wid.upper().startswith("LOCAL-"):
        session = LocalSessionService(project).shelf(args.reason, session_id=wid)
        print(f"Shelved local session {session.id}: {args.reason}")
        return 0
    state = eng.shelf(reason=args.reason)
    if state is None:
        print("No active pointer to shelf", file=sys.stderr)
        return 1
    print(f"Shelved {state.work_id}: {args.reason}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    state = WorkflowEngine(_project(args)).sync(args.work_id)
    print(f"Synced {state.work_id} -> phase {state.phase}")
    return 0


def cmd_list_shelved(args: argparse.Namespace) -> int:
    rows = WorkflowEngine(_project(args)).list_shelved()
    if not rows:
        print("(no shelved work)")
        return 0
    for wid, phase, at, reason in rows:
        print(f"{wid}\t{phase}\t{at}\t{reason}")
    return 0


def cmd_pointer(args: argparse.Namespace) -> int:
    store = PointerStore(_project(args))
    try:
        if args.pointer_cmd == "get":
            print(store.get())
        elif args.pointer_cmd == "set":
            store.set(args.work_id)
            print(f"pointer set to: {args.work_id}")
        elif args.pointer_cmd == "reset":
            store.reset()
            print("pointer cleared")
        else:
            return 2
    except PointerError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


def cmd_quiet_status(args: argparse.Namespace) -> int:
    """Show quiet/product-test mode status and the hot session paths."""
    from ..quiet import is_quiet, quiet_resume_blurb

    project = _project(args)
    quiet = is_quiet(project, quiet_flag=bool(getattr(args, "quiet", False)))
    print(
        json.dumps(
            {
                "quiet": quiet,
                "blurb": quiet_resume_blurb(guide_live=bool(args.guide_live)),
                "hot_session_dir": str(project.hot_session_dir()),
                "current_session": str(project.current_session_path()),
            },
            indent=2,
        )
    )
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def cmd_shell(args: argparse.Namespace) -> int:
    """Bridge to the remaining shell session scripts (installed home first)."""
    project = _project(args)
    name = args.script
    candidates = []
    for base in (project.home / "scripts", project.root / "scripts"):
        candidates += [base / name, base / f"{name}.sh"]
    script = next((c for c in candidates if c.is_file()), None)
    if script is None:
        print(f"shell bridge: script not found: {name}", file=sys.stderr)
        return 1
    return subprocess.call([str(script), *args.script_args], cwd=project.root)
