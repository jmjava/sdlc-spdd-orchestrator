"""Ops console: Vue3 UI + Flask JSON API (install, SQLite, rollback, Guide)."""

from .app import create_app, run_installer

__all__ = ["create_app", "run_installer"]