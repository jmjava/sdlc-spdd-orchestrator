"""CHORE-003: committed dogfood ledger is non-empty and archive cannot wipe it.

These tests prove memory *exists* to retrieve (C-MEMORY precondition).
They do not prove that retrieved lessons reduce C-REWORK on a follow-on.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sdlc-spdd" / "docs" / "research"))

from check_dogfood_ledger import (  # noqa: E402
    LIVE_LEDGER,
    check_live,
    issues_for_dogfood_ledger,
)

POLICY = ROOT / "sdlc-spdd" / "docs" / "research" / "dogfood-ledger-policy.md"
SEED = ROOT / "tests" / "research" / "fixtures" / "chore003_dogfood_seed.json"
STORAGE = ROOT / "sdlc-spdd" / "docs" / "storage-v3.md"
RUNTIME = ROOT / "sdlc-spdd" / "docs" / "runtime-and-ledger.md"


class CheckerTests(unittest.TestCase):
    def test_empty_ledger_fails(self) -> None:
        issues = issues_for_dogfood_ledger("")
        self.assertTrue(issues)
        self.assertTrue(any("empty" in i for i in issues))

    def test_token_stub_fails(self) -> None:
        stub = "\n".join(
            json.dumps({"kind": kind, "title": kind, "body": kind})
            for kind in ("decision", "pitfall", "pattern")
        )
        issues = issues_for_dogfood_ledger(stub)
        self.assertTrue(issues, "kind-name-only bodies must fail")
        self.assertTrue(any("stub" in i for i in issues))

    def test_valid_three_kinds_pass(self) -> None:
        body = "x" * 48
        text = "\n".join(
            json.dumps(
                {
                    "kind": kind,
                    "title": f"{kind} title",
                    "body": f"{kind} {body}",
                }
            )
            for kind in ("decision", "pitfall", "pattern")
        )
        self.assertEqual(issues_for_dogfood_ledger(text), [])


class LiveLedgerTests(unittest.TestCase):
    def test_live_ledger_passes_checker(self) -> None:
        self.assertTrue(LIVE_LEDGER.is_file())
        issues = check_live()
        self.assertEqual(issues, [], msg=issues)

    def test_retrieve_pitfall_is_non_vacuous(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "engine" / "src")
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "sdlc_engine",
                "--root",
                str(ROOT),
                "context",
                "retrieve",
                "--kind",
                "pitfall",
                "--limit",
                "5",
                "--no-staged",
            ],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        hits = payload.get("ledger") or []
        self.assertGreater(len(hits), 0, payload)
        self.assertTrue(any(row.get("kind") == "pitfall" for row in hits))

    def test_policy_doc_states_leave_ledger(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        blob = text.lower()
        self.assertIn("must not", blob)
        self.assertIn("lessons.jsonl", blob)
        self.assertIn("truncate", blob)
        self.assertIn("chore-003-restore", blob)
        self.assertIn("does **not** prove", blob)

    def test_storage_docs_state_archive_leave_ledger(self) -> None:
        for path in (STORAGE, RUNTIME):
            blob = path.read_text(encoding="utf-8").lower()
            self.assertIn("lessons.jsonl", blob)
            self.assertIn("archive", blob)
            self.assertRegex(blob, r"never (truncat|delet|wip)")

    def test_seed_fixture_has_required_kinds(self) -> None:
        rows = json.loads(SEED.read_text(encoding="utf-8"))
        kinds = {row["kind"] for row in rows}
        self.assertTrue({"decision", "pitfall", "pattern"} <= kinds)
        self.assertTrue(all(row.get("source") == "chore-003-restore" for row in rows))


if __name__ == "__main__":
    unittest.main()
