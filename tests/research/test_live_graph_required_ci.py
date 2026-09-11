"""Leftover #17: required CI must not treat MagicMock / skipped live graph as proof.

Proving tests: required CI fails the graph-mode claim when the live graph
job is the only evidence and it is skipped. MagicMock Guide parity in
test_cretrieve.py is the client contract, not the Neo4j store.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sdlc-spdd" / "docs" / "research"))

from check_live_graph_ci import (  # noqa: E402
    KIND_LIVE,
    KIND_MOCK,
    REQUIRED_CONTRACT,
    REQUIRED_HERMETIC,
    REQUIRED_P0,
    EXPERIMENTAL,
    GraphEvidence,
    graph_mode_required_ci_issues,
    issues_for_live_repo,
    issues_for_repo_live_graph_ci,
    pull_request_is_path_filtered,
)


class GraphModeEvidenceTests(unittest.TestCase):
    def test_skipped_live_graph_as_sole_evidence_fails_required_ci(self) -> None:
        issues = graph_mode_required_ci_issues(
            [
                GraphEvidence(
                    name="guide-neo4j-live",
                    kind=KIND_LIVE,
                    skippable=True,
                    conclusion="skipped",
                )
            ]
        )
        self.assertTrue(issues, "skipped live graph must fail required-CI proof")
        self.assertTrue(
            any("skipped" in issue for issue in issues),
            f"expected skipped-live failure, got {issues}",
        )

    def test_magicmock_is_not_live_graph_evidence(self) -> None:
        issues = graph_mode_required_ci_issues(
            [
                GraphEvidence(
                    name="test_mocked_guide_parity_finds_ledger_id",
                    kind=KIND_MOCK,
                    conclusion="success",
                )
            ]
        )
        self.assertTrue(issues, "MagicMock must not count as live graph proof")
        self.assertTrue(
            any("MagicMock" in issue for issue in issues),
            f"expected MagicMock failure, got {issues}",
        )

    def test_magicmock_plus_skipped_live_still_fails(self) -> None:
        """The hole on origin/main: hermetic MagicMock green + experimental skip."""
        issues = graph_mode_required_ci_issues(
            [
                GraphEvidence(
                    name="test_cretrieve.GuideRoundTripTests",
                    kind=KIND_MOCK,
                    conclusion="success",
                ),
                GraphEvidence(
                    name="guide-neo4j-live",
                    kind=KIND_LIVE,
                    skippable=True,
                    conclusion="skipped",
                ),
            ]
        )
        self.assertTrue(issues)
        self.assertTrue(any("MagicMock" in issue for issue in issues), issues)
        self.assertTrue(any("skipped" in issue for issue in issues), issues)

    def test_successful_live_graph_is_proof(self) -> None:
        issues = graph_mode_required_ci_issues(
            [
                GraphEvidence(
                    name="guide-neo4j-live",
                    kind=KIND_LIVE,
                    skippable=False,
                    conclusion="success",
                )
            ]
        )
        self.assertEqual(issues, [], msg=issues)

    def test_path_filtered_unrun_live_job_is_not_proof(self) -> None:
        issues = graph_mode_required_ci_issues(
            [
                GraphEvidence(
                    name="guide-neo4j-live",
                    kind=KIND_LIVE,
                    skippable=True,
                    conclusion=None,
                )
            ]
        )
        self.assertTrue(issues)
        self.assertTrue(any("skipped" in issue for issue in issues), issues)

    def test_failed_live_graph_is_not_proof(self) -> None:
        issues = graph_mode_required_ci_issues(
            [
                GraphEvidence(
                    name="guide-neo4j-live",
                    kind=KIND_LIVE,
                    skippable=False,
                    conclusion="failure",
                )
            ]
        )
        self.assertTrue(issues)
        self.assertTrue(any("failed" in issue for issue in issues), issues)


class WorkflowContractTests(unittest.TestCase):
    def test_required_p0_runs_live_graph_contract(self) -> None:
        text = REQUIRED_P0.read_text(encoding="utf-8")
        self.assertIn(REQUIRED_CONTRACT, text)
        self.assertIn(REQUIRED_HERMETIC, text)
        self.assertNotIn("SDLC_GUIDE_STACK_LIVE", text)
        self.assertNotIn("test-guide-stack-live.sh", text)

    def test_experimental_workflow_is_path_filtered_skippable(self) -> None:
        text = EXPERIMENTAL.read_text(encoding="utf-8")
        self.assertTrue(
            pull_request_is_path_filtered(text),
            "experimental live job must stay path-filtered (skippable)",
        )
        self.assertIn("test-guide-stack-live.sh", text)
        self.assertNotRegex(text, r"(?m)^[ \t]*continue-on-error:\s*true\s*$")

    def test_repo_workflows_pass_the_contract(self) -> None:
        issues = issues_for_live_repo()
        self.assertEqual(issues, [], msg=issues)

    def test_required_workflow_without_contract_is_the_hole(self) -> None:
        required = (
            "name: Test Research P0 Artifacts\n"
            "jobs:\n"
            "  test-research-p0:\n"
            "    steps:\n"
            "      - run: python3 -m unittest tests.research.test_cretrieve -v\n"
        )
        experimental = (
            "on:\n"
            "  pull_request:\n"
            "    paths:\n"
            "      - engine/tests_e2e/**\n"
            "jobs:\n"
            "  guide-neo4j-live:\n"
            "    steps:\n"
            "      - run: ./tests/test-guide-stack-live.sh\n"
        )
        issues = issues_for_repo_live_graph_ci(required, experimental)
        self.assertTrue(issues, "MagicMock-only required P0 must fail the contract")
        self.assertTrue(
            any("test_live_graph_required_ci" in issue or "skippable" in issue for issue in issues),
            f"expected missing-contract / skippable failure, got {issues}",
        )
        self.assertTrue(
            pull_request_is_path_filtered(experimental),
            "fixture experimental workflow must parse as path-filtered",
        )

    def test_path_filter_helper_ignores_push_only_paths(self) -> None:
        text = (
            "on:\n"
            "  pull_request:\n"
            "  push:\n"
            "    paths:\n"
            "      - engine/**\n"
        )
        self.assertFalse(pull_request_is_path_filtered(text))


if __name__ == "__main__":
    unittest.main()
