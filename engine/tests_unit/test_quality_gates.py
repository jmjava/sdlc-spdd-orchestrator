"""Smell gates bound to Suite 1 so unused imports and new CCN fail without a new workflow."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


RUFF_SELECT = "F,E9"  # mirrors [tool.ruff.lint] select in engine/pyproject.toml


def test_ruff_rule_set_matches_pyproject() -> None:
    text = (REPO / "engine" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'select = ["F", "E9"]' in text, "CI/test rule set drifted from pyproject"


def test_ruff_pyflakes_clean() -> None:
    """CHORE-004: full pyflakes, not only unused imports — F821 shipped a NameError once."""
    ruff = shutil.which("ruff") or sys.executable
    cmd = [ruff, "check", "--select", RUFF_SELECT, "engine/src", "scripts"] if ruff != sys.executable else [
        sys.executable, "-m", "ruff", "check", "--select", RUFF_SELECT, "engine/src", "scripts"
    ]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_complexity_gate_proves_new_ccn_fails() -> None:
    script = REPO / "scripts" / "test-check-complexity.sh"
    proc = subprocess.run(["bash", str(script)], cwd=REPO, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "test-check-complexity: PASS" in proc.stdout
