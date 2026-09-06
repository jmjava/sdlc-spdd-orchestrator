"""TEST-002 first slice: gold completeness + recorded method vs unstructured.

Numbers in SLICE-LOG.md are n=1 and protocol-incomplete. These tests prove
the artifacts exist and the scorer matches the log — they do not prove the
method works.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLICE = ROOT / "tests" / "eval" / "test-002-hello"
LOG = SLICE / "SLICE-LOG.md"
SCORER = SLICE / "score_slice.py"
GOLD_SRC = SLICE / "src" / "hello.py"
GOLD_TEST = SLICE / "tests" / "test_farewell.py"
METHOD_SRC = SLICE / "runs" / "method" / "src" / "hello.py"
UNST_SRC = SLICE / "runs" / "unstructured" / "src" / "hello.py"
CANVAS = SLICE / "canvas" / "TEST-002-hello.md"
REQUIREMENT = (
    ROOT
    / "sdlc-spdd"
    / "requirements"
    / "milestones"
    / "milestone-2"
    / "TEST-002-assistant-behavior-eval.md"
)
RESEARCH_README = ROOT / "docs" / "research" / "README.md"
MILESTONE2 = (
    ROOT
    / "sdlc-spdd"
    / "requirements"
    / "milestones"
    / "milestone-2"
    / "MILESTONE-2.md"
)
SEED_SRC = ROOT / "tests" / "live-consumer" / "seed" / "src" / "hello.py"
WORK_CANVAS = (
    ROOT / "sdlc-spdd" / "spdd" / "canvas" / "TEST-002-assistant-behavior-eval.md"
)
VALIDATE_CANVAS = ROOT / "scripts" / "validate-reasons-canvas.sh"


def _load_hello(path: Path):
    spec = importlib.util.spec_from_file_location("hello_mod", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _farewell_ok(path: Path) -> tuple[bool, str]:
    mod = _load_hello(path)
    fn = getattr(mod, "farewell", None)
    if fn is None:
        return False, "farewell missing"
    got = fn("ada")
    if got != "goodbye, ada":
        return False, f"got {got!r}"
    return True, ""


class GoldCompletenessTests(unittest.TestCase):
    def test_gold_source_runs_greet(self) -> None:
        mod = _load_hello(GOLD_SRC)
        self.assertEqual(mod.greet("x"), "hello, x")
        self.assertFalse(hasattr(mod, "farewell"))

    def test_gold_observable_fails_before_implementation(self) -> None:
        ok, reason = _farewell_ok(GOLD_SRC)
        self.assertFalse(ok, reason)
        self.assertTrue(GOLD_TEST.is_file())
        self.assertIn("goodbye, ada", GOLD_TEST.read_text(encoding="utf-8"))

    def test_canvas_has_t01_files_and_nongoals(self) -> None:
        text = CANVAS.read_text(encoding="utf-8")
        self.assertIn("### T01", text)
        self.assertIn("- Files: `src/hello.py`", text)
        self.assertIn("shout", text.lower())
        self.assertIn("Non-Goals", text)

    def test_spring_boot_still_has_no_java(self) -> None:
        example = ROOT / "examples" / "spring-boot-order-api"
        java = list(example.rglob("*.java")) if example.is_dir() else []
        self.assertEqual(java, [], "slice must keep using hello gold while Spring Boot has no Java")


class RecordedRunTests(unittest.TestCase):
    def test_method_run_passes_farewell_without_shout(self) -> None:
        ok, reason = _farewell_ok(METHOD_SRC)
        self.assertTrue(ok, reason)
        mod = _load_hello(METHOD_SRC)
        self.assertFalse(hasattr(mod, "shout"))

    def test_unstructured_run_has_extra_shout(self) -> None:
        ok, reason = _farewell_ok(UNST_SRC)
        self.assertTrue(ok, reason)
        mod = _load_hello(UNST_SRC)
        self.assertTrue(hasattr(mod, "shout"))

    def test_scorer_method_zero_unmapped_unstructured_positive(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCORER), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["n"], 1)
        self.assertEqual(payload["protocol"], "incomplete")
        self.assertIs(payload["c_port_reported"], False)
        by_name = {row["condition"]: row for row in payload["runs"]}
        self.assertEqual(by_name["method"]["n_unmapped_hunks"], 0)
        self.assertEqual(by_name["method"]["scope_deviation_rate"], 0.0)
        self.assertGreater(by_name["unstructured"]["n_unmapped_hunks"], 0)
        self.assertGreater(by_name["unstructured"]["scope_deviation_rate"], 0.0)
        self.assertIn("shout", by_name["unstructured"]["unmapped_defs"])
        self.assertAlmostEqual(by_name["unstructured"]["scope_deviation_rate"], 1 / 3)


class SliceLogTests(unittest.TestCase):
    def test_log_states_limitations_beside_numbers(self) -> None:
        text = LOG.read_text(encoding="utf-8")
        blob = text.lower()
        self.assertIn("incomplete", blob)
        self.assertRegex(text, r"\bn\s*(=|</td>)\s*\*?\*?1")
        self.assertIn("cursor grok", blob)
        self.assertIn("c-port", blob)
        self.assertIn("not reported", blob)
        self.assertIn("1/3", text)
        self.assertIsNone(re.search(r"statistically\s+significant", text, re.I))
        self.assertIsNone(re.search(r"\bwe showed\b", text, re.I))
        self.assertIn("do not treat", blob)

    def test_log_does_not_claim_fixes_drift(self) -> None:
        text = LOG.read_text(encoding="utf-8")
        self.assertIn("does not claim", text.lower())
        self.assertIn("fixes drift", text.lower())

    def test_research_readme_points_at_slice(self) -> None:
        readme = RESEARCH_README.read_text(encoding="utf-8")
        self.assertIn("TEST-002", readme)
        self.assertIn("test-002-hello", readme)
        self.assertIn("protocol incomplete", readme.lower())

    def test_requirement_status_complete_but_protocol_incomplete(self) -> None:
        req = REQUIREMENT.read_text(encoding="utf-8")
        self.assertIn("**Status:** Complete (protocol incomplete; n=1)", req)
        self.assertIn("[x] Gold task has source + canvas + expected operations", req)
        self.assertIn("[x] A recorded run", req)
        self.assertIn("[x] Limitations of n and model version", req)

    def test_milestone_linked_work_is_complete(self) -> None:
        text = MILESTONE2.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r"TEST-002-assistant-behavior-eval.*Complete \(protocol incomplete; n=1\)",
        )
        self.assertIn("[x] TEST-002-assistant-behavior-eval", text)

    def test_live_consumer_seed_was_not_mutated(self) -> None:
        self.assertTrue(SEED_SRC.is_file())
        seed = SEED_SRC.read_text(encoding="utf-8")
        self.assertIn("def greet", seed)
        self.assertNotIn("def farewell", seed)
        self.assertNotIn("def shout", seed)

    def test_work_and_gold_canvases_validate(self) -> None:
        self.assertTrue(VALIDATE_CANVAS.is_file())
        for path in (WORK_CANVAS, CANVAS):
            proc = subprocess.run(
                ["bash", str(VALIDATE_CANVAS), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)


if __name__ == "__main__":
    unittest.main()
