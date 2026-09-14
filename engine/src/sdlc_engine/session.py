"""Session-facing workflow operations (one engine, REF-003).

These used to live in the bash workflow twin (``sdlc-workflow.sh`` /
``sdlc-team-registry.sh``). The remaining shell session scripts
(``start-agent-session.sh``, ``capture-session-memory.sh``) call back into the
engine through ``sdlc-engine session ...`` for anything that touches workflow
state, the registry, or the pointer, so there is exactly one implementation.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import canvas as canvas_mod
from .links import collect_links
from .phases import GATE_LABELS, PHASE_ORDER, gates_for_phase, recommended_command
from .project import Project
from .registry import TeamRegistry
from .timeutil import utc_now as _utc_now
from .workflow import WorkflowEngine


def jira_status(project: Project, work_id: str) -> str:
    """``<KEY>`` when a real key is known (claim note or requirement), ``draft``
    when a ``## Jira`` section exists without a key, else ``missing``."""
    wid = (work_id or "").strip()
    if not wid:
        return "missing"
    row = next((r for r in TeamRegistry(project).rows() if r.work_id == wid), None)
    links = collect_links(project, wid, row)
    if links.has_real_jira:
        return links.jira_key
    return "draft" if links.jira_draft else "missing"


def jira_ask_prompt(project: Project, work_id: str) -> str:
    """Agent-facing instruction when the tracker key is unset; empty otherwise."""
    wid = (work_id or "").strip()
    if not wid or os.environ.get("SDLC_SESSION_ASK_JIRA", "1") != "1":
        return ""
    status = jira_status(project, wid)
    if status == "missing":
        return (
            f"Tracker link: Jira key is missing for {wid}. Ask the user for the issue key "
            "(or confirm none applies) before coding or claiming tracker progress. Then run "
            f"`./scripts/sdlc.sh claim {wid} --jira KEY` (or set `- Key:` under `## Jira` on the "
            "requirement and re-claim). Do not invent a key."
        )
    if status == "draft":
        return (
            f"Tracker link: Jira draft exists for {wid} but `- Key:` is unset. Ask the user for the "
            "issue key (or confirm none applies) before coding or claiming tracker progress. Then run "
            f"`./scripts/sdlc.sh claim {wid} --jira KEY` (or set `- Key:` under `## Jira` and "
            "re-claim). Do not invent a key."
        )
    return ""


@dataclass
class SessionService:
    project: Project
    workflow: WorkflowEngine | None = None

    def __post_init__(self) -> None:
        self.workflow = self.workflow or WorkflowEngine(self.project)

    # --- state touches used by the session scripts ---

    def touch_session(self, work_id: str, phase: str, milestone: str = "") -> None:
        wf = self.workflow
        state = wf.ensure_state(work_id)
        if phase in PHASE_ORDER:
            state.phase = phase
        state.active = True
        state.shelved_at = ""
        state.shelved_reason = ""
        state.last_session_at = _utc_now()
        if milestone:
            state.milestone = milestone
        wf.save_state(state)
        wf._log(work_id, "session", f"phase={state.phase}")

    def record_capture(self, work_id: str, phase: str = "resume") -> None:
        wf = self.workflow
        state = wf.ensure_state(work_id)
        state.last_capture_at = _utc_now()
        if phase and phase != "resume" and phase in PHASE_ORDER:
            state.phase = phase
        wf.save_state(state)
        wf._log(work_id, "capture", f"phase={phase}")

    # --- recommendation (architecture-first) ---

    def recommend(self, work_id: str, phase: str, operation: str = "") -> str:
        """Assistant command for the phase; never /sdlc-spdd-code when the canvas blocks coding."""
        from .quiet import is_quiet, quiet_resume_blurb

        if is_quiet(self.project):
            return quiet_resume_blurb()
        canvas = self.project.canvas_path(work_id)
        text = canvas.read_text(encoding="utf-8") if canvas.is_file() else ""
        if not operation and text:
            op, _ = canvas_mod.next_operation(canvas)
            operation = op
        if phase == "code" and text and not canvas_mod.canvas_allows_coding(text):
            raw = canvas_mod.normalize_readiness(canvas_mod.extract_readiness_raw(text)) or "absent"
            return f"/sdlc-spdd-architect @spdd/canvas/{work_id}.md  # readiness={raw} — not Ready For Coding"
        return recommended_command(phase, work_id, operation)

    # --- brief ---

    def _canvas_facts(self, wid: str, state: Any) -> tuple[str, str, str, str]:
        """(next op id, op title, effective operation, readiness label) from the canvas."""
        canvas = self.project.canvas_path(wid)
        if not canvas.is_file():
            return "", "", state.operation, "absent"
        op, title = canvas_mod.next_operation(canvas)
        raw = canvas_mod.extract_readiness_raw(canvas.read_text(encoding="utf-8"))
        readiness = canvas_mod.normalize_readiness(raw) or raw or "absent"
        return op, title, op or state.operation, readiness

    @staticmethod
    def _pending_gates(state: Any) -> list[str]:
        return [
            GATE_LABELS.get(g, g)
            for g in gates_for_phase(state.phase)
            if state.gates.get(g, "pending") != "passed"
        ]

    def _brief_rows(self, wid: str, state: Any) -> list[str]:
        op, title, operation, readiness = self._canvas_facts(wid, state)
        idx = PHASE_ORDER.index(state.phase) + 1 if state.phase in PHASE_ORDER else 0
        next_op = f"{op} — {title}" if op and title else (operation or "none")
        status = "active" if state.active else "shelved"
        return [
            "| Field | Value |",
            "|-------|-------|",
            f"| Work ID | {wid} |",
            f"| Workflow status | {status} |",
            f"| Phase | {state.phase} ({idx}/{len(PHASE_ORDER)}) |",
            f"| Readiness | {readiness} |",
            f"| Jira | {jira_status(self.project, wid)} |",
            f"| Next operation | {next_op} |",
            f"| Assistant command | {self.recommend(wid, state.phase, operation)} |",
            "| After this phase | `./scripts/sdlc.sh advance` |",
            '| Capture (guarded) | `./scripts/sdlc.sh capture --summary "<summary>"` |',
            "| Orient / status | `./scripts/sdlc.sh next` or `/sdlc-spdd-whereami` |",
            "",
        ]

    def brief_markdown(self, work_id: str = "") -> str:
        wid = (work_id or self.workflow.pointer.get() or "").strip()
        if not wid:
            return "No active Work ID. Run `./scripts/sdlc.sh resume <WORK-ID>`."
        state = self.workflow.sync(wid)
        lines = self._brief_rows(wid, state)
        pending = self._pending_gates(state)
        if pending:
            lines.append("Pending gates:")
            lines.extend(f"- {p}" for p in pending)
        ask = jira_ask_prompt(self.project, wid)
        if ask:
            lines.extend(["", "Tracker follow-up:", f"- {ask}"])
        return "\n".join(lines) + "\n"

    # --- shell session scripts (REF-010 will pythonize these) ---

    def _script(self, name: str) -> Path:
        for cand in (
            self.project.home / "scripts" / name,
            self.project.root / "scripts" / name,
        ):
            if cand.is_file() and os.access(cand, os.X_OK):
                return cand
        raise FileNotFoundError(f"{name} not found under {self.project.home / 'scripts'} or {self.project.root / 'scripts'}")

    def _run(self, argv: list[str]) -> int:
        env = dict(os.environ)
        env["SDLC_ROOT"] = str(self.project.root)
        return subprocess.call(argv, env=env)

    def start(self, work_id: str = "", phase: str = "") -> int:
        wid = (work_id or self.workflow.pointer.get() or "").strip()
        if not wid:
            print("start: no active pointer — run: ./scripts/sdlc.sh resume <WORK-ID>")
            return 2
        state = self.workflow.sync(wid)
        script = self._script("start-agent-session.sh")
        return self._run([
            str(script), "--target", str(self.project.root),
            "--work-id", wid, "--phase", phase or state.phase,
        ])

    def _resolve_capture_target(self, work_id: str) -> tuple[str, int]:
        """(Work ID, rc): rc 3 on pointer mismatch, 2 when no pointer, 0 when resolved."""
        pointer = self.workflow.pointer.get()
        if work_id and pointer and pointer != work_id:
            print(f"capture: --work-id '{work_id}' does not match pointer '{pointer}'", file=sys.stderr)
            print(f"Run: ./scripts/sdlc.sh resume {work_id}", file=sys.stderr)
            return "", 3
        wid = (work_id or pointer or "").strip()
        if not wid:
            print("capture: no active pointer — run: ./scripts/sdlc.sh resume <WORK-ID>")
            return "", 2
        return wid, 0

    def capture(self, args: list[str], *, work_id: str = "", phase: str = "") -> int:
        wid, rc = self._resolve_capture_target(work_id)
        if rc:
            return rc
        phase = phase or self.workflow.ensure_state(wid).phase or "resume"
        script = self._script("capture-session-memory.sh")
        argv = [str(script), "--target", str(self.project.root), "--work-id", wid, "--phase", phase, *args]
        return self.workflow.pointer.run_against(wid, argv)

    def complete(self, args: list[str]) -> int:
        """Guarded ``capture --complete``; refuses without a full verify receipt."""
        have = {"--verify-command": False, "--verify-exit": False, "--verify-result": False}
        has_phase = False
        for tok in args:
            if tok in have:
                have[tok] = True
            if tok == "--phase":
                has_phase = True
        if not all(have.values()):
            print(
                "complete: verify receipt required (command, exit, pass/fail). Refuse complete without it.",
                file=sys.stderr,
            )
            print("Pass --verify-command, --verify-exit, and --verify-result=pass.", file=sys.stderr)
            return 1
        extra = list(args)
        if not has_phase:
            extra += ["--phase", "code"]
        return self.capture(["--complete", *extra])
