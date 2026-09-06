"""REF-001: Python gate_check is the SUT; shell CLI delegates when importable.

A headings-only canvas with a 'ready for coding' substring is the historical
confound (shell grep pass / Python FEAT-014 fail). These tests prove the SUT
path rejects it, and that SDLC_ENGINE=shell still delegates when Python can
be imported. SDLC_GATE_ENGINE=shell is the labeled non-SUT fallback.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "src"))
SUT_DOC = ROOT / "sdlc-spdd" / "docs" / "research" / "engine-sut.md"
TESTING = ROOT / "TESTING.md"
ROADMAP = ROOT / "sdlc-spdd" / "ROADMAP.md"
SDLC_SH = ROOT / "scripts" / "sdlc.sh"
WORKFLOW = ROOT / "templates" / "agent-context" / "sdlc-workflow.sh"
WID = "FEAT-REF001-headings"


WEAK_CANVAS = """# REASONS Canvas: FEAT-REF001-headings

## Metadata

- Work ID: FEAT-REF001-headings

## R - Requirements

## O - Operations

Mentions ready for coding in prose so the old shell grep would pass.

## Final Status

- Status: In Progress
"""


def _seed(root: Path) -> None:
    req = root / "requirements" / "milestones"
    req.mkdir(parents=True, exist_ok=True)
    (req / f"{WID}.md").write_text(f"# Requirement {WID}\n\nNeed a gated change.\n", encoding="utf-8")
    analysis = root / "spdd" / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / f"{WID}-analysis.md").write_text(f"# Analysis {WID}\n", encoding="utf-8")
    canvas = root / "spdd" / "canvas"
    canvas.mkdir(parents=True, exist_ok=True)
    (canvas / f"{WID}.md").write_text(WEAK_CANVAS, encoding="utf-8")
    (root / ".sdlc" / "sessions").mkdir(parents=True, exist_ok=True)


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "engine" / "src")
    env.pop("SDLC_GATE_ENGINE", None)
    return env


class SutDocTests(unittest.TestCase):
    def test_sut_doc_names_python_gate_check(self) -> None:
        text = SUT_DOC.read_text(encoding="utf-8")
        blob = text.lower()
        self.assertIn("workflowengine.gate_check", blob)
        self.assertIn("sdlc_engine=auto", blob)
        self.assertIn("sdlc_gate_engine=shell", blob)
        self.assertIn("not the sut", blob)

    def test_testing_and_roadmap_name_sut(self) -> None:
        testing = TESTING.read_text(encoding="utf-8").lower()
        roadmap = ROADMAP.read_text(encoding="utf-8").lower()
        self.assertIn("gate_check", testing)
        self.assertIn("system under test", testing)
        self.assertIn("ref-001", roadmap)
        self.assertIn("complete (p2)", roadmap)


class WeakCanvasGateTests(unittest.TestCase):
    def test_python_gate_rejects_headings_only(self) -> None:
        from sdlc_engine.project import Project
        from sdlc_engine.workflow import WorkflowEngine

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            ok, failures = WorkflowEngine(Project(root)).gate_check(WID, "code")
            self.assertFalse(ok, failures)
            joined = " ".join(failures).lower()
            self.assertTrue(
                "ready" in joined or "requirement" in joined or "files" in joined or "operation" in joined,
                failures,
            )

    def test_shell_engine_delegates_to_python_when_importable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            env = _env()
            env["SDLC_ENGINE"] = "shell"
            env["SDLC_ROOT"] = str(root)
            proc = subprocess.run(
                ["bash", str(WORKFLOW), "gate", "--phase", "code", "--work-id", WID],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            blob = (proc.stdout + proc.stderr).lower()
            self.assertTrue(
                "empty requirements" in blob or "files:" in blob or "no t##" in blob,
                proc.stdout + proc.stderr,
            )

    def test_gate_engine_shell_fallback_is_not_sut(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            env = _env()
            env["SDLC_GATE_ENGINE"] = "shell"
            env["SDLC_ROOT"] = str(root)
            proc = subprocess.run(
                ["bash", str(WORKFLOW), "gate", "--phase", "code", "--work-id", WID],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_sdlc_sh_default_auto_uses_python(self) -> None:
        self.assertIn("SDLC_ENGINE:-auto", SDLC_SH.read_text(encoding="utf-8"))
        env = _env()
        env.pop("SDLC_ENGINE", None)
        proc = subprocess.run(
            ["bash", str(SDLC_SH), "version"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.strip().startswith("2.0.0a"), proc.stdout)

    def test_python_parser_has_no_top_level_capture(self) -> None:
        # sdlc.sh capture stages lessons; Python only has `local capture`.
        # Default auto must not route the shell verb into argparse.
        from io import StringIO
        from contextlib import redirect_stderr

        from sdlc_engine.cli_parser import build_parser

        parser = build_parser()
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["capture", "--summary", "ok"])
        text = SDLC_SH.read_text(encoding="utf-8")
        self.assertIn("capture|start|accept", text)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "engine" / "src"))
    unittest.main()
