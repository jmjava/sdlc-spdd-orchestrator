"""Retired: Flask HTML ops console.

The default console UI is Vue3. Use::

    pytest -q engine/tests_e2e/test_vue3_console_playwright.py
"""

from __future__ import annotations

import pytest

pytest.skip(
    "Flask HTML console retired; use engine/tests_e2e/test_vue3_console_playwright.py",
    allow_module_level=True,
)
