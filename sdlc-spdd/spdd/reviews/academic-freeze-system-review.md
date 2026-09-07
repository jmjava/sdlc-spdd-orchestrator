# Academic freeze — system review

**Date:** 2026-09-07  
**Scope:** this repository as the journal-style artifact (stores + retrievability).  
**Result:** **Changes Requested** on operator/front-door copy. TEST-003 T01–T05 are complete (`e716100` / #259).  
**Not claimed:** RQ1 drift, RQ4 usefulness, embeddings, n≥3, DIF, Embabel upstream.

This is a hostile-reviewer pass against the freeze, not a new Work ID.

## What is actually proven

| Claim | Where it is proven | Not a substitute |
|-------|--------------------|------------------|
| Git ledger persist→read | TEST-003 hermetic `test_cretrieve` | — |
| SQLite persist→read **when enabled** | same suite + live e2e with sqlite in backends | Default install does **not** enable sqlite |
| Guide **client** contract | mocked `work_subgraph` on research P0 | Not Neo4j |
| Guide **graph** persist→read | live `test_guide_projection_roundtrip.py` + `test_context_store_guide_live.py` via `test-guide-stack-experimental.yml` | `prove-academic-review.sh` (hermetic) |
| Context-select | T04 hermetic + live `test_live_context_selects_right_records` | RQ4 usefulness |
| Unreachable Guide fails parity | `ContextStore.parity` + CLI exit 1; live job fails if Embabel is down | Slash-command effects (those must not block) |

Hermetic referee command: `./sdlc-spdd/docs/research/prove-academic-review.sh`  
Required graph command: `SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh`

## Findings to fix or improve

### F1 — high — Front-door docs still say live Guide is optional / skip

A referee who starts at README / TESTING / ops-console will conclude the opposite of DOC-001 T05.

| Location | What it says now |
|----------|------------------|
| `README.md` (~268) | “Guide Neo4j projection is **optional**. When disabled or unreachable, every command still works…” |
| `TESTING.md` (~150) | “Live Guide+Neo4j is **optional** (`SDLC_GUIDE_STACK_LIVE=1 …`)” |
| `docs/ops-console.md` (~110) | “The experimental workflow **skips** live Guide+Neo4j … when `repo.embabel.com` is unreachable” |
| `CHANGELOG.md` | Older bullets still say skip-on-unreachable and “Live Guide+Neo4j stays **optional**” (even with a superseded note) |
| `sdlc-spdd/spdd/canvas/DOC-003-replication-package.md` Sync Notes | “Live Guide remains optional” |

Consumer **install** can stay optional. Freeze **evidence** cannot. Split those two sentences everywhere a human actually reads.

**Fix:** rewrite those surfaces. Keep slash-command “do not block when Guide is absent.” Delete skip-as-pass language for the experimental job.

### F2 — high — P0 checker does not police operator docs

`check_p0_artifacts.py` fails “live Guide+Neo4j stays **optional**” only in research specs. It does not scan `README.md`, `TESTING.md`, `docs/ops-console.md`, `docs/storage-v3.md`, or CHANGELOG — which is where F1 still lives.

**Fix:** extend P0 (or a sibling gate) to fail freeze-forbidden phrases on those files. That is how T04/T05 regressions came back.

### F3 — high — “Three storage modes” is test-proven, not the default operator matrix

- Defaults: `git-pointers` + `guide-dice` (`engine/src/sdlc_engine/persistence.py`). SQLite is opt-in.
- Persist: git success can leave `result.ok` true while Guide/SQLite are `partial` (soft-fail).
- Parity: Guide enabled + down → `ok: false`, CLI exit 1 (hard-fail).

Laptop with default backends and no Guide: capture looks fine; `sdlc-engine context parity` fails. Freeze tests enable sqlite explicitly. The paper claim is “three modes exist and are proven,” not “a default install runs all three.”

**Fix:** say that in DOC-001 / storage-v3 / README in one place. Do not quietly add sqlite to defaults without a Work ID.

### F4 — medium — Console still coaches “files-only is normal”

`engine/src/sdlc_engine/installer/dashboard.py` when Guide is enabled but unreachable:

> “Guide is configured but unreachable — start it from the Guide tab, or continue files-only **(normal).**”

CLI parity is a fail. The dashboard calls the same state normal.

**Fix:** if `guide-dice` is enabled and unreachable, copy must match CLI (start Guide **or disable the backend**), not “normal files-only.” Disabled Guide (`enabled: false`) can stay non-blocking.

### F5 — medium — Experimental workflow path filters miss claim-bearing docs

`.github/workflows/test-guide-stack-experimental.yml` watches `sdlc-spdd/docs/research/**` but not `README.md`, `TESTING.md`, `docs/ops-console.md`, or `CHANGELOG.md`. Combined with F2, rewriting freeze language in the docs people read neither fails P0 nor re-runs graph CI.

**Fix:** add those paths, or drop path filters on `main` for the evidence job.

### F6 — medium — Graph “read” is subgraph id/text; `get_lesson` 403 is allowed

`engine/tests_e2e/test_guide_projection_roundtrip.py`: if `get_lesson` is not `ok`, the test still passes when `status == 403`. Guide v2 ingest is `context-index.md`, not `lessons.jsonl`. Some runbooks/diagrams still talk as if JSONL ingest / `spdd_getLesson` is the read path.

**Fix:** document v2 ingest honestly. Treat 403 as a named limitation, or fail until full-body read works. Do not imply `lessons.jsonl` is what Neo4j ingested.

### F7 — medium — Bare `test-guide-stack-live.sh` exits 0 SKIP

Without `SDLC_GUIDE_STACK_LIVE=1` (and not CI), the script prints SKIP and **exit 0** (`tests/test-guide-stack-live.sh` ~28–31). CI + Embabel-down is fixed. A careless referee running the script with no flag gets a green skip.

**Fix:** exit non-zero with “not a C-RETRIEVE pass,” or require an explicit `--allow-skip`.

### F8 — low — Duplicate / superseded contract text

- DOC-001 canvas still checks T04 “live Guide+Neo4j stays optional” **and** T05 “required evidence” (history is real; a reader can pick the wrong checkbox).
- `MILESTONE-2.md` table said “live Neo4j extra” (corrected in this close-out).
- `docs/` vs `sdlc-spdd/docs/` copies of storage/session docs can drift independently.

**Fix:** one-line “T04 superseded by T05” on the DOC-001 T04 operation; keep a single shipped-docs rule.

### F9 — low — Deferred retrieve honesty (already named, not leftover TEST-003)

From `cretrieve-suite.md`: hyphenated last-wins queries that share tokens; near-duplicates only a ranker can split; incremental load across Guide restarts. Not RQ4. Do not call them TEST-003 holes.

## Recommended next (do not open unless asked)

1. Docs honesty pass: README, TESTING, ops-console, CHANGELOG, DOC-003 sync note, dashboard copy (F1, F4, F8).
2. Extend P0 checker to those files (F2).
3. Workflow path-filter / live-script skip-exit (F5, F7).
4. Named limitation for `get_lesson` 403 vs subgraph-only read (F6).

Do **not** invent a SPIKE for RQ1/RQ4. Do **not** treat hermetic P0 green as mode-3 proof.

## Required to accept this freeze as written

F1 is the one a referee will actually hit. Until front-door docs match DOC-001 T05, the tree contains two stories.
