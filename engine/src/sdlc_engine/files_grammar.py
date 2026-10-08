"""Files: line grammar for the review-time path check.

Real canvases mix repo paths with prose: a bare ``README``, a work-id
phrase such as ``DOC-001 spec``, and a bare basename such as
``check_p0_artifacts.py``. Those forms are part of the allow rule.
A changed path that matches none of them is still an extra path.

Not ``gate_check``. Does not change ``ENFORCED_GATES``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from pathlib import Path

_WORK_ID = re.compile(r"\b([A-Z]{2,}-\d+)\b")
_FILLER = frozenset({"possibly", "and", "or"})
_FILES_PREFIX = "- files:"
_CANVAS_GLOBS = ("sdlc-spdd/spdd/canvas/*.md", "spdd/canvas/*.md")


def parse_files_tokens(rest: str) -> tuple[str, ...]:
    """Path tokens plus prose outside backticks.

    Backtick spans are kept. Comma- and semicolon-separated words outside
    backticks are kept too, so ``README`` and ``DOC-001 spec`` are not
    dropped when the line also quotes a path. Filler words (``possibly``,
    ``and``, ``or``) are not tokens.
    """
    quoted = re.findall(r"`([^`]+)`", rest)
    prose = re.sub(r"`[^`]*`", " ", rest)
    raw: list[str] = list(quoted)
    for part in re.split(r"[,;]", prose):
        token = _prose_token(part)
        if token:
            raw.append(token)
    return _dedupe(raw)


def short_work_id(text: str) -> str:
    """``TEST-003`` from ``- Work ID: TEST-003-cretrieve-roundtrip``, or empty."""
    match = re.search(r"(?m)^- Work ID:\s*(\S+)", text)
    if not match:
        return ""
    hit = _WORK_ID.search(match.group(1))
    return hit.group(1) if hit else ""


def work_ids_in_token(token: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(match.group(1) for match in _WORK_ID.finditer(token)))


def token_allows_path(rel: str, token: str) -> bool:
    """True when ``rel`` is the path token, a bare name, or prose the token names."""
    token = token.strip().strip("`")
    if not token or not rel:
        return False
    if _glob_allows(rel, token):
        return True
    if _exact_or_child(rel, token):
        return True
    if _install_mirror(rel, token):
        return True
    if _bare_name_allows(rel, token):
        return True
    return _phrase_allows(rel, token)


def files_tokens_in_canvas(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(_FILES_PREFIX):
            found.extend(parse_files_tokens(stripped.split(":", 1)[1]))
    return _dedupe(found)


def tokens_from_related_canvases(
    related: Sequence[str],
    mentioned: Iterable[str],
) -> tuple[str, ...]:
    """Files tokens from canvases whose work id a prose phrase named.

    ``DOC-001 spec`` on the canvas under review pulls path and prose tokens
    from the DOC-001 canvas. One level only.
    """
    wanted = {item for item in mentioned if item}
    if not wanted:
        return ()
    found: list[str] = []
    for text in related:
        if short_work_id(text) not in wanted:
            continue
        found.extend(files_tokens_in_canvas(text))
    return _dedupe(found)


def scope_allow_tokens(
    canvas_text: str,
    operation_tokens: Iterable[Iterable[str]],
    related_canvases: Sequence[str] | None,
) -> tuple[str, ...]:
    """Own work id plus Files tokens from canvases a prose phrase named."""
    found: list[str] = []
    own = short_work_id(canvas_text)
    if own:
        found.append(own)
    mentioned: list[str] = []
    for tokens in operation_tokens:
        for token in tokens:
            mentioned.extend(work_ids_in_token(token))
    if related_canvases:
        found.extend(tokens_from_related_canvases(related_canvases, mentioned))
    return _dedupe(found)


def load_canvas_texts(root: Path) -> list[str]:
    """Canvas bodies next to ``root``, for prose work-id references."""
    texts: list[str] = []
    for pattern in _CANVAS_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                texts.append(path.read_text(encoding="utf-8"))
    return texts


def _prose_token(part: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", " ", part)
    words: list[str] = []
    for word in cleaned.split():
        bare = word.strip(".,'\"")
        if not bare or bare.lower() in _FILLER:
            continue
        words.append(bare)
    return " ".join(words).strip()


def _dedupe(raw: Iterable[str]) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        token = item.strip().strip("`").strip()
        if not token or token.lower() in _FILLER or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return tuple(out)


def _glob_allows(rel: str, token: str) -> bool:
    if not token.endswith("/**"):
        return False
    prefix = token[:-3].rstrip("/")
    return bool(prefix) and (rel == prefix or rel.startswith(prefix + "/"))


def _exact_or_child(rel: str, token: str) -> bool:
    prefix = token.rstrip("/")
    if not prefix or " " in prefix:
        return False
    return rel == prefix or rel.startswith(prefix + "/")


def _install_mirror(rel: str, token: str) -> bool:
    """``scripts/foo.sh`` also names ``sdlc-spdd/scripts/foo.sh``."""
    if "/" not in token or " " in token:
        return False
    return rel == "sdlc-spdd/" + token.rstrip("/")


def _bare_name_allows(rel: str, token: str) -> bool:
    if "/" in token or " " in token:
        return False
    base = rel.rsplit("/", 1)[-1]
    stem = base.split(".", 1)[0]
    if base == token or stem == token:
        return True
    return any(work_id in rel for work_id in work_ids_in_token(token))


def _phrase_allows(rel: str, token: str) -> bool:
    if " " not in token:
        return False
    if any(work_id in rel for work_id in work_ids_in_token(token)):
        return True
    return "milestone" in token.lower() and "milestone" in rel.lower()
