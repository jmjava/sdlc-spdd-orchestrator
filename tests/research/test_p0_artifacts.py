"""Tests for Milestone 2 P0 research-artifact checks.

These tests are meant to fail on token-only stubs. If a fixture that only
mentions the words "Fowler" / "RQ1" starts passing, the checker has been
weakened and should be rejected.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sdlc-spdd" / "docs" / "research"))

from check_p0_artifacts import (  # noqa: E402
    check_doc001,
    check_doc002,
    check_doc003,
    check_test001,
    issues_for_constructs_spec,
    issues_for_evaluation_protocol,
    issues_for_related_work,
    issues_for_threats_replication,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GREP_TOKENS_DOC002 = (
    "Novelty",
    "Fowler",
    "SDLC Agents",
    "Spec Kit",
    "SWE-agent",
    "C-DRIFT",
)
GREP_TOKENS_TEST001 = (
    "RQ1",
    "RQ2",
    "RQ3",
    "RQ4",
    "RQ5",
    "unstructured",
    "gold task",
    "Stop rule",
)
GREP_TOKENS_DOC003 = (
    "C-DRIFT",
    "C-COMPLY",
    "C-CONTEXT",
    "C-MEMORY",
    "C-PORT",
    "TEST-001",
    "live-consumer",
    "nondeterminism",
)


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class RelatedWorkCheckerTests(unittest.TestCase):
    def test_valid_fixture_has_no_issues(self) -> None:
        issues = issues_for_related_work(_read("related_work_valid.md"))
        self.assertEqual(issues, [], msg=issues)

    def test_token_stub_fails_even_if_old_grep_would_pass(self) -> None:
        text = _read("related_work_token_stub.md")
        self.assertTrue(
            all(token in text for token in GREP_TOKENS_DOC002),
            "fixture must still contain the old grep tokens",
        )
        issues = issues_for_related_work(text)
        self.assertTrue(issues, "token stub must fail the structured checker")
        self.assertTrue(
            any("matrix" in issue for issue in issues),
            f"expected a matrix failure, got {issues}",
        )

    def test_missing_iso_row_fails(self) -> None:
        issues = issues_for_related_work(_read("related_work_missing_row.md"))
        self.assertTrue(
            any("ISO 12207" in issue for issue in issues),
            f"expected missing ISO comparator, got {issues}",
        )

    def test_missing_construct_columns_fails(self) -> None:
        issues = issues_for_related_work(_read("related_work_missing_columns.md"))
        joined = " ".join(issues)
        self.assertIn("c-drift", joined)
        self.assertIn("c-comply", joined)
        self.assertIn("c-context", joined)
        self.assertIn("evidence", joined)

    def test_embabel_upstream_framing_fails(self) -> None:
        issues = issues_for_related_work(_read("related_work_embabel_upstream.md"))
        self.assertTrue(
            any("Embabel" in issue for issue in issues),
            f"expected Embabel upstream failure, got {issues}",
        )

    def test_evidence_as_finding_fails(self) -> None:
        issues = issues_for_related_work(_read("related_work_evidence_finding.md"))
        self.assertTrue(
            any("evidence" in issue for issue in issues),
            f"expected evidence-as-finding failure, got {issues}",
        )


class ConstructsSpecCheckerTests(unittest.TestCase):
    def test_live_doc001_spec_parses(self) -> None:
        spec = ROOT / "sdlc-spdd" / "docs" / "research" / "research-questions-and-constructs.md"
        self.assertTrue(spec.is_file(), "DOC-001 spec missing from checkout")
        issues = issues_for_constructs_spec(spec.read_text(encoding="utf-8"))
        self.assertEqual(issues, [], msg=issues)

    def test_empty_spec_fails(self) -> None:
        issues = issues_for_constructs_spec("")
        self.assertTrue(issues)

    def test_rq_name_drop_without_construct_fields_fails(self) -> None:
        stub = """# Spec
## RQ1 — Drift
## RQ2
## RQ3
## RQ4
## RQ5
### C-DRIFT
hello
### C-COMPLY
hello
### C-CONTEXT
hello
### C-MEMORY
hello
### C-PORT
hello
## Claims allowed today
fixes drift
"""
        issues = issues_for_constructs_spec(stub)
        self.assertTrue(any("C-DRIFT missing field" in i for i in issues), issues)


class EvaluationProtocolCheckerTests(unittest.TestCase):
    def test_valid_fixture_has_no_issues(self) -> None:
        issues = issues_for_evaluation_protocol(_read("eval_protocol_valid.md"))
        self.assertEqual(issues, [], msg=issues)

    def test_token_stub_fails_even_if_old_grep_would_pass(self) -> None:
        text = _read("eval_protocol_token_stub.md")
        self.assertTrue(all(token.lower() in text.lower() for token in GREP_TOKENS_TEST001))
        issues = issues_for_evaluation_protocol(text)
        self.assertTrue(issues, "token stub must fail the structured checker")
        self.assertTrue(
            any("procedure" in issue or "baseline" in issue for issue in issues),
            f"expected procedure/baseline failure, got {issues}",
        )


    def test_rq_name_drop_without_procedure_headings_fails(self) -> None:
        issues = issues_for_evaluation_protocol(_read("eval_protocol_rq_namedrop.md"))
        self.assertTrue(
            any("procedure" in issue for issue in issues),
            f"expected missing procedure headings, got {issues}",
        )


class ThreatsReplicationCheckerTests(unittest.TestCase):
    def test_valid_fixture_has_no_issues(self) -> None:
        issues = issues_for_threats_replication(_read("threats_valid.md"))
        self.assertEqual(issues, [], msg=issues)

    def test_token_stub_fails_even_if_old_grep_would_pass(self) -> None:
        text = _read("threats_token_stub.md")
        self.assertTrue(
            all(token.lower() in text.lower() for token in GREP_TOKENS_DOC003),
            "fixture must still contain the old grep tokens",
        )
        issues = issues_for_threats_replication(text)
        self.assertTrue(issues, "token stub must fail the structured checker")
        self.assertTrue(
            any("heading" in issue or "table" in issue for issue in issues),
            f"expected heading/table failure, got {issues}",
        )

    def test_missing_c_port_in_construct_section_fails(self) -> None:
        issues = issues_for_threats_replication(_read("threats_missing_construct.md"))
        self.assertTrue(
            any("C-PORT" in issue for issue in issues),
            f"expected missing C-PORT in construct section, got {issues}",
        )


class LiveArtifactTests(unittest.TestCase):
    def test_doc001_live_files_pass(self) -> None:
        issues = check_doc001()
        self.assertEqual(issues, [], msg=issues)

    def test_doc002_live_files_pass(self) -> None:
        issues = check_doc002()
        self.assertEqual(issues, [], msg=issues)

    def test_test001_live_files_pass(self) -> None:
        issues = check_test001()
        self.assertEqual(issues, [], msg=issues)

    def test_doc003_live_files_pass(self) -> None:
        issues = check_doc003()
        self.assertEqual(issues, [], msg=issues)


if __name__ == "__main__":
    unittest.main()
