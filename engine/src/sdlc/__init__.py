"""Compatibility alias so ``python -m sdlc`` is the same as ``python -m sdlc_engine``."""

from sdlc_engine.cli import main

__all__ = ["main"]
