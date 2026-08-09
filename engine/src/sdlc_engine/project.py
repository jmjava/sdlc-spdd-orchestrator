"""Project root/home resolution and artifact path helpers.

Layout (storage v3): everything the framework owns lives under a single
folder — ``<repo>/sdlc-spdd/`` — called the *home*:

    <root>/                repo root (git toplevel)
      sdlc-spdd/           home (framework folder)
        requirements/      milestones + requirements
        spdd/              canvas/ analysis/ reviews/ sync/ memory/
        harness/ skills/
        scripts/           installed workflow CLI
        .sdlc/             gitignored runtime (sessions, staged, sqlite)

Legacy sprawled layouts (framework dirs at repo root) resolve ``home == root``
so every path helper keeps working until ``upgrade --consolidate`` runs.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

HOME_DIR_NAME = "sdlc-spdd"


@dataclass(frozen=True)
class Project:
    root: Path

    @classmethod
    def resolve(cls, root: str | Path | None = None) -> "Project":
        if root is not None:
            path = Path(root).expanduser().resolve()
            return cls(path)
        env = os.environ.get("SDLC_ROOT")
        if env:
            return cls(Path(env).expanduser().resolve())
        try:
            out = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if out:
                return cls(Path(out).resolve())
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return cls(Path.cwd().resolve())

    @property
    def home(self) -> Path:
        """Single framework folder; falls back to root for legacy layouts."""
        env = os.environ.get("SDLC_HOME")
        if env:
            return Path(env).expanduser().resolve()
        candidate = self.root / HOME_DIR_NAME
        if candidate.is_dir():
            return candidate
        return self.root

    @property
    def is_single_folder(self) -> bool:
        return self.home != self.root

    @property
    def sdlc_dir(self) -> Path:
        return self.home / ".sdlc"

    @property
    def workflows_dir(self) -> Path:
        return self.sdlc_dir / "workflows"

    @property
    def pointer_path(self) -> Path:
        return self.sdlc_dir / "pointer"

    # --- storage v3: single lesson ledger + registry ---

    @property
    def memory_dir(self) -> Path:
        return self.home / "spdd" / "memory"

    @property
    def ledger_path(self) -> Path:
        """Committed system of record: one JSONL record per accepted lesson."""
        return self.memory_dir / "lessons.jsonl"

    @property
    def staged_ledger_path(self) -> Path:
        """Gitignored stage: captures land here until accept promotes them."""
        return self.sdlc_dir / "staged" / "lessons.jsonl"

    @property
    def registry_jsonl_path(self) -> Path:
        """Committed claim/release event log (replaces the legacy TSV registry)."""
        return self.memory_dir / "registry.jsonl"

    # Kept name for compatibility with existing callers; now points at the
    # lean JSONL registry.
    @property
    def registry_path(self) -> Path:
        return self.registry_jsonl_path

    # --- contracts ---

    @property
    def spdd_dir(self) -> Path:
        return self.home / "spdd"

    @property
    def requirements_dir(self) -> Path:
        return self.home / "requirements"

    @property
    def roadmap_path(self) -> Path:
        return self.home / "ROADMAP.md"

    @property
    def session_notes_dir(self) -> Path:
        return self.home / "session-notes"

    @property
    def harness_dir(self) -> Path:
        """Install-time harness. Single-folder: <home>/harness; legacy: agent-context/harness."""
        direct = self.home / "harness"
        if direct.is_dir():
            return direct
        return self.home / "agent-context" / "harness"

    @property
    def skills_dir(self) -> Path:
        """Phase and #SkillName playbooks under harness/skills/."""
        return self.harness_dir / "skills"

    def canvas_path(self, work_id: str) -> Path:
        return self.spdd_dir / "canvas" / f"{work_id}.md"

    def analysis_path(self, work_id: str) -> Path:
        return self.spdd_dir / "analysis" / f"{work_id}-analysis.md"

    def review_path(self, work_id: str) -> Path:
        return self.spdd_dir / "reviews" / f"{work_id}-review.md"

    def sync_path(self, work_id: str) -> Path:
        return self.spdd_dir / "sync" / f"{work_id}-sync.md"

    def milestone_path(self, work_id: str) -> Path:
        return self.requirements_dir / "milestones" / f"{work_id}.md"

    def progress_log_path(self, work_id: str) -> Path:
        """Lean progress ledger (not feature mirror).

        ``work_id`` is accepted for call-site symmetry; the ledger is shared.
        Use :meth:`ledger_section_for_work` when reading evidence for one work item.
        """
        return self.home / "spdd" / "memory" / "entries" / "progress.md"

    @staticmethod
    def ledger_section_for_work(text: str, work_id: str) -> str:
        """Extract shared-ledger slices that belong to one Work ID.

        Supports ``## <WORK-ID>`` sections and capture-style
        ``### <ts> - <WORK-ID> - <phase>`` blocks.
        """
        import re

        wid = (work_id or "").strip()
        if not text or not wid:
            return ""
        parts: list[str] = []
        for block in re.split(r"(?m)^##\s+", text):
            if not block.strip():
                continue
            first = block.splitlines()[0].strip()
            if (
                first == wid
                or first.startswith(f"{wid} ")
                or first.startswith(f"{wid}—")
                or first.startswith(f"{wid} -")
            ):
                parts.append(block)
        pattern = re.compile(
            rf"(?m)^###[^\n]*\b{re.escape(wid)}\b[^\n]*\n(?:.*?)(?=^###\s+|^##\s+|\Z)",
            re.DOTALL,
        )
        for match in pattern.finditer(text):
            parts.append(match.group(0))
        return "\n".join(parts)

    # --- runtime (never committed) ---

    def hot_session_dir(self) -> Path:
        return self.sdlc_dir / "sessions"

    def current_session_path(self) -> Path:
        return self.hot_session_dir() / "current-session.md"

    def ensure_runtime_dirs(self) -> None:
        self.sdlc_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.hot_session_dir().mkdir(parents=True, exist_ok=True)
        self.staged_ledger_path.parent.mkdir(parents=True, exist_ok=True)
        (self.home / "spdd" / "memory" / "entries").mkdir(parents=True, exist_ok=True)
