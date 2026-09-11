#!/usr/bin/env python3
"""Fail-closed contract for C-RETRIEVE live-graph evidence in required CI.

Required research P0 (`test-research-p0.yml`) runs hermetic TEST-003, including
MagicMock Guide *client* parity. That is not the Neo4j graph store.

The live Guide+Neo4j job lives in `test-guide-stack-experimental.yml` and is
path-filtered, so GitHub can skip it. A skipped live job is not graph-mode
proof. MagicMock must not fill that gap.

This module evaluates evidence. Required CI must fail the graph-mode claim
when the live graph job is the only evidence and it is skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_P0 = REPO_ROOT / ".github" / "workflows" / "test-research-p0.yml"
EXPERIMENTAL = REPO_ROOT / ".github" / "workflows" / "test-guide-stack-experimental.yml"

KIND_MOCK = "magicmock"
KIND_LIVE = "live-graph"

REQUIRED_CONTRACT = "tests.research.test_live_graph_required_ci"
REQUIRED_HERMETIC = "tests.research.test_cretrieve"


@dataclass(frozen=True)
class GraphEvidence:
    """One CI artifact that someone might count as graph-mode proof."""

    name: str
    kind: str
    skippable: bool = False
    conclusion: str | None = None


def graph_mode_required_ci_issues(evidence: list[GraphEvidence]) -> list[str]:
    """Return issues if *evidence* is not enough to prove live graph in required CI.

    A successful live-graph job is proof. MagicMock never is. A skipped or
    path-filtered-only live job is not proof — including when it is the only
    live-graph evidence.
    """
    live = [row for row in evidence if row.kind == KIND_LIVE]
    mocks = [row for row in evidence if row.kind == KIND_MOCK]
    proven = [row for row in live if row.conclusion == "success"]
    if proven:
        return []

    issues: list[str] = []
    if mocks:
        issues.append("MagicMock is not live graph proof")
    if not live:
        if not issues:
            issues.append("no live graph evidence")
        return issues

    if any(row.conclusion == "failure" for row in live) and not any(
        row.conclusion in (None, "skipped") or row.skippable for row in live
    ):
        issues.append("live graph job failed")
        return issues

    issues.append("live graph job is the only evidence and it is skipped")
    return issues


def pull_request_is_path_filtered(workflow_text: str) -> bool:
    """True when pull_request (not push) lists path filters — the job can skip."""
    lines = workflow_text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^([ \t]*)pull_request:\s*$", line)
        if match is None:
            continue
        indent = match.group(1)
        child: list[str] = []
        for later in lines[index + 1 :]:
            if later.strip() == "":
                child.append(later)
                continue
            later_indent = later[: len(later) - len(later.lstrip())]
            if len(later_indent) <= len(indent):
                break
            child.append(later)
        return any(re.match(r"^[ \t]+paths:\s*$", row) for row in child)
    return False


def issues_for_required_p0_workflow(text: str) -> list[str]:
    issues: list[str] = []
    if REQUIRED_CONTRACT not in text:
        issues.append(
            "required research P0 must run tests.research.test_live_graph_required_ci "
            "(MagicMock / skipped live graph is not proof)"
        )
    if REQUIRED_HERMETIC not in text:
        issues.append("required research P0 must still run tests.research.test_cretrieve")
    if "SDLC_GUIDE_STACK_LIVE" in text:
        issues.append(
            "required research P0 must not set SDLC_GUIDE_STACK_LIVE "
            "(the hermetic job is not the live graph)"
        )
    if "test-guide-stack-live.sh" in text:
        issues.append("required research P0 must not invoke test-guide-stack-live.sh")
    return issues


def issues_for_experimental_guide_workflow(text: str) -> list[str]:
    issues: list[str] = []
    if "test-guide-stack-live.sh" not in text:
        issues.append("experimental Guide workflow must invoke test-guide-stack-live.sh")
    if re.search(r"(?m)^[ \t]*continue-on-error:\s*true\s*$", text):
        issues.append("experimental live graph must not continue-on-error")
    return issues


def issues_for_repo_live_graph_ci(
    required_text: str,
    experimental_text: str,
) -> list[str]:
    """Inspect the two workflow files. Fail the hole: MagicMock + skippable live."""
    issues = issues_for_required_p0_workflow(required_text)
    issues.extend(issues_for_experimental_guide_workflow(experimental_text))
    skippable = pull_request_is_path_filtered(experimental_text)
    has_contract = REQUIRED_CONTRACT in required_text
    if skippable and not has_contract:
        issues.append(
            "path-filtered live graph job is skippable; required CI must run "
            "the live-graph contract so a skip is not treated as proof"
        )
    return issues


def issues_for_live_repo() -> list[str]:
    issues: list[str] = []
    if not REQUIRED_P0.is_file():
        return ["missing .github/workflows/test-research-p0.yml"]
    if not EXPERIMENTAL.is_file():
        return ["missing .github/workflows/test-guide-stack-experimental.yml"]
    issues.extend(
        issues_for_repo_live_graph_ci(
            REQUIRED_P0.read_text(encoding="utf-8"),
            EXPERIMENTAL.read_text(encoding="utf-8"),
        )
    )
    return issues
