"""Fitness function: engine source has no embabel/guide push URL or PR target.

Read from the engine, not from historical docs:

- ``installer/guide_runtime.py`` clones and fast-forward pulls
  ``DEFAULT_GIT_URL`` (``https://github.com/jmjava/orch-guide.git``). It does
  not push.
- ``issues.py`` and ``sunset.py`` pass ``gh --repo`` from ``SDLC_GITHUB_REPO``,
  ``GH_REPO``, or the origin remote. They do not hardcode a repo slug.
- ``installer/guide.py`` mentions ``embabel/guide`` only as a local checkout
  name. That mention is not a push URL or a PR target.
"""

from __future__ import annotations

import re
from pathlib import Path

_PUSH_URL = re.compile(
    r"(?:(?:git\+)?https://github\.com/embabel/guide(?:\.git)?\b"
    r"|git@github\.com:embabel/guide(?:\.git)?\b"
    r"|ssh://(?:git@)?github\.com/embabel/guide(?:\.git)?\b)",
    re.IGNORECASE,
)
_PR_TARGET = re.compile(
    r"(?:--repo(?:=|\s+)[\"']?(?:https://github\.com/)?embabel/guide\b"
    r"|github\.com/embabel/guide/(?:compare|pull)\b"
    r"|[\"']embabel/guide(?:\.git)?[\"'])",
    re.IGNORECASE,
)

ENGINE_SRC = Path(__file__).resolve().parents[1] / "src"


def _hits(text: str, label: str) -> list[str]:
    found: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if _PUSH_URL.search(line) or _PR_TARGET.search(line):
            found.append(f"{label}:{lineno}")
    return found


def test_engine_source_has_no_embabel_guide_push_url_or_pr_target() -> None:
    findings: list[str] = []
    for path in sorted(ENGINE_SRC.rglob("*.py")):
        findings.extend(_hits(path.read_text(encoding="utf-8"), str(path)))
    assert findings == []
    assert _hits('git push https://github.com/embabel/guide.git\n', "push-url")
    assert _hits('cmd.extend(["--repo", "embabel/guide"])\n', "pr-target")
