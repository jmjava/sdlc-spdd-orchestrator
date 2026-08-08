"""Project root resolution and artifact path helpers."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


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
    def sdlc_dir(self) -> Path:
        return self.root / ".sdlc"

    @property
    def workflows_dir(self) -> Path:
        return self.sdlc_dir / "workflows"

    @property
    def pointer_path(self) -> Path:
        return self.sdlc_dir / "pointer"

    @property
    def registry_path(self) -> Path:
        return self.root / "agent-context" / "work-registry.tsv"

    def canvas_path(self, work_id: str) -> Path:
        """Canonical REASONS canvas (stay-set). Legacy feature mirror is fallback only."""
        primary = self.root / "spdd" / "canvas" / f"{work_id}.md"
        if primary.is_file():
            return primary
        alt = self.root / "agent-context" / "features" / work_id / "reasons-canvas.md"
        return alt if alt.is_file() else primary

    def feature_dir(self, work_id: str) -> Path:
        """Legacy mirror dir (deprecated #86). Prefer stay-set paths."""
        return self.root / "agent-context" / "features" / work_id

    def analysis_path(self, work_id: str) -> Path:
        return self.root / "spdd" / "analysis" / f"{work_id}-analysis.md"

    def review_path(self, work_id: str) -> Path:
        return self.root / "spdd" / "reviews" / f"{work_id}-review.md"

    def sync_path(self, work_id: str) -> Path:
        return self.root / "spdd" / "sync" / f"{work_id}-sync.md"

    def milestone_path(self, work_id: str) -> Path:
        return self.root / "requirements" / "milestones" / f"{work_id}.md"

    def hot_session_dir(self) -> Path:
        """Hot session briefs live under gitignored `.sdlc/sessions/` (#85)."""
        return self.sdlc_dir / "sessions"

    def legacy_session_dir(self) -> Path:
        return self.root / "agent-context" / "sessions"

    def current_session_path(self) -> Path:
        """Prefer hot `.sdlc/sessions/current-session.md`, else legacy fallback."""
        hot = self.hot_session_dir() / "current-session.md"
        if hot.is_file():
            return hot
        legacy = self.legacy_session_dir() / "current-session.md"
        return legacy if legacy.is_file() else hot

    def progress_log_path(self, work_id: str) -> Path:
        """Lean progress ledger (not feature mirror).

        ``work_id`` is accepted for call-site symmetry; the ledger is shared.
        Use :meth:`ledger_section_for_work` when reading evidence for one work item.
        """
        return self.root / "spdd" / "memory" / "entries" / "progress.md"

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

    def ensure_runtime_dirs(self) -> None:
        self.sdlc_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.hot_session_dir().mkdir(parents=True, exist_ok=True)
        (self.root / "agent-context").mkdir(parents=True, exist_ok=True)
        (self.root / "spdd" / "memory" / "entries").mkdir(parents=True, exist_ok=True)
