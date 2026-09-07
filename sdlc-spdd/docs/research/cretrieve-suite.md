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
| Git ledger | persist/accept → `context retrieve` / `context show` returns the same id | Hermetic TEST-003 — proven |
| SQLite | when enabled, `context parity` has empty missing/extra; retrieve `sqlite_graph` includes the id | Hermetic TEST-003 — proven |
| Guide (client) | **mocked** `by-label` HTTP so `context parity` missing is empty on default CI | Client contract only — **not** the graph |
| Guide (live Neo4j graph) | `engine/tests_e2e/test_guide_projection_roundtrip.py` + `test_context_store_guide_live.py` via `tests/test-guide-stack-live.sh` | **Required** graph-mode proof |

Unreachable Guide is a skip in `parity()`, **not** a C-RETRIEVE pass of the graph mode.

## Removed from this review's scope

- reduced-**drift** (RQ1)
- retrieve-**usefulness** (RQ4 / C-MEMORY follow-on rework)
- Guide **embeddings** / DICE IR (never this bar; `dice_measured` stays false on FEAT-017)
- treating `db query --search` (work_items FTS) as `context retrieve`
- treating mocked Guide HTTP as the Neo4j graph store
