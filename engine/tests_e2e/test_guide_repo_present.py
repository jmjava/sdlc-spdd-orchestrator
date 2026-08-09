"""Live check that orch-guide clone is present (optional local path)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sdlc_engine.installer.guide_runtime import ensure_guide_repo


def _resolve_guide_home() -> Path:
    if os.environ.get("GUIDE_HOME"):
        return Path(os.environ["GUIDE_HOME"]).expanduser()
    for candidate in (
        Path.home() / "github/jmjava/orch-guide",
        Path(__file__).resolve().parents[2].parent / "orch-guide",
    ):
        if candidate.is_dir():
            return candidate
    pytest.fail("GUIDE_HOME not found — clone jmjava/orch-guide or set GUIDE_HOME")


def test_ensure_guide_repo_present() -> None:
    guide_home = _resolve_guide_home()
    result = ensure_guide_repo(
        {
            "guide_home": str(guide_home),
            "guide_git_url": "https://github.com/jmjava/orch-guide.git",
        },
        pull=False,
    )
    assert result["ok"] is True
    assert result["action"] == "present"
