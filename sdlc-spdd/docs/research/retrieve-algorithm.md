# Retrieve algorithm (FEAT-017)

**Work ID:** FEAT-017-retrieval-ir-eval  
**Construct:** C-CONTEXT relevance (lexical proxy)

This is the **written algorithm** for `sdlc-engine context retrieve`. It is not DICE, not Guide embeddings, and not Neo4j.

## Inputs

| Flag | Meaning |
|------|---------|
| `--work-id`, `--area`, `--kind` | Exact-match filters (optional) |
| `--keyword` | Exact membership in `record.keywords` |
| `--query` | Free-text string, tokenized `[a-z0-9]+` length ≥ 2 |
| `--rank` | `keyword-list` \| `title-body` (default: title-body if `--query`, else keyword-list if `--keyword`, else unfiltered ts) |
| `--limit` | Max hits (default 50) |
| `--no-staged` | Accepted ledger only |

## Algorithms

### keyword-list (pre-FEAT-017 default)

A record matches iff `--keyword` (lowercased) is in the record’s `keywords` list. No title/body search. Sort: `ts` desc, `id` desc.

### title-body (lexical baseline)

Candidates: records passing work/area/kind filters (**not** the keyword list). Score each query token: **+3** if it is a substring of `title`, **+1** if it is a substring of `body`. Drop score 0. Sort: score desc, then `ts` desc, `id` desc.

SQLite `db query --search` (FTS5/LIKE) is a **different CLI**, not this retrieve path. Guide `spdd_*` tools are a third path and are **unmeasured** here.

## IR eval

```bash
sdlc-engine context eval-retrieve --fixture tests/research/fixtures/retrieve_ir_qrels.json
```

The fixture is built so exact keyword-list **misses** the relevant pitfall (`keywords: ["notify"]`, query keyword `idempotency`) while title-body **hits** it at rank 1 (`precision@1 = 1`). `dice_measured` is always `false` in this eval.

## DICE / hybrid graph

SPIKE-001 remains shelved. FEAT-017 does **not** measure Guide embeddings. Do not report DICE as an IR result. Lexical title-body vs keyword-list is the only measured retrieve comparison in this repo today.
