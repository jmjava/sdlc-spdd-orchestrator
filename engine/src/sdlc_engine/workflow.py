"""Workflow state: phases, gates, shelf/resume, next/status."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import canvas as canvas_mod
from .phases import (
    GATE_LABELS,
    GATE_NAMES,
    PHASE_ORDER,
    gates_for_phase,
    next_phase,
    phase_index,
    recommended_command,
    valid_phase,
)
from .pointer import PointerStore
from .project import Project
from .quiet import is_quiet, quiet_resume_blurb


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class WorkflowState:
    work_id: str
    phase: str = "init"
    operation: str = ""
    active: bool = True
    shelved_at: str = ""
    shelved_reason: str = ""
    milestone: str = ""
    last_session_at: str = ""
    last_capture_at: str = ""
    gates: dict[str, str] = field(default_factory=dict)
    skips: dict[str, str] = field(default_factory=dict)

    def to_map(self) -> dict[str, str]:
        data = {
            "work_id": self.work_id,
            "phase": self.phase,
            "operation": self.operation,
            "active": "1" if self.active else "0",
            "shelved_at": self.shelved_at,
            "shelved_reason": self.shelved_reason,
            "milestone": self.milestone,
            "last_session_at": self.last_session_at,
            "last_capture_at": self.last_capture_at,
        }
        for gate in GATE_NAMES:
            data[f"gate_{gate}"] = self.gates.get(gate, "pending")
        for key, value in self.skips.items():
            data[f"skip_{key}"] = value
        return data


class WorkflowEngine:
    def __init__(self, project: Project | None = None) -> None:
        self.project = project or Project.resolve()
        self.project.ensure_runtime_dirs()
        self.pointer = PointerStore(self.project)

    def _state_path(self, work_id: str) -> Path:
        return self.project.workflows_dir / f"{work_id}.state"

    def _history_path(self, work_id: str) -> Path:
        return self.project.workflows_dir / f"{work_id}.history"

    def load_state(self, work_id: str) -> WorkflowState:
        path = self._state_path(work_id)
        state = WorkflowState(work_id=work_id)
        if not path.is_file():
            for gate in GATE_NAMES:
                state.gates[gate] = "pending"
            return state
        raw: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            raw[key] = value
        state.phase = raw.get("phase", "init")
        state.operation = raw.get("operation", "")
        state.active = raw.get("active", "1") != "0"
        state.shelved_at = raw.get("shelved_at", "")
        state.shelved_reason = raw.get("shelved_reason", "")
        state.milestone = raw.get("milestone", "")
        state.last_session_at = raw.get("last_session_at", "")
        state.last_capture_at = raw.get("last_capture_at", "")
        for gate in GATE_NAMES:
            state.gates[gate] = raw.get(f"gate_{gate}", "pending")
        for key, value in raw.items():
            if key.startswith("skip_"):
                state.skips[key[len("skip_") :]] = value
        return state

    def save_state(self, state: WorkflowState) -> None:
        path = self._state_path(state.work_id)
        tmp = path.with_suffix(path.suffix + ".tmp")
        lines = [f"{k}={v}" for k, v in state.to_map().items()]
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tmp.replace(path)

    def _log(self, work_id: str, action: str, detail: str = "") -> None:
        path = self._history_path(work_id)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"{_utc_now()}\t{action}\t{detail}\n")

    def ensure_state(self, work_id: str) -> WorkflowState:
        path = self._state_path(work_id)
        if not path.is_file():
            state = WorkflowState(work_id=work_id, phase="init")
            for gate in GATE_NAMES:
                state.gates[gate] = "pending"
            self.save_state(state)
            self._log(work_id, "create", f"work_id={work_id}")
            return state
        return self.load_state(work_id)

    def infer_phase_from_artifacts(self, work_id: str) -> str:
        root = self.project.root
        inferred = "init"
        if (root / "requirements" / "milestones" / f"{work_id}.md").is_file() or (
            self.project.feature_dir(work_id) / "requirement.md"
        ).is_file():
            inferred = "analysis"
        if self.project.analysis_path(work_id).is_file():
            inferred = "plan"
        canvas = self.project.canvas_path(work_id)
        if canvas.is_file():
            inferred = "architect"
            text = canvas.read_text(encoding="utf-8")
            if re.search(r"ready\s+for\s+coding", text, re.IGNORECASE):
                inferred = "code"
        progress = self.project.progress_log_path(work_id)
        legacy_progress = self.project.feature_dir(work_id) / "progress-log.md"
        evidence = ""
        if progress.is_file():
            evidence = Project.ledger_section_for_work(
                progress.read_text(encoding="utf-8"), work_id
            )
        elif legacy_progress.is_file():
            evidence = legacy_progress.read_text(encoding="utf-8")
        if evidence and re.search(
            r"(T\d{2}.*complete|implemented|merged)", evidence, re.IGNORECASE
        ):
            inferred = "code"
        if self.project.review_path(work_id).is_file():
            inferred = "review"
        lean_retro = root / "spdd" / "memory" / "entries" / "retro.md"
        if (self.project.feature_dir(work_id) / "retro.md").is_file() or (
            lean_retro.is_file()
            and bool(
                Project.ledger_section_for_work(
                    lean_retro.read_text(encoding="utf-8"), work_id
                )
            )
        ):
            inferred = "retro"
        if self.project.sync_path(work_id).is_file():
            inferred = "sync"
        session = self.project.current_session_path()
        if session.is_file():
            sess_text = session.read_text(encoding="utf-8")
            if work_id in sess_text:
                m = re.search(r"^- Phase:\s*(\S+)", sess_text, re.MULTILINE)
                if m and valid_phase(m.group(1)):
                    sess_phase = m.group(1)
                    if phase_index(sess_phase) > phase_index(inferred):
                        inferred = sess_phase
        return inferred

    def sync(self, work_id: str | None = None) -> WorkflowState:
        wid = work_id or self.pointer.get()
        if not wid:
            raise ValueError("sync requires a Work ID or active pointer")
        state = self.ensure_state(wid)
        state.phase = self.infer_phase_from_artifacts(wid)
        canvas = self.project.canvas_path(wid)
        if canvas.is_file():
            state.gates["canvas_exists"] = "passed"
            op, _title = canvas_mod.next_operation(canvas)
            state.operation = op
        if self.project.analysis_path(wid).is_file() or (
            self.project.feature_dir(wid) / "requirement.md"
        ).is_file() or self.project.milestone_path(wid).is_file():
            state.gates["requirement_documented"] = "passed"
        if self.project.review_path(wid).is_file():
            state.gates["review_completed"] = "passed"
            state.gates["safeguards_checked"] = "passed"
        if (self.project.feature_dir(wid) / "retro.md").is_file():
            state.gates["retro_completed"] = "passed"
        self.save_state(state)
        self._log(wid, "sync", f"phase={state.phase}")
        return state

    def resume(self, work_id: str, phase: str | None = None, force: bool = False) -> WorkflowState:
        current = self.pointer.get()
        if current and current != work_id:
            # Auto-shelf previous work
            prev = self.load_state(current)
            if prev.active:
                prev.active = False
                prev.shelved_at = _utc_now()
                prev.shelved_reason = f"auto-shelf for resume {work_id}"
                self.save_state(prev)
        self.pointer.set(work_id)
        state = self.ensure_state(work_id)
        state = self.sync(work_id)
        if phase:
            if not valid_phase(phase):
                raise ValueError(f"unknown phase: {phase}")
            state.phase = phase
        state.active = True
        state.shelved_at = ""
        state.shelved_reason = ""
        self.save_state(state)
        self._log(work_id, "resume", f"phase={state.phase}")
        return state

    def advance(self, to: str | None = None) -> WorkflowState:
        wid = self.pointer.get()
        if not wid:
            raise ValueError("advance requires an active pointer")
        state = self.ensure_state(wid)
        if to:
            if not valid_phase(to):
                raise ValueError(f"unknown phase: {to}")
            state.phase = to
        else:
            nxt = next_phase(state.phase)
            if not nxt:
                raise ValueError(f"already at final phase: {state.phase}")
            state.phase = nxt
        self.save_state(state)
        self._log(wid, "advance", f"phase={state.phase}")
        return state

    def skip(self, phase: str, reason: str = "manual skip") -> WorkflowState:
        wid = self.pointer.get()
        if not wid:
            raise ValueError("skip requires an active pointer")
        if not valid_phase(phase):
            raise ValueError(f"unknown phase: {phase}")
        state = self.ensure_state(wid)
        state.skips[phase] = reason
        nxt = next_phase(phase)
        if nxt:
            state.phase = nxt
        self.save_state(state)
        self._log(wid, "skip", f"phase={phase} reason={reason}")
        return state

    def shelf(self, reason: str = "manual shelf") -> WorkflowState | None:
        wid = self.pointer.get()
        if not wid:
            return None
        state = self.ensure_state(wid)
        state.active = False
        state.shelved_at = _utc_now()
        state.shelved_reason = reason
        self.save_state(state)
        self.pointer.reset()
        self._log(wid, "shelf", reason)
        return state

    def list_shelved(self) -> list[tuple[str, str, str, str]]:
        rows: list[tuple[str, str, str, str]] = []
        for path in sorted(self.project.workflows_dir.glob("*.state")):
            state = self.load_state(path.stem)
            if not state.active:
                rows.append((state.work_id, state.phase, state.shelved_at, state.shelved_reason))
        return rows

    def next_text(self) -> str:
        wid = self.pointer.get()
        from .local_sessions import LocalSessionService, is_local_id

        if wid and is_local_id(wid):
            return LocalSessionService(self.project).next_text_for_active(wid)
        if not wid:
            shelved = self.list_shelved()
            lines = [
                "== SDLC: what to do now ==",
                "No active Work ID pointer.",
                "",
                "Do now:",
                "  ./scripts/sdlc.sh list-work",
                "  ./scripts/sdlc.sh claim <WORK-ID>",
            ]
            if shelved:
                lines.append("  ./scripts/sdlc.sh list-shelved         # see parked work")
            lines.extend(LocalSessionService(self.project).next_hint_lines())
            return "\n".join(lines) + "\n"
        state = self.sync(wid)
        canvas = self.project.canvas_path(wid)
        op, title = canvas_mod.next_operation(canvas) if canvas.is_file() else ("", "")
        if op:
            state.operation = op
            self.save_state(state)
        if is_quiet(self.project):
            return (
                "== SDLC: what to do now (quiet) ==\n"
                f"Work ID: {wid}\n"
                f"Phase: {state.phase}\n\n"
                f"{quiet_resume_blurb()}\n"
            )
        cmd = recommended_command(state.phase, wid, state.operation)
        idx = PHASE_ORDER.index(state.phase) + 1 if state.phase in PHASE_ORDER else 0
        lines = [
            "== SDLC: what to do now ==",
            f"Work ID: {wid}",
            f"Phase: {state.phase} ({idx}/{len(PHASE_ORDER)})",
            "",
            "Do now (assistant):",
            f"  {cmd}",
            "",
            "Or run in terminal:",
            f"  ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id {wid} --phase {state.phase}",
            "",
            "Gates still open:",
        ]
        open_gates = gates_for_phase(state.phase)
        any_open = False
        for gate in open_gates:
            status = state.gates.get(gate, "pending")
            if status != "passed":
                any_open = True
                lines.append(f"  [ ] {GATE_LABELS.get(gate, gate)}")
        if not any_open:
            lines.append("  (none — ready to advance)")
        nxt = next_phase(state.phase)
        lines.extend(
            [
                "",
                "When this phase is done:",
                "  ./scripts/sdlc.sh advance",
            ]
        )
        if nxt:
            lines.append(f"  (moves to: {nxt})")
        if op and title:
            lines.extend(["", f"Next canvas operation: {op} — {title}"])
        return "\n".join(lines) + "\n"

    def status_json(self, work_id: str | None = None) -> str:
        wid = work_id or self.pointer.get()
        payload: dict = {
            "pointer": self.pointer.get(),
            "work_id": wid or None,
            "phases": list(PHASE_ORDER),
        }
        if wid:
            state = self.sync(wid)
            canvas = self.project.canvas_path(wid)
            op, title = canvas_mod.next_operation(canvas) if canvas.is_file() else ("", "")
            quiet = is_quiet(self.project)
            payload.update(
                {
                    "phase": state.phase,
                    "operation": op or state.operation,
                    "operation_title": title,
                    "active": state.active,
                    "quiet": quiet,
                    "recommended_command": (
                        quiet_resume_blurb()
                        if quiet
                        else recommended_command(
                            state.phase, wid, op or state.operation
                        )
                    ),
                    "gates": state.gates,
                }
            )
        return json.dumps(payload, indent=2)
