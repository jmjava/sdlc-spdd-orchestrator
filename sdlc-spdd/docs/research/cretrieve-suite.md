# C-RETRIEVE suite (TEST-003)

**Work ID:** TEST-003-cretrieve-roundtrip  
**Construct:** C-RETRIEVE (DOC-001 §1 academic-review claim)

This is the **named hermetic test pack** for ledger + SQLite + the Guide
**client contract** on default CI. The paper claim is **three storage modes**.
Live **Guide+Neo4j** is **required evidence** for the graph mode. Mocked HTTP
is **not** the graph-store proof.

This review's **scope removed** reduced-**drift** (RQ1) and retrieve-**usefulness**
(RQ4). Those are not leftover TEST-003 work. Guide embeddings were never this
bar. `embabel-dif` was **removed** from this review (later / other-repo).

## Command

Hermetic (ledger + SQLite + mocked Guide client):

```bash
PYTHONPATH=engine/src python3 -m unittest tests.research.test_cretrieve -v
```

Research CI (`test-research-p0.yml`) runs the same module.

Referee hermetic one-shot (P0 docs + C-RETRIEVE hermetic + SUT + dogfood ledger):

```bash
./sdlc-spdd/docs/research/prove-academic-review.sh
```

**Required** live graph (mode 3):

```bash
SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh
```

CI: `.github/workflows/test-guide-stack-experimental.yml` (`guide-neo4j-live`).

## What it proves

| Store | Round-trip | Status for this freeze |
|-------|------------|------------------------|
| Git ledger | persist/accept → `context retrieve` / `context show` returns the same id. **T04:** given two Work IDs and three areas, retrieve-by-work / area / kind / query returns the matching ids and excludes **sibling** records | Hermetic TEST-003 — proven |
| SQLite | when enabled, `context parity` has empty missing/extra; `lessons_for_work` / `lessons_for_area` match the ledger subsets | Hermetic TEST-003 — proven |
| Guide (client) | **mocked** `work_subgraph` so `context parity` missing is empty on default CI; mocked per-work kind lists for T04 | Client contract only — **not** the graph |
| Guide (live Neo4j graph) | persist derives Guide v2 ingest from the ledger, load, then `work_subgraph` must return the same id **and** `test_live_context_selects_right_records` must keep work-local ids out of the other work and keep other-area ids out of `area_lessons` (`engine/tests_e2e/test_guide_projection_roundtrip.py` + `test_context_store_guide_live.py` via `tests/test-guide-stack-live.sh`) | **Required** graph-mode proof |

`sdlc-spdd-projection-v2` projects canvases + `spdd/memory/context-index.md`, not `lessons.jsonl`. `ContextStore.project_to_guide` rebuilds that table from accepted ledger records so the graph stores `{kind}:{workId}:{area}:{source}`. A test that only writes the markdown table is not a C-RETRIEVE pass.

Unreachable Guide is a skip in `parity()`, **not** a C-RETRIEVE pass of the graph mode.

## From trivial to non-trivial (T04)

Writing one pitfall and reading that id back is a smoke test. The graph store
is only doing work if **retrieve context** changes which records come back.

Fixture: `tests/research/fixtures/cretrieve_context_select.json` (two Work IDs,
three areas, pitfall / decision / pattern). Exact id-set equality, not “contains.”

| Axis | What the test demands | Not claimed |
|------|----------------------|-------------|
| Work context | `context retrieve --work-id ALPHA` returns ALPHA’s two records, none of BETA | Not usefulness (RQ4) |
| Area context | `--area ctx-engine` is **cross-work** (both engine pitfalls) and excludes console/docs | Not embeddings |
| Kind ∩ work | ALPHA + pitfall is one id | — |
| Query inside work | query `Vue` inside ALPHA hits the console decision; `by-label` does not leak BETA | Lexical only (FEAT-017); not DICE IR |
| SQLite | `lessons_for_work` / `lessons_for_area` match those sets | `db query --search` is a different CLI |
| Live graph | `work_subgraph(ALPHA)` has ALPHA ids, not BETA; pitfalls vs decisions stay typed; `area_lessons(ctx-engine)` has both engine pitfalls, not the console decision | Skip/unreachable is not a pass |
| Staged vs accepted | staged id is absent from accepted retrieve | — |
| Last-wins | same id rewritten; retrieve finds v2 body, not v1 | — |

Deferred (still not this freeze): near-duplicate bodies that only a ranker
can separate; hyphenated queries that share tokens (`unique-token-v1` vs
`unique-token-v2` both match `unique`/`token`); incremental load across
Guide process restarts; embeddings; n≥3 significance tests.

## Removed from this review's scope

- reduced-**drift** (RQ1)
- retrieve-**usefulness** (RQ4 / C-MEMORY follow-on rework)
- Guide **embeddings** / DICE IR (never this bar; `dice_measured` stays false on FEAT-017)
- treating `db query --search` (work_items FTS) as `context retrieve`
- treating mocked Guide HTTP as the Neo4j graph store
