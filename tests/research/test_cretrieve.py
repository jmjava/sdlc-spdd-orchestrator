"""TEST-003: C-RETRIEVE round-trip suite for the academic-review claim.

Smoke: persist one lesson, then require the same id back from the git ledger,
from SQLite when enabled, and from Guide parity when enabled (HTTP mocked
so default CI does not need Neo4j).

Non-trivial: a four-record fixture (two Work IDs, three areas, three kinds)
must retrieve the matching subset for a given work/area/kind/query context
and exclude sibling records. That is selectivity, not RQ4 usefulness.

Does not prove RQ1 drift, RQ4 usefulness, or Guide embeddings.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from sdlc_engine.context_store import ContextStore  # noqa: E402
from sdlc_engine.persistence import save_config  # noqa: E402
from sdlc_engine.project import Project  # noqa: E402

from .cretrieve_context_select import (  # noqa: E402
    ids_matching,
    load_records,
    persist_records,
    retrieved_ids,
    seed_canvases,
    subgraph_kind_ids,
)

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
        self.assertIn("three storage modes", text)
        self.assertIn("required evidence", text)
        self.assertIn("mocked", text)
        self.assertIn("scope removed", text)
        self.assertIn("drift", text)
        self.assertIn("usefulness", text)
        self.assertIn("embedding", text)
        self.assertIn("test_guide_projection_roundtrip", text)
        self.assertIn("test-guide-stack-experimental", text)
        self.assertIn("embabel-dif", text)
        self.assertIn("later / other-repo", text)
        self.assertIn("the graph-store proof", text)
        self.assertIn("select", text)
        self.assertIn("context", text)
        self.assertIn("sibling", text)

    def test_doc001_names_this_suite(self) -> None:
        text = DOC001.read_text(encoding="utf-8")
        self.assertIn("TEST-003", text)
        self.assertIn("test_cretrieve", text)
        blob = text.lower()
        self.assertIn("scope removed", blob)
        self.assertIn("drift", blob)
        self.assertIn("usefulness", blob)
        self.assertIn("three storage modes", blob)
        self.assertIn("required evidence", blob)
        self.assertIn("test_context_store_guide_live", blob)

    def test_ci_runs_this_suite(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("tests.research.test_cretrieve", text)
        self.assertIn("PYTHONPATH=engine/src", text)

    def test_referee_prove_script_runs_this_suite(self) -> None:
        self.assertTrue(PROVE.is_file(), PROVE)
        text = PROVE.read_text(encoding="utf-8")
        self.assertIn("tests.research.test_cretrieve", text)
        self.assertIn("SDLC_GUIDE_STACK_LIVE=1", text)
        self.assertIn("does NOT prove the Neo4j graph", text)

    def test_live_graph_tests_exist(self) -> None:
        rt = ROOT / "engine" / "tests_e2e" / "test_guide_projection_roundtrip.py"
        triple = ROOT / "engine" / "tests_e2e" / "test_context_store_guide_live.py"
        self.assertTrue(rt.is_file(), rt)
        self.assertTrue(triple.is_file(), triple)
        blob = triple.read_text(encoding="utf-8")
        self.assertIn("test_live_persist_enters_all_backends", blob)
        self.assertIn("test_live_context_selects_right_records", blob)
        self.assertIn("result.guide", blob)
        self.assertIn("work_subgraph", blob)
        self.assertIn("via", blob)


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

            client = MagicMock()
            client.health_ok.return_value = True
            client.work_subgraph.return_value = {
                "ok": True,
                "data": {"pitfalls": [{"id": lesson_id}]},
            }
            with patch("sdlc_engine.context_store.GuideClient", return_value=client):
                parity = store.parity(repair=False)
            self.assertTrue(parity.get("guide", {}).get("enabled"), parity)
            self.assertEqual(parity.get("guide", {}).get("via"), "work_subgraph")
            self.assertNotIn("unreachable", parity.get("guide") or {})
            self.assertEqual(parity.get("guide", {}).get("missing") or [], [], parity)
            self.assertTrue(parity.get("guide", {}).get("ok"), parity)

    def test_unreachable_guide_fails_parity(self) -> None:
        """guide-dice enabled + Guide down is a failed retrieve, not a skip-pass."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers", "guide-dice"])
            _persist_accept(store)
            parity = store.parity(repair=False)
            guide = parity.get("guide") or {}
            self.assertTrue(guide.get("enabled"))
            self.assertTrue(guide.get("unreachable"), guide)
            self.assertFalse(guide.get("ok"), guide)
            self.assertFalse(parity.get("ok"), parity)
            self.assertFalse(bool(guide.get("skipped")), guide)


class ContextualSelectTests(unittest.TestCase):
    """Given retrieve context, return the matching subset — not the whole store."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.records = load_records()
        seed_canvases(self.root, self.records)
        self.store = _store(self.root, ["git-pointers", "sqlite"])
        self.keys = persist_records(self.store, self.records, project_guide=False)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_work_id_excludes_the_other_work(self) -> None:
        alpha = ids_matching(self.records, work_id="FEAT-910-ctx-alpha")
        beta = ids_matching(self.records, work_id="FEAT-911-ctx-beta")
        got = retrieved_ids(self.store, work_id="FEAT-910-ctx-alpha")
        self.assertEqual(got, alpha)
        self.assertTrue(got.isdisjoint(beta))

    def test_area_is_cross_work_and_excludes_other_areas(self) -> None:
        engine = ids_matching(self.records, area="ctx-engine")
        got = retrieved_ids(self.store, area="ctx-engine")
        self.assertEqual(got, engine)
        self.assertIn(self.keys["alpha_engine_pitfall"], got)
        self.assertIn(self.keys["beta_engine_pitfall"], got)
        self.assertNotIn(self.keys["alpha_console_decision"], got)
        self.assertNotIn(self.keys["beta_docs_pattern"], got)

    def test_work_and_kind_intersection(self) -> None:
        expected = ids_matching(
            self.records, work_id="FEAT-910-ctx-alpha", kind="pitfall"
        )
        got = retrieved_ids(
            self.store, work_id="FEAT-910-ctx-alpha", kind="pitfall"
        )
        self.assertEqual(got, expected)
        self.assertEqual(got, {self.keys["alpha_engine_pitfall"]})

    def test_query_inside_work_does_not_leak_sibling_work(self) -> None:
        vue = retrieved_ids(
            self.store, work_id="FEAT-910-ctx-alpha", query="Vue"
        )
        self.assertEqual(vue, {self.keys["alpha_console_decision"]})
        leaked = retrieved_ids(
            self.store, work_id="FEAT-910-ctx-alpha", query="by-label"
        )
        self.assertEqual(leaked, set())

    def test_sqlite_work_and_area_match_ledger_sets(self) -> None:
        alpha = ids_matching(self.records, work_id="FEAT-910-ctx-alpha")
        engine = ids_matching(self.records, area="ctx-engine")
        work_ids = {
            row["id"]
            for row in self.store.index.lessons_for_work("FEAT-910-ctx-alpha")
            if not row["staged"]
        }
        area_ids = {
            row["id"]
            for row in self.store.index.lessons_for_area("ctx-engine")
            if not row["staged"]
        }
        self.assertEqual(work_ids, alpha)
        self.assertEqual(area_ids, engine)

    def test_mocked_work_subgraph_partitions_kinds_per_work(self) -> None:
        records = self.records
        save_config(
            self.root,
            {"backends": ["git-pointers", "sqlite", "guide-dice"]},
        )
        store = ContextStore(Project(self.root), guide_base_url="http://guide.test")

        def work_subgraph(wid: str) -> dict:
            data: dict[str, list] = {
                "pitfalls": [],
                "decisions": [],
                "patterns": [],
            }
            for row in records:
                if row["work_id"] != wid:
                    continue
                data[f"{row['kind']}s"].append({"id": self.keys[row["key"]]})
            return {"ok": True, "data": data}

        client = MagicMock()
        client.health_ok.return_value = True
        client.work_subgraph.side_effect = work_subgraph
        with patch("sdlc_engine.context_store.GuideClient", return_value=client):
            parity = store.parity(repair=False)
            alpha_sg = store._guide_client().work_subgraph("FEAT-910-ctx-alpha")
        self.assertTrue(parity.get("guide", {}).get("ok"), parity)
        data = alpha_sg["data"]
        self.assertEqual(
            subgraph_kind_ids(data, "pitfall"),
            {self.keys["alpha_engine_pitfall"]},
        )
        self.assertEqual(
            subgraph_kind_ids(data, "decision"),
            {self.keys["alpha_console_decision"]},
        )
        self.assertNotIn(
            self.keys["beta_engine_pitfall"], subgraph_kind_ids(data, "pitfall")
        )


class StagedAndOverwriteTests(unittest.TestCase):
    def test_staged_record_is_absent_from_accepted_retrieve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers", "sqlite"])
            result = store.persist_lesson(
                kind="pitfall",
                work_id=WID,
                area=AREA,
                body=f"{MARKER}: staged only",
                source="staged-select",
                accept=False,
                project_guide=False,
            )
            lesson_id = str(result.git.get("id") or "")
            accepted = retrieved_ids(store, work_id=WID)
            self.assertNotIn(lesson_id, accepted)
            staged = store.retrieve(work_id=WID, include_staged=True, limit=20)
            staged_ids = {row.get("id") for row in (staged.get("ledger") or [])}
            self.assertIn(lesson_id, staged_ids)

    def test_last_wins_body_on_same_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed(root)
            store = _store(root, ["git-pointers"])
            store.persist_lesson(
                kind="pitfall",
                work_id=WID,
                area=AREA,
                body="overwrite first body bananasplit",
                source="overwrite",
                accept=True,
                project_guide=False,
            )
            store.persist_lesson(
                kind="pitfall",
                work_id=WID,
                area=AREA,
                body="overwrite second body xylophone",
                source="overwrite",
                accept=True,
                project_guide=False,
            )
            lesson_id = f"pitfall:{WID}:{AREA}:overwrite"
            shown = store.show(lesson_id)
            self.assertIsNotNone(shown)
            assert shown is not None
            self.assertIn("xylophone", shown.get("body") or "")
            self.assertNotIn("bananasplit", shown.get("body") or "")
            hits = retrieved_ids(store, work_id=WID, query="xylophone")
            self.assertEqual(hits, {lesson_id})
            old = retrieved_ids(store, work_id=WID, query="bananasplit")
            self.assertEqual(old, set())


if __name__ == "__main__":
    unittest.main()
