"""FEAT-017: lexical retrieve vs exact keyword-list (C-CONTEXT relevance proxy)."""

from __future__ import annotations

import json
from pathlib import Path

from sdlc_engine.cli import main
from sdlc_engine.lessons_ledger import LessonRecord
from sdlc_engine.retrieve import (
    ALG_KEYWORD_LIST,
    ALG_TITLE_BODY,
    evaluate_fixture,
    keyword_list_filter,
    load_and_evaluate,
    rank_title_body,
)

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "research"
    / "fixtures"
    / "retrieve_ir_qrels.json"
)


def test_keyword_list_misses_relevant_title_body_hit() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    out = evaluate_fixture(data)
    relevant = "pitfall:FEAT-017-fixture:notify:eval"
    kw = out["baselines"][ALG_KEYWORD_LIST]
    tb = out["baselines"][ALG_TITLE_BODY]
    assert relevant not in kw["ids"][: out["k"]]
    assert kw["precision_at_k"] == 0.0
    assert tb["ids"][0] == relevant
    assert tb["precision_at_k"] == 1.0
    assert tb["recall_at_k"] == 1.0
    assert out["dice_measured"] is False


def test_load_and_evaluate_path() -> None:
    out = load_and_evaluate(FIXTURE)
    assert out["baselines"][ALG_TITLE_BODY]["precision_at_k"] == 1.0


def test_rank_ignores_keyword_list_membership() -> None:
    rec = LessonRecord(
        id="pitfall:x:notify:t",
        kind="pitfall",
        work_id="x",
        area="notify",
        title="idempotency key required",
        body="retry",
        keywords=["notify"],
        source="t",
    )
    assert keyword_list_filter([rec], "idempotency") == []
    ranked = rank_title_body([rec], "idempotency key")
    assert ranked and ranked[0][1].id == rec.id
    assert ranked[0][0] > 0


def test_cli_eval_retrieve(tmp_path: Path, capsys) -> None:
    rc = main(["context", "eval-retrieve", "--fixture", str(FIXTURE)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dice_measured"] is False
    assert payload["baselines"][ALG_KEYWORD_LIST]["precision_at_k"] == 0.0
    assert payload["baselines"][ALG_TITLE_BODY]["precision_at_k"] == 1.0
