"""TEST-003: C-RETRIEVE round-trip suite for the academic-review claim.

Persist one lesson, then require the same id back from the git ledger,
from SQLite when enabled, and from Guide parity when enabled (HTTP mocked
so default CI does not need Neo4j).

Does not prove RQ1 drift, RQ4 usefulness, or Guide embeddings.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from sdlc_engine.context_store import ContextStore  # noqa: E402
from sdlc_engine.persistence import save_config  # noqa: E402
from sdlc_engine.project import Project  # noqa: E402

SUITE_DOC = ROOT / "sdlc-spdd" / "docs" / "research" / "cretrieve-suite.md"
DOC001 = ROOT / "sdlc-spdd" / "docs" / "research" / "research-questions-and-constructs.md"
WORKFLOW = ROOT / ".github" / "workflows" / "test-research-p0.yml"
PROVE = ROOT / "sdlc-spdd" / "docs" / "research" / "prove-academic-review.sh"

WID = "TEST-003-cretrieve-roundtrip"
AREA = "engine/retrieve"
MARKER = "C-RETRIEVE-ROUNDTRIP-MARKER"
SOURCE = "test-003"


def _seed(root: Path) -> None:
    req = root / "requirements" / "milestones"
    req.mkdir(parents=True, exist_ok=True)
    (req / f"{WID}.md").write_text(f"# Requirement {WID}\n\nRetrieve proof.\n", encoding="utf-8")
    canvas = root / "spdd" / "canvas"
    canvas.mkdir(parents=True, exist_ok=True)
    (canvas / f"{WID}.md").write_text(
        f"""# REASONS Canvas: {WID}

## Metadata

- Work ID: {WID}
- Work Type: Test
- Status: In Progress
""",
        encoding="utf-8",
    )
    (root / "spdd" / "memory").mkdir(parents=True, exist_ok=True)


def _store(root: Path, backends: list[str]) -> ContextStore:
    save_config(root, {"backends": backends})
    return ContextStore(Project(root), guide_base_url="http://guide.test")


def _persist_accept(store: ContextStore) -> str:
    result = store.persist_lesson(
        kind="pitfall",
        work_id=WID,
        area=AREA,
        body=f"{MARKER}: never treat unreachable Guide as a retrieve pass.",
        source=SOURCE,
        keywords=["cretrieve"],
        project_guide=False,
    )
    assert result.git.get("ok") is True, result.as_dict()
    lesson_id = str(result.git.get("id") or "")
    assert lesson_id, result.as_dict()
    store.accept(work_id=WID, project_guide=False)
    return lesson_id


class SuiteDocTests(unittest.TestCase):
    def test_suite_doc_states_non_claims(self) -> None:
        text = SUITE_DOC.read_text(encoding="utf-8").lower()
        self.assertIn("c-retrieve", text)
        self.assertIn("python 3 only", text)
        self.assertIn("optional", text)
        self.assertIn("scope removed", text)
        self.assertIn("drift", text)
        self.assertIn("usefulness", text)
        self.assertIn("embedding", text)
        self.assertIn("test_guide_projection_roundtrip", text)
        self.assertIn("test-guide-stack-experimental", text)
        self.assertIn("embabel-dif", text)
        self.assertIn("later / other-repo", text)

    def test_doc001_names_this_suite(self) -> None:
        text = DOC001.read_text(encoding="utf-8")
        self.assertIn("TEST-003", text)
        self.assertIn("test_cretrieve", text)
        blob = text.lower()
        self.assertIn("scope removed", blob)
        self.assertIn("drift", blob)
        self.assertIn("usefulness", blob)
        self.assertIn("python 3 only", blob)
        self.assertIn("optional", blob)
        self.assertIn("live guide+neo4j is **required**", blob)
        self.assertIn("first-class", blob)

    def test_ci_runs_this_suite(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("tests.research.test_cretrieve", text)
        self.assertIn("PYTHONPATH=engine/src", text)

    def test_referee_prove_script_runs_this_suite(self) -> None:
        self.assertTrue(PROVE.is_file(), PROVE)
        text = PROVE.read_text(encoding="utf-8")
        self.assertIn("tests.research.test_cretrieve", text)
        self.assertIn("No Docker", text)
        self.assertNotIn("SDLC_GUIDE_STACK_LIVE=1", text)


class LedgerRoundTripTests(unittest.TestCase):
    def test_persist_accept_retrieve_same_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers"])
            lesson_id = _persist_accept(store)
            shown = store.show(lesson_id)
            self.assertIsNotNone(shown)
            assert shown is not None
            self.assertIn(MARKER, shown.get("body") or "")
            hits = store.retrieve(
                work_id=WID,
                kind="pitfall",
                include_staged=False,
                limit=20,
            )
            ids = [row.get("id") for row in (hits.get("ledger") or [])]
            self.assertIn(lesson_id, ids, hits)
            lexical = store.retrieve(
                work_id=WID,
                query="unreachable Guide",
                include_staged=False,
                limit=10,
            )
            lex_ids = [row.get("id") for row in (lexical.get("ledger") or [])]
            self.assertIn(lesson_id, lex_ids, lexical)

    def test_unknown_work_id_does_not_invent_hits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers"])
            _persist_accept(store)
            hits = store.retrieve(
                work_id="FEAT-DOES-NOT-EXIST",
                include_staged=False,
            )
            self.assertEqual(hits.get("ledger") or [], [])


class SqliteRoundTripTests(unittest.TestCase):
    def test_parity_and_graph_contain_accepted_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers", "sqlite"])
            lesson_id = _persist_accept(store)
            parity = store.parity(repair=False)
            self.assertTrue(parity.get("sqlite", {}).get("enabled"))
            self.assertEqual(parity.get("sqlite", {}).get("missing") or [], [])
            self.assertEqual(parity.get("sqlite", {}).get("extra") or [], [])
            self.assertTrue(parity.get("sqlite", {}).get("ok"), parity)
            self.assertIn(lesson_id, store.index.accepted_lesson_ids())
            graph = store.retrieve(
                work_id=WID,
                include_staged=False,
            ).get("sqlite_graph") or {}
            graph_ids = [row.get("id") for row in (graph.get("lessons") or [])]
            self.assertIn(lesson_id, graph_ids, graph)


class GuideRoundTripTests(unittest.TestCase):
    def test_mocked_guide_parity_finds_ledger_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers", "sqlite", "guide-dice"])
            lesson_id = _persist_accept(store)

            class Resp:
                status = 200

                def __init__(self, payload: bytes) -> None:
                    self._payload = payload

                def read(self) -> bytes:
                    return self._payload

                def __enter__(self) -> Resp:
                    return self

                def __exit__(self, *a: object) -> bool:
                    return False

            def fake_urlopen(req: Request, timeout: float = 30.0) -> Resp:
                url = getattr(req, "full_url", "") or str(req)
                if "by-label" in url:
                    return Resp(json.dumps({"items": [{"id": lesson_id}]}).encode())
                return Resp(b"{}")

            with patch("sdlc_engine.context_store.urllib.request.urlopen", fake_urlopen):
                parity = store.parity(repair=False)
            self.assertTrue(parity.get("guide", {}).get("enabled"), parity)
            self.assertNotIn("unreachable", parity.get("guide") or {})
            self.assertEqual(parity.get("guide", {}).get("missing") or [], [], parity)
            self.assertTrue(parity.get("guide", {}).get("ok"), parity)

    def test_unreachable_guide_is_skip_not_a_pass_of_the_claim(self) -> None:
        """parity() must not report guide ok-with-missing-empty when HTTP fails.

        Unreachable is skipped; that is not C-RETRIEVE evidence. This test
        locks the skip shape so we do not mistake it for a round-trip.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers", "guide-dice"])
            _persist_accept(store)
            parity = store.parity(repair=False)
            guide = parity.get("guide") or {}
            self.assertTrue(guide.get("enabled"))
            self.assertTrue(guide.get("skipped") or guide.get("unreachable") or guide.get("ok") is False)
            self.assertTrue(
                guide.get("unreachable") or guide.get("skipped"),
                f"unreachable Guide must be labelled skip, got {guide}",
            )


if __name__ == "__main__":
    unittest.main()
