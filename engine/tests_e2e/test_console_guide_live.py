"""Ops console Guide tab probe against a live Guide stack."""

from __future__ import annotations

import os
from typing import Any

import pytest

pytest.importorskip("playwright")
pytest.importorskip("pytest_playwright")


def _goto_console(page, live_console: dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
    page.goto(live_console["base"] + "/")
    page.locator(".brand").wait_for()
    page.locator("#target").fill(str(live_console["target"]))


def _open_tab(page, tab: str) -> None:  # type: ignore[no-untyped-def]
    page.locator(f".tab[data-tab='{tab}']").click()
    page.locator(f"#pane-{tab}").wait_for(state="visible")


def test_guide_tab_live_probe(page, live_console, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    port = int(os.environ.get("GUIDE_PORT", "21337"))
    monkeypatch.setenv("GUIDE_BASE_URL", f"http://127.0.0.1:{port}")

    _goto_console(page, live_console)
    _open_tab(page, "guide")
    page.locator("#btn-guide-probe").click()
    page.wait_for_function(
        """() => {
          const t = document.getElementById('guide-probe').textContent || '';
          return t !== 'Status not loaded.' && !t.includes('Loading');
        }"""
    )
    probe = page.locator("#guide-probe").inner_text().lower()
    assert "tcp" in probe or "http" in probe or "open" in probe or "ok" in probe
