"""Ops console Guide tab probe against a live Guide stack (Vue3 UI)."""

from __future__ import annotations

import os
from typing import Any

import pytest

pytest.importorskip("playwright")
pytest.importorskip("pytest_playwright")


def _goto_console(page, live_console: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_console["base"] + "/")
    page.get_by_test_id("console-shell").wait_for()
    page.get_by_test_id("target-input").fill(str(live_console["target"]))


def test_guide_tab_live_probe(page, live_console, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    port = int(os.environ.get("GUIDE_PORT", "21337"))
    monkeypatch.setenv("GUIDE_BASE_URL", f"http://127.0.0.1:{port}")

    _goto_console(page, live_console)
    page.get_by_test_id("tab-guide").click()
    page.get_by_test_id("guide-panel").wait_for(state="visible")
    page.get_by_test_id("btn-guide-probe").click()
    page.wait_for_function(
        """() => {
          const t = document.querySelector('[data-testid="guide-probe"]')?.textContent || '';
          return t && t !== 'Status not loaded.' && !t.includes('Loading');
        }"""
    )
    probe = page.get_by_test_id("guide-probe").inner_text().lower()
    assert "tcp" in probe or "http" in probe or "open" in probe or "up" in probe or "down" in probe
