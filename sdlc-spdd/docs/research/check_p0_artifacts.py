#!/usr/bin/env python3
"""Machine checks for Milestone 2 P0 research artifacts.

These checks parse structure (markdown tables, required columns, construct
fields). A document that merely mentions the strings "Fowler" or "RQ1" is
not enough. Exit 0 only when the named Work ID's live files satisfy the
checks.

Usage:
    python3 check_p0_artifacts.py --work-id DOC-001|DOC-002|TEST-001|DOC-003
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RESEARCH = REPO_ROOT / "sdlc-spdd" / "docs" / "research"
CANVAS_DIR = REPO_ROOT / "sdlc-spdd" / "spdd" / "canvas"
REVIEW_DIR = REPO_ROOT / "sdlc-spdd" / "spdd" / "reviews"
VALIDATE_CANVAS = REPO_ROOT / "scripts" / "validate-reasons-canvas.sh"

FORBIDDEN_UPSTREAM = re.compile(
    r"(pr\s+(to|against|on)\s+embabel|upstream\s+(pr|to|into)\s+embabel|"
    r"merge\s+.*embabel/guide|contribute\s+to\s+embabel)",
    re.IGNORECASE,
)

CAUSAL_FINDING = re.compile(
    r"\b(we\s+(showed|demonstrated|proved|found)\b|statistically\s+significant|"
    r"p\s*<\s*0\.|fixes\s+drift)\b",
    re.IGNORECASE,
)

CONSTRUCT_FIELDS = (
    "Definition",
    "Measure",
    "Instrument today",
    "Target instrument",
    "Proxy weakness",
)

DOC001_CONSTRUCTS = (
    "C-DRIFT",
    "C-COMPLY",
    "C-CONTEXT",
    "C-MEMORY",
    "C-PORT",
)

# Each required comparator is present if `any` matches a System cell, or if
# every token in `all_across_rows` appears in some System cell.
REQUIRED_COMPARATORS: tuple[dict[str, object], ...] = (
    {"id": "Spec Kit", "any": ["spec kit"]},
    {"id": "OpenSpec", "any": ["openspec"]},
    {"id": "OpenSPDD", "any": ["openspdd"]},
    {"id": "BMAD", "any": ["bmad"]},
    {"id": "Fowler SPDD", "any": ["fowler spdd"]},
    {"id": "SDLC Agents", "any": ["sdlc agents"]},
    {"id": "Aider", "any": ["aider"]},
    {"id": "SWE-agent", "any": ["swe-agent", "sweagent"]},
    {"id": "OpenHands", "any": ["openhands", "open hands"]},
    {
        "id": "AutoGen/CrewAI",
        "any": ["autogen/crewai", "autogen / crewai"],
        "all_across_rows": ["autogen", "crewai"],
    },
    {
        "id": "Cursor/Copilot/Claude native memory",
        "any": [
            "cursor/copilot/claude",
            "native memory",
            "assistant native memory",
        ],
        "all_across_rows": ["cursor", "copilot", "claude"],
    },
    {
        "id": "gIBIS/QOC",
        "any": ["gibis/qoc", "gibis / qoc"],
        "all_across_rows": ["gibis", "qoc"],
    },
    {
        "id": "ISO 12207/SPEM/CMMI",
        "any": ["iso 12207/spem/cmmi", "iso/iec 12207/spem/cmmi"],
        "all_across_rows": ["12207", "spem", "cmmi"],
    },
)

REQUIRED_MATRIX_HEADER_TOKENS = (
    "system",
    "c-drift",
    "c-comply",
    "c-context",
    "evidence",
    "delta",
)

TEST001_BASELINES = (
    "unstructured chat",
    "canvas-only",
    "lifecycle-only",
    "full sdlc-spdd",
)

THREAT_CATEGORIES = (
    "construct",
    "internal",
    "external",
    "conclusion",
    "reliability",
)

REPLICATION_GOLD = "tests/live-consumer/seed/src/hello.py"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_separator(row: list[str]) -> bool:
    if not row:
        return False
    return all(re.fullmatch(r":?-{3,}:?", re.sub(r"\s+", "", c)) for c in row if c)


def parse_markdown_tables(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        if "|" in line:
            row = split_row(line)
            if is_separator(row):
                continue
            if row:
                current.append(row)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def heading_blocks(text: str) -> dict[str, str]:
    """Map normalized heading text -> body until next heading of same or higher level."""
    blocks: dict[str, str] = {}
    matches = list(re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE))
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks[_norm(match.group(2))] = text[start:end]
    return blocks


def find_matrix_table(text: str) -> list[list[str]] | None:
    """Prefer the table immediately under a Claim × system matrix heading."""
    match = re.search(
        r"^#{1,6}\s+.*claim\s*.\s*system\s+matrix.*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    if match:
        rest = text[match.end() :]
        tables = parse_markdown_tables(rest)
        if tables:
            return tables[0]
    for table in parse_markdown_tables(text):
        if not table:
            continue
        header = _norm(" ".join(table[0]))
        if "delta" in header and ("system" in header or "comparator" in header):
            return table
    return None


def header_index(header: list[str], *needles: str) -> int | None:
    for i, cell in enumerate(header):
        n = _norm(cell)
        if all(needle in n for needle in needles):
            return i
    return None


def comparator_present(spec: dict[str, object], system_cells: list[str]) -> bool:
    cells_norm = [_norm(c) for c in system_cells]
    blob = " | ".join(cells_norm)
    any_aliases = spec.get("any") or []
    assert isinstance(any_aliases, list)
    if any(alias in blob for alias in any_aliases):
        return True
    all_tokens = spec.get("all_across_rows")
    if isinstance(all_tokens, list) and all_tokens:
        return all(any(token in cell for cell in cells_norm) for token in all_tokens)
    return False


def issues_for_related_work(text: str) -> list[str]:
    issues: list[str] = []
    if not text.strip():
        return ["related-work document is empty"]

    if FORBIDDEN_UPSTREAM.search(text):
        issues.append("related-work frames an Embabel/guide upstream PR (forbidden)")

    if not re.search(r"^#{1,6}\s+.*novelty", text, re.MULTILINE | re.IGNORECASE):
        issues.append("missing Novelty heading")

    novelty_blocks = [
        body
        for heading, body in heading_blocks(text).items()
        if "novelty" in heading
    ]
    novelty = "\n".join(novelty_blocks)
    if novelty:
        quotes = re.findall(r"^>\s*(.+)$", novelty, re.MULTILINE)
        novelty_sentence = " ".join(quotes) if quotes else novelty
        ns = _norm(novelty_sentence)
        if "repository-native" not in ns:
            issues.append("novelty sentence missing 'repository-native'")
        if "observable" not in ns:
            issues.append("novelty sentence missing 'observable'")
        if "c-drift" not in ns and "intent" not in ns:
            issues.append("novelty sentence missing C-DRIFT or intent")
        if "c-comply" not in ns and "compliance" not in ns:
            issues.append("novelty sentence missing C-COMPLY or compliance")
        if "c-context" not in ns and "context" not in ns:
            issues.append("novelty sentence missing C-CONTEXT or context")
        if re.search(r"with evidence that", novelty_sentence, re.IGNORECASE):
            issues.append(
                "novelty sentence must not use 'with evidence that' "
                "(DOC-001 T03: reduced-drift evidence is not this review's aim)"
            )
        if CAUSAL_FINDING.search(novelty_sentence):
            issues.append("novelty sentence uses causal-finding language")

    if not re.search(
        r"^#{1,6}\s+.*not claiming",
        text,
        re.MULTILINE | re.IGNORECASE,
    ):
        issues.append("missing 'What we are not claiming' heading")
    else:
        not_claim = next(
            (
                body
                for heading, body in heading_blocks(text).items()
                if "not claiming" in heading
            ),
            "",
        )
        nc = _norm(not_claim)
        for token in ("llm", "rag", "multi-agent"):
            if token not in nc:
                issues.append(f"not-claiming section missing {token}")
        if "embabel-dif" not in nc and "deterministic intent folding" not in nc:
            issues.append("not-claiming section must name embabel-dif as out of this review")

    if not re.search(r"fork-only", text, re.IGNORECASE):
        issues.append("related-work must state Guide is fork-only")

    table = find_matrix_table(text)
    if table is None or len(table) < 2:
        issues.append("missing Claim × system matrix table with data rows")
        return issues

    header = table[0]
    header_blob = _norm(" ".join(header))
    for token in REQUIRED_MATRIX_HEADER_TOKENS:
        if token not in header_blob:
            issues.append(f"matrix header missing required token {token!r}")

    sys_i = header_index(header, "system")
    if sys_i is None:
        sys_i = header_index(header, "comparator")
    delta_i = header_index(header, "delta")
    if sys_i is None or delta_i is None:
        issues.append("matrix must have System (or Comparator) and Delta columns")
        return issues

    data_rows = table[1:]
    system_cells = []
    for row in data_rows:
        if sys_i >= len(row):
            issues.append(f"matrix row has too few cells: {row!r}")
            continue
        system_cells.append(row[sys_i])
        delta = row[delta_i] if delta_i < len(row) else ""
        delta_plain = re.sub(r"[\\W_]+", "", delta, flags=re.UNICODE)
        if len(delta.strip()) < 24 or len(delta_plain) < 16:
            issues.append(
                f"matrix delta too thin for {row[sys_i]!r} (need a real difference, not '-' or a token)"
            )
        if _norm(delta) in {"-", "n/a", "todo", "tbd", "yes", "no", "same"}:
            issues.append(f"matrix delta is a stub for {row[sys_i]!r}")

    for spec in REQUIRED_COMPARATORS:
        if not comparator_present(spec, system_cells):
            issues.append(f"matrix missing required comparator {spec['id']}")

    return issues


def issues_for_constructs_spec(text: str) -> list[str]:
    issues: list[str] = []
    if not text.strip():
        return ["constructs spec is empty"]
    for rq in ("RQ1", "RQ2", "RQ3", "RQ4", "RQ5"):
        if not re.search(rf"^#{{1,6}}\s+.*{rq}\b", text, re.MULTILINE):
            issues.append(f"constructs spec missing {rq} heading")
    blocks = heading_blocks(text)
    for construct in DOC001_CONSTRUCTS:
        key = construct.lower()
        body = None
        for heading, content in blocks.items():
            # Require the construct id at the start so "RQ1 — Drift (C-DRIFT)"
            # is not treated as the C-DRIFT construct section.
            if heading == key or heading.startswith(f"{key} ") or heading.startswith(f"{key}—") or heading.startswith(f"{key} -"):
                body = content
                break
        if body is None:
            issues.append(f"constructs spec missing {construct} section")
            continue
        for field in CONSTRUCT_FIELDS:
            if field.lower() not in _norm(body):
                issues.append(f"{construct} missing field {field}")
    if "claims allowed today" not in _norm(text):
        issues.append("constructs spec missing claims-allowed table heading")
    if not re.search(r"fixes.*drift", text, re.IGNORECASE):
        issues.append("claims table must mention the forbidden 'fixes drift' claim")
    if "## 1. Academic review goal" not in text:
        issues.append("constructs spec must freeze the academic review goal (DOC-001 §1)")
    blob = _norm(text)
    if "advice store" not in blob or "lessons.jsonl" not in text:
        issues.append("constructs spec must name the advice store (lessons.jsonl)")
    quotes = re.findall(r"^>\s*(.+)$", text, re.MULTILINE)
    contribution = " ".join(quotes)
    if re.search(r"with evidence that", contribution, re.IGNORECASE):
        issues.append(
            "contribution sentence must not use 'with evidence that' "
            "(reduced-drift evidence is not this review's object)"
        )
    if "embabel-dif" not in blob:
        issues.append("constructs spec must name embabel-dif as later/out of scope")
    if "retriev" not in blob:
        issues.append("constructs spec must name retrievability as the in-scope empirical claim")
    if "context retrieve" not in blob:
        issues.append("constructs spec must name context retrieve")
    if "guide" not in blob:
        issues.append("constructs spec must name the Guide store")
    if "sqlite" not in blob:
        issues.append("constructs spec must name the SQLite store")
    if "c-retrieve" not in blob:
        issues.append("constructs spec must name supporting measure C-RETRIEVE")
    if "scope removed" not in blob:
        issues.append(
            "constructs spec must state that this review's scope removed drift and usefulness"
        )
    return issues


def issues_for_evaluation_protocol(text: str) -> list[str]:
    issues: list[str] = []
    if not text.strip():
        return ["evaluation protocol is empty"]
    blob = _norm(text)
    for rq in ("rq1", "rq2", "rq3", "rq4", "rq5"):
        if rq not in blob:
            issues.append(f"protocol missing {rq.upper()}")
        # Each RQ must have a procedure, not a name-drop: require a heading or labeled step.
        if not re.search(
            rf"^#{{1,6}}\s+.*{rq}\b|^\*\*{rq}\b|^{rq}\s*[—\-:].*procedur",
            text,
            re.MULTILINE | re.IGNORECASE,
        ):
            issues.append(f"protocol missing a procedure heading/label for {rq.upper()}")
    for baseline in TEST001_BASELINES:
        if baseline not in blob:
            issues.append(f"protocol missing baseline {baseline!r}")
    if "gold task" not in blob:
        issues.append("protocol missing gold task")
    else:
        if not re.search(
            r"(examples/|tests/|[A-Za-z0-9_./-]+\.(py|java|md|ts))",
            text,
        ):
            issues.append("gold task does not name a concrete file path")
    if "rater" not in blob:
        issues.append("protocol missing rater protocol")
    if "stop rule" not in blob and "stop rules" not in blob:
        issues.append("protocol missing stop rule")
    if "nondetermin" not in blob:
        issues.append("protocol missing nondeterminism plan")
    if "java" not in blob:
        issues.append("protocol must list the Spring Boot example Java-source gap")
    if "cursor" not in blob:
        issues.append("protocol must list the Cursor-oriented live-consumer limitation")
    if not re.search(
        r"(do not collect|not collect(ing)? study data|protocol only|no study data)",
        text,
        re.IGNORECASE,
    ):
        issues.append("protocol must state that this Work ID does not collect study data")
    if FORBIDDEN_UPSTREAM.search(text):
        issues.append("protocol frames an Embabel/guide upstream PR (forbidden)")
    if CAUSAL_FINDING.search(text) and "must not" not in blob:
        # Allow discussing forbidden language; fail if it looks like a result paragraph.
        if re.search(r"\b(result|we found|n\s*=\s*\d+)", text, re.IGNORECASE):
            issues.append("protocol contains study-result language (TEST-001 is protocol only)")
    return issues


def _heading_body(blocks: dict[str, str], *needles: str) -> str | None:
    for heading, body in blocks.items():
        if all(needle in heading for needle in needles):
            return body
    return None


def find_replication_table(text: str) -> list[list[str]] | None:
    for table in parse_markdown_tables(text):
        if not table:
            continue
        header = _norm(" ".join(table[0]))
        has_loc = "command" in header or "location" in header
        has_freeze = "freeze" in header or "version" in header
        if has_loc and has_freeze:
            return table
    return None


def issues_for_threats_replication(text: str) -> list[str]:
    """Structured checks for DOC-003. Token name-drops are not enough."""
    issues: list[str] = []
    if not text.strip():
        return ["threats/replication pack is empty"]
    blob = _norm(text)
    blocks = heading_blocks(text)

    for category in THREAT_CATEGORIES:
        if _heading_body(blocks, category) is None:
            issues.append(f"missing {category} validity heading")

    construct_body = _heading_body(blocks, "construct") or ""
    construct_blob = _norm(construct_body)
    for construct in DOC001_CONSTRUCTS:
        if construct.lower() not in construct_blob:
            issues.append(f"construct-validity section missing {construct}")

    table = find_replication_table(text)
    if table is None or len(table) < 2:
        issues.append(
            "missing replication checklist table with Freeze and Location/command columns"
        )
    else:
        data_rows = table[1:]
        if len(data_rows) < 4:
            issues.append("replication checklist has fewer than 4 freeze rows")
        for row in data_rows:
            joined = _norm(" ".join(row))
            if joined in {"", "-", "n/a", "todo", "tbd"} or len(joined) < 12:
                issues.append(f"replication checklist row is a stub: {row!r}")

    if REPLICATION_GOLD not in text:
        issues.append(f"replication pack must name gold path {REPLICATION_GOLD}")
    if "evaluation-protocol.md" not in text:
        issues.append("replication pack must cite evaluation-protocol.md")
    if _heading_body(blocks, "nondetermin") is None:
        issues.append("missing nondeterminism heading")
    if "test-001" not in blob and "test 001" not in blob:
        issues.append("nondeterminism handling must cite TEST-001")
    if not re.search(r"n\s*≥\s*3|n\s*>=\s*3|n\s*>?=\s*3", text, re.IGNORECASE):
        issues.append("must restate TEST-001 n≥3 rule")
    if "protocol incomplete" not in blob:
        issues.append("must restate TEST-001 protocol-incomplete rule for n=1")
    if "live-consumer" not in blob:
        issues.append("must discuss the live-consumer harness")
    if not re.search(
        r"does not prove|do not (cite|treat|use).{0,80}live-consumer.{0,40}(as a )?(test-002|result|c-drift)",
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        issues.append("must state that live-consumer does not prove the method / C-DRIFT")
    if "cannot be automated" not in blob and "not be automated" not in blob:
        issues.append("must state what cannot be automated")
    if "git rev-parse" not in blob and "commit sha" not in blob and "git sha" not in blob:
        issues.append("must say how to freeze the engine commit (git SHA)")
    if "sdlc_engine" not in blob and "__version__" not in blob and "engine version" not in blob:
        issues.append("must say how to freeze the engine version")
    if "model" not in blob:
        issues.append("must say how to freeze the model id")
    if "sampling" not in blob and "temperature" not in blob:
        issues.append("must name assistant sampling (or temperature) as a nondeterminism source")
    if FORBIDDEN_UPSTREAM.search(text):
        issues.append("replication pack frames an Embabel/guide upstream PR (forbidden)")
    if CAUSAL_FINDING.search(text) and "must not" not in blob and "do not" not in blob:
        if re.search(r"\b(we found|n\s*=\s*\d+\s+showed)", text, re.IGNORECASE):
            issues.append("replication pack contains study-result language")
    return issues


def _run_canvas_validator(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing canvas {path.relative_to(REPO_ROOT)}"]
    if not VALIDATE_CANVAS.is_file():
        return [f"missing validator {VALIDATE_CANVAS}"]
    proc = subprocess.run(
        [str(VALIDATE_CANVAS), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return [
            f"canvas validator failed for {path.name}: "
            f"{(proc.stderr or proc.stdout).strip()[:400]}"
        ]
    return []


def _review_issues(path: Path, work_id: str) -> list[str]:
    if not path.is_file():
        return [f"missing review {path.relative_to(REPO_ROOT)}"]
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    if work_id.lower() not in _norm(text):
        issues.append(f"review does not mention {work_id}")
    if not re.search(r"result\s*:", text, re.IGNORECASE):
        issues.append("review missing Result line")
    if not re.search(r"approv", text, re.IGNORECASE):
        issues.append("review missing approval language")
    return issues


def check_doc001() -> list[str]:
    spec = RESEARCH / "research-questions-and-constructs.md"
    issues: list[str] = []
    if not spec.is_file():
        return ["missing sdlc-spdd/docs/research/research-questions-and-constructs.md"]
    issues.extend(issues_for_constructs_spec(spec.read_text(encoding="utf-8")))
    issues.extend(
        _run_canvas_validator(CANVAS_DIR / "DOC-001-research-questions-and-constructs.md")
    )
    issues.extend(
        _review_issues(
            REVIEW_DIR / "DOC-001-research-questions-and-constructs-review.md",
            "DOC-001",
        )
    )
    readme = REPO_ROOT / "README.md"
    if readme.is_file():
        readme_text = readme.read_text(encoding="utf-8")
        if "fixes that" in readme_text:
            issues.append("README.md still contains 'fixes that'")
        if "designed to make that drift" not in readme_text:
            issues.append("README.md missing design-intent hedge sentence")
    return issues


def check_doc002() -> list[str]:
    doc = RESEARCH / "related-work-and-novelty.md"
    if not doc.is_file():
        return ["missing sdlc-spdd/docs/research/related-work-and-novelty.md"]
    issues = issues_for_related_work(doc.read_text(encoding="utf-8"))
    issues.extend(_run_canvas_validator(CANVAS_DIR / "DOC-002-related-work-map.md"))
    issues.extend(_review_issues(REVIEW_DIR / "DOC-002-related-work-map-review.md", "DOC-002"))
    return issues


def check_test001() -> list[str]:
    doc = RESEARCH / "evaluation-protocol.md"
    if not doc.is_file():
        return ["missing sdlc-spdd/docs/research/evaluation-protocol.md"]
    text = doc.read_text(encoding="utf-8")
    issues = issues_for_evaluation_protocol(text)
    issues.extend(_run_canvas_validator(CANVAS_DIR / "TEST-001-evaluation-protocol.md"))
    issues.extend(
        _review_issues(REVIEW_DIR / "TEST-001-evaluation-protocol-review.md", "TEST-001")
    )
    example = REPO_ROOT / "examples" / "spring-boot-order-api"
    java_sources = list(example.rglob("*.java")) if example.is_dir() else []
    if not java_sources and not re.search(r"no java", text, re.IGNORECASE):
        issues.append(
            "protocol must record that examples/spring-boot-order-api currently has no Java sources"
        )
    if java_sources and re.search(r"no java sources", text, re.IGNORECASE):
        issues.append(
            "protocol claims no Java sources but .java files exist under examples/spring-boot-order-api"
        )
    seed = REPO_ROOT / "tests" / "live-consumer" / "seed" / "src" / "hello.py"
    if re.search(r"live-consumer/seed", text) and not seed.is_file():
        issues.append("protocol names live-consumer seed but tests/live-consumer/seed/src/hello.py is missing")
    return issues


def check_doc003() -> list[str]:
    doc = RESEARCH / "threats-to-validity-and-replication.md"
    if not doc.is_file():
        return ["missing sdlc-spdd/docs/research/threats-to-validity-and-replication.md"]
    text = doc.read_text(encoding="utf-8")
    issues = issues_for_threats_replication(text)
    issues.extend(_run_canvas_validator(CANVAS_DIR / "DOC-003-replication-package.md"))
    issues.extend(
        _review_issues(REVIEW_DIR / "DOC-003-replication-package-review.md", "DOC-003")
    )
    seed = REPO_ROOT / "tests" / "live-consumer" / "seed" / "src" / "hello.py"
    if REPLICATION_GOLD in text and not seed.is_file():
        issues.append(f"replication pack names {REPLICATION_GOLD} but the file is missing")
    protocol = RESEARCH / "evaluation-protocol.md"
    if "evaluation-protocol.md" in text and not protocol.is_file():
        issues.append("replication pack cites evaluation-protocol.md but the file is missing")
    if FORBIDDEN_UPSTREAM.search(text):
        issues.append("DOC-003 frames an Embabel/guide upstream PR (forbidden)")
    return issues


CHECKERS = {
    "DOC-001": check_doc001,
    "DOC-002": check_doc002,
    "TEST-001": check_test001,
    "DOC-003": check_doc003,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-id",
        required=True,
        choices=sorted(CHECKERS) + ["all"],
    )
    args = parser.parse_args(argv)
    targets = list(CHECKERS) if args.work_id == "all" else [args.work_id]
    failed = False
    for work_id in targets:
        issues = CHECKERS[work_id]()
        if issues:
            failed = True
            print(f"FAIL {work_id}", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)
        else:
            print(f"PASS {work_id}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
