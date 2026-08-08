import os

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-github-integration",
        action="store_true",
        default=False,
        help="Run live GitHub Issues integration tests",
    )
    parser.addoption(
        "--run-viewer-e2e",
        action="store_true",
        default=False,
        help="Run Playwright ADF viewer GUI tests (needs chromium)",
    )
    parser.addoption(
        "--run-console-e2e",
        action="store_true",
        default=False,
        help="Run Playwright ops console GUI tests (needs chromium)",
    )
    parser.addoption(
        "--run-guide-live",
        action="store_true",
        default=False,
        help="Run Vue3 console tests against live Guide+Neo4j (dual-repo)",
    )
    parser.addoption(
        "--run-adf-viewer-live",
        action="store_true",
        default=False,
        help="Run Vue3 ADF tab against a real viewer process",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    # Auto-enable when env asks for create/integration, otherwise require the flag
    # or SDLC_GITHUB_INTEGRATION=1 so default `pytest -q` stays offline-safe.
    gh_enabled = (
        config.getoption("--run-github-integration")
        or os.environ.get("SDLC_GITHUB_INTEGRATION", "0") == "1"
        or os.environ.get("SDLC_GITHUB_ISSUE_CREATE", "0") == "1"
    )
    e2e_enabled = (
        config.getoption("--run-viewer-e2e")
        or os.environ.get("SDLC_VIEWER_E2E", "0") == "1"
    )
    console_e2e_enabled = (
        config.getoption("--run-console-e2e")
        or os.environ.get("SDLC_CONSOLE_E2E", "0") == "1"
    )
    guide_live_enabled = (
        config.getoption("--run-guide-live")
        or os.environ.get("SDLC_GUIDE_STACK_LIVE", "0") == "1"
    )
    adf_viewer_live_enabled = (
        config.getoption("--run-adf-viewer-live")
        or os.environ.get("SDLC_ADF_VIEWER_LIVE", "0") == "1"
    )
    skip_gh = pytest.mark.skip(
        reason="need --run-github-integration or SDLC_GITHUB_INTEGRATION=1"
    )
    skip_e2e = pytest.mark.skip(
        reason="need --run-viewer-e2e or SDLC_VIEWER_E2E=1 (and playwright chromium)"
    )
    skip_console_e2e = pytest.mark.skip(
        reason="need --run-console-e2e or SDLC_CONSOLE_E2E=1 (and playwright chromium)"
    )
    skip_guide_live = pytest.mark.skip(
        reason="need --run-guide-live or SDLC_GUIDE_STACK_LIVE=1 (dual-repo Guide+Neo4j)"
    )
    skip_adf_viewer_live = pytest.mark.skip(
        reason="need --run-adf-viewer-live or SDLC_ADF_VIEWER_LIVE=1"
    )
    for item in items:
        if not gh_enabled and "github_integration" in item.keywords:
            item.add_marker(skip_gh)
        if not e2e_enabled and "viewer_e2e" in item.keywords:
            item.add_marker(skip_e2e)
        if not console_e2e_enabled and "console_e2e" in item.keywords:
            item.add_marker(skip_console_e2e)
        if not guide_live_enabled and "guide_live" in item.keywords:
            item.add_marker(skip_guide_live)
        if not adf_viewer_live_enabled and "adf_viewer_live" in item.keywords:
            item.add_marker(skip_adf_viewer_live)
