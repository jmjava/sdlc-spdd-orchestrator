"""Lexical retrieve algorithms for the lessons ledger (FEAT-017).

Two baselines, no embeddings, no Neo4j:

- ``keyword-list`` — exact membership of ``--keyword`` in ``record.keywords``
  (the pre-FEAT-017 ``LessonsLedger.records(keyword=…)`` filter). Sort: ts, id
  descending.
- ``title-body`` — tokenize the query; score +3 per token in title, +1 per
  token in body (case-insensitive substring). Sort: score desc, then ts, id
  desc. Records with score 0 are dropped.

Neither baseline is DICE / Guide embedding retrieval. DICE remains unmeasured.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .lessons_ledger import LessonRecord

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

ALG_KEYWORD_LIST = "keyword-list"
ALG_TITLE_BODY = "title-body"
ALG_UNFILTERED_TS = "unfiltered-ts"

TITLE_WEIGHT = 3.0
BODY_WEIGHT = 1.0


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if len(t) >= 2]


def keyword_list_filter(records: Iterable[LessonRecord], keyword: str) -> list[LessonRecord]:
    kw = (keyword or "").strip().lower()
    out = [r for r in records if not kw or kw in [k.lower() for k in r.keywords]]
    out.sort(key=lambda r: (r.ts, r.id), reverse=True)
    return out


def title_body_score(record: LessonRecord, query: str) -> float:
    tokens = tokenize(query)
    if not tokens:
        return 0.0
    title = (record.title or "").lower()
    body = (record.body or "").lower()
    score = 0.0
    for tok in tokens:
        if tok in title:
            score += TITLE_WEIGHT
        if tok in body:
            score += BODY_WEIGHT
    return score


def rank_title_body(records: Iterable[LessonRecord], query: str) -> list[tuple[float, LessonRecord]]:
    scored = [(title_body_score(r, query), r) for r in records]
    hit = [(s, r) for s, r in scored if s > 0]
    hit.sort(key=lambda pair: (-pair[0], pair[1].ts, pair[1].id))
    return hit


def precision_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = ranked_ids[:k]
    if not top:
        return 0.0
    return sum(1 for i in top if i in relevant) / float(k)


def recall_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = set(ranked_ids[: max(0, k)])
    return len(top & relevant) / float(len(relevant))


def records_from_fixture(data: dict[str, Any]) -> list[LessonRecord]:
    out: list[LessonRecord] = []
    for raw in data.get("records") or []:
        out.append(
            LessonRecord(
                id=str(raw.get("id") or ""),
                kind=str(raw.get("kind") or "pitfall"),
                work_id=str(raw.get("work_id") or ""),
                area=str(raw.get("area") or ""),
                phase=str(raw.get("phase") or ""),
                title=str(raw.get("title") or ""),
                body=str(raw.get("body") or ""),
                source=str(raw.get("source") or "eval"),
                keywords=[str(k) for k in (raw.get("keywords") or [])],
            )
        )
    return out


def evaluate_fixture(data: dict[str, Any]) -> dict[str, Any]:
    """Run keyword-list vs title-body on a qrel fixture. No embeddings."""
    records = records_from_fixture(data)
    query = str(data.get("query") or "")
    keyword = str(data.get("keyword") or "")
    k = int(data.get("k") or 1)
    qrels = {str(i): int(rel) for i, rel in (data.get("qrels") or {}).items()}
    relevant = {i for i, rel in qrels.items() if rel > 0}

    kw_ids = [r.id for r in keyword_list_filter(records, keyword)]
    tb_ids = [r.id for _, r in rank_title_body(records, query)]

    return {
        "query": query,
        "keyword": keyword,
        "k": k,
        "relevant": sorted(relevant),
        "dice_measured": False,
        "baselines": {
            ALG_KEYWORD_LIST: {
                "ids": kw_ids,
                "precision_at_k": precision_at_k(kw_ids, relevant, k),
                "recall_at_k": recall_at_k(kw_ids, relevant, k),
            },
            ALG_TITLE_BODY: {
                "ids": tb_ids,
                "precision_at_k": precision_at_k(tb_ids, relevant, k),
                "recall_at_k": recall_at_k(tb_ids, relevant, k),
            },
        },
    }


def load_and_evaluate(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return evaluate_fixture(data)
