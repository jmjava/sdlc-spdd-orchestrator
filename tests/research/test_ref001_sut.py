"""REF-001/REF-003: Python gate_check is the only engine.

A headings-only canvas with a 'ready for coding' substring is the historical
confound (shell grep pass / Python FEAT-014 fail). These tests prove the SUT
rejects it through both entry points (sdlc-engine and the sdlc.sh dispatcher),
and that the removed SDLC_ENGINE / SDLC_GATE_ENGINE switches are refused.
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
    home = root / "sdlc-spdd"
    req = home / "requirements" / "milestones"
    req.mkdir(parents=True, exist_ok=True)
    (req / f"{WID}.md").write_text(f"# Requirement {WID}\n\nNeed a gated change.\n", encoding="utf-8")
    analysis = home / "spdd" / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / f"{WID}-analysis.md").write_text(f"# Analysis {WID}\n", encoding="utf-8")
    canvas = home / "spdd" / "canvas"
    canvas.mkdir(parents=True, exist_ok=True)
    (canvas / f"{WID}.md").write_text(WEAK_CANVAS, encoding="utf-8")
    (home / ".sdlc" / "sessions").mkdir(parents=True, exist_ok=True)


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "engine" / "src")
    env.pop("SDLC_GATE_ENGINE", None)
    env.pop("SDLC_ENGINE", None)
    return env


class SutDocTests(unittest.TestCase):
    def test_sut_doc_names_python_gate_check(self) -> None:
        text = SUT_DOC.read_text(encoding="utf-8")
        blob = text.lower()
        self.assertIn("workflowengine.gate_check", blob)
        self.assertIn("one engine", blob)
        self.assertIn("removed", blob)
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

    def test_sdlc_sh_gate_rejects_headings_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            proc = subprocess.run(
                ["bash", str(SDLC_SH), "--target", str(root), "gate", "--phase", "code", "--work-id", WID],
                cwd=str(ROOT),
                env=_env(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            blob = (proc.stdout + proc.stderr).lower()
            self.assertTrue(
                "ready" in blob or "requirement" in blob or "files" in blob or "operation" in blob,
                proc.stdout + proc.stderr,
            )

    def test_removed_engine_switches_are_refused(self) -> None:
        for var in ("SDLC_ENGINE", "SDLC_GATE_ENGINE"):
            env = _env()
            env[var] = "shell"
            proc = subprocess.run(
                ["bash", str(SDLC_SH), "version"],
                cwd=str(ROOT),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 2, (var, proc.stdout, proc.stderr))
            self.assertIn("removed", proc.stderr.lower())

    def test_sdlc_sh_is_a_thin_python_dispatcher(self) -> None:
        text = SDLC_SH.read_text(encoding="utf-8")
        self.assertNotIn("SDLC_ENGINE:-auto", text)
        self.assertIn("-m sdlc_engine", text)
        proc = subprocess.run(
            ["bash", str(SDLC_SH), "version"],
            cwd=str(ROOT),
            env=_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.strip().startswith("2.0.0a"), proc.stdout)

    def test_python_parser_owns_session_verbs(self) -> None:
        # REF-003: capture/start/complete/accept are engine verbs, not shell verbs.
        from sdlc_engine.cli_parser import build_parser

        parser = build_parser()
        args, extra = parser.parse_known_args(["capture", "--summary", "ok"])
        self.assertEqual(args.command, "capture")
        self.assertEqual(extra, ["--summary", "ok"])
        for verb in ("start", "complete", "accept"):
            self.assertEqual(parser.parse_args([verb]).command, verb)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "engine" / "src"))
    unittest.main()
