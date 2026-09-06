# Analysis: FEAT-017 — Retrieval as information retrieval

## Metadata

- Work ID: FEAT-017-retrieval-ir-eval
- Date: 2026-09-06
- Depends on: DOC-001, FEAT-015 (merged)

## Scope Lock

### In Scope

- Written retrieve algorithm (keyword-list vs title-body)
- Qrel fixture where keyword-list misses and title-body hits
- Precision@k / recall@k in tests
- DICE marked non-claim (no embedding measurement)

### NOT in Scope

- Neo4j / Guide embeddings
- Changing default retrieve for callers that only pass `--keyword`
- TEST-002 study data
- Embabel upstream

## Recommendation

Keep `--keyword` as exact list membership. Add `--query` title-body ranking and `context eval-retrieve` on a committed qrel fixture.
