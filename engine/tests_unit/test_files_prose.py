"""Files: prose grammar. Extra paths still force Changes Requested.

The proving replay runs the I2 check against the merged #245–#263 diffs.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from sdlc_engine.canvas import check_operation_diff_scope
from sdlc_engine.review_scope import review_result_for_scope

_ROOT = Path(__file__).resolve().parents[2]

# Pull requests that exist in 245–263. The canvas is the work the PR reviewed.
_HISTORICAL = (
    (245, "5a7500442116a7246e11e5fd4e782b8310b6e10b", "TEST-003-cretrieve-roundtrip"),
    (246, "eebe7eba970f83708e46e3e00ebc0bd2d43f5ca4", "TEST-003-cretrieve-roundtrip"),
    (247, "9f14dcde691e4ef2fc1fbde19cfb88ee2d725d3e", "DOC-003-replication-package"),
    (248, "92d3e514c45a11fc3f31b6d3bf6ccf590c2b832f", "DOC-001-research-questions-and-constructs"),
    (249, "52b44f2f92c58cb627dddf3b756ffce7700f78fe", "DOC-001-research-questions-and-constructs"),
    (252, "bd5e6d773b5d1363c38383802cb1f734a41626df", "TEST-003-cretrieve-roundtrip"),
    (256, "ccd2290566613f72e939129dd4f6c8541d7f8986", "TEST-003-cretrieve-roundtrip"),
    (259, "e716100f0afcd92487abf9985a5184f93b6ad8e9", "TEST-003-cretrieve-roundtrip"),
    (263, "53a2bf71d047f31d227cfe313391d7e7e5a006a9", "TEST-003-cretrieve-roundtrip"),
)

_PROSE_CANVAS = """## O - Operations
### T01 - Docs
- Status: Complete
- Files: `src/app.py`, DOC-001 spec, README, CHANGELOG, `check_p0_artifacts.py`
"""


def test_prose_files_allow_readme_work_id_and_basename() -> None:
    result = check_operation_diff_scope(
        _PROSE_CANVAS,
        [
            "src/app.py",
            "README.md",
            "docs/research/README.md",
            "CHANGELOG.md",
            "sdlc-spdd/docs/research/check_p0_artifacts.py",
            "sdlc-spdd/spdd/canvas/DOC-001-research-questions-and-constructs.md",
        ],
        selected_ops=["T01"],
    )
    assert result.ok, result.extra_paths


def test_work_id_phrase_uses_that_canvas_files() -> None:
    related = """- Work ID: DOC-001-research-questions-and-constructs
## Operations
### T01 - Spec
- Status: Complete
- Files: `sdlc-spdd/docs/research/research-questions-and-constructs.md`
"""
    result = check_operation_diff_scope(
        _PROSE_CANVAS,
        ["sdlc-spdd/docs/research/research-questions-and-constructs.md"],
        selected_ops=["T01"],
        related_canvases=[related],
    )
    assert result.ok, result.extra_paths


def test_prose_does_not_hide_an_extra_path() -> None:
    result = check_operation_diff_scope(
        _PROSE_CANVAS,
        ["src/app.py", "README.md", "src/evil.py"],
        selected_ops=["T01"],
    )
    assert not result.ok
    assert result.extra_paths == ("src/evil.py",)
    assert review_result_for_scope(result, "Approved") == "Changes Requested"
    assert review_result_for_scope(result, "Approved With Notes") == "Changes Requested"


def test_backticks_do_not_drop_prose_or_keep_possibly() -> None:
    from sdlc_engine.files_grammar import parse_files_tokens

    tokens = parse_files_tokens(
        "`README.md`, possibly `sdlc-spdd/docs/spdd-compliance.md`, CHANGELOG, milestone pointer"
    )
    assert "README.md" in tokens
    assert "sdlc-spdd/docs/spdd-compliance.md" in tokens
    assert "CHANGELOG" in tokens
    assert "milestone pointer" in tokens
    assert "possibly" not in tokens


def test_install_mirror_of_a_files_path() -> None:
    canvas = """## Operations
### T01 - Script
- Status: In Progress
- Files: `scripts/verify-agent-command-effects.sh`
"""
    result = check_operation_diff_scope(
        canvas,
        ["sdlc-spdd/scripts/verify-agent-command-effects.sh"],
        selected_ops=["T01"],
    )
    assert result.ok, result.extra_paths


# Paths the old backtick-only grammar marked extra even though a Files: line
# named them as README / CHANGELOG, a work id, a bare basename, or that
# work's own canvas. The I2 replay must not report these.
_PROSE_COVERED = {
    245: (
        "CHANGELOG.md",
        "docs/research/README.md",
        "sdlc-spdd/spdd/canvas/TEST-003-cretrieve-roundtrip.md",
        "sdlc-spdd/docs/research/research-questions-and-constructs.md",
        "sdlc-spdd/requirements/milestones/milestone-2/MILESTONE-2.md",
    ),
    246: (
        "sdlc-spdd/spdd/canvas/DOC-001-research-questions-and-constructs.md",
        "sdlc-spdd/docs/research/check_p0_artifacts.py",
        "sdlc-spdd/docs/research/research-questions-and-constructs.md",
    ),
    249: (
        ".github/workflows/test-guide-stack-experimental.yml",
        "sdlc-spdd/docs/research/check_p0_artifacts.py",
        "sdlc-spdd/docs/research/prove-academic-review.sh",
        "CHANGELOG.md",
    ),
    252: ("CHANGELOG.md", "sdlc-spdd/spdd/canvas/TEST-003-cretrieve-roundtrip.md"),
    259: ("sdlc-spdd/scripts/verify-agent-command-effects.sh",),
}


def test_i2_against_historical_diffs_245_through_263() -> None:
    """Run the I2 check on each #245–#263 diff and the canvas Files: lines.

    Every T## is passed as ``--ops`` so this tests the Files grammar, not the
    last-T default from leftover #8. Prose-covered paths must not be extra.
    A path the canvas never named can still be extra.
    """
    misses: list[str] = []
    for number, sha, work in _HISTORICAL:
        canvas_rel = f"sdlc-spdd/spdd/canvas/{work}.md"
        text = _git("show", f"{sha}:{canvas_rel}")
        changed = _changed(sha)
        related = _related_canvases(sha, canvas_rel)
        ops = re.findall(r"^### (T\d+)\b", text, re.MULTILINE)
        result = check_operation_diff_scope(
            text,
            changed,
            selected_ops=ops,
            related_canvases=related,
        )
        for path in _PROSE_COVERED.get(number, ()):
            if path not in changed:
                misses.append(f"#{number} fixture path not in diff: {path}")
            elif path in result.extra_paths:
                misses.append(f"#{number} prose path still extra: {path}")
    assert not misses, "\n".join(misses)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(_ROOT), *args], text=True)


def _changed(sha: str) -> list[str]:
    parent = _git("rev-parse", f"{sha}^").strip()
    names = _git("diff", "--name-only", f"{parent}...{sha}")
    return [line for line in names.splitlines() if line]


def _related_canvases(sha: str, skip: str) -> list[str]:
    listing = _git("ls-tree", "-r", "--name-only", sha, "sdlc-spdd/spdd/canvas")
    texts: list[str] = []
    for path in listing.splitlines():
        if not path or path == skip:
            continue
        texts.append(_git("show", f"{sha}:{path}"))
    return texts
