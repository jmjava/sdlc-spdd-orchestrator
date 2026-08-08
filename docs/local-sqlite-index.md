# Local SQLite index (pre-GUIDE)

Lightweight, **zero-install** query cache for Work IDs and artifacts. Uses Python’s
stdlib `sqlite3` — no database server.

## What it is / is not

| Is | Is not |
|----|--------|
| Regenerable index under `.sdlc/index.sqlite` (gitignored) | A multi-user live shared database |
| Fast local `SELECT` / full-text over canvases + registry | A replacement for GUIDE/Neo4j RAG |
| Optional JSON/SQL export for inspection | Something you commit and merge as a binary |

**Multi-user sync stays git:** `work-registry.tsv`, canvases, milestone requirements.
Each machine rebuilds its own SQLite file after pull/claim.

This is the intended step **before** optional Guide (Embabel Guide + Neo4j): same
questions, cheaper substrate. SPIKE-001’s Guide path is on `main` for field
confirmation; SQLite remains the zero-install local cache either way. See
[ops-console.md](ops-console.md) (SQLite tab) and [guide-flow.md](guide-flow.md).

## Commands

Always routed to the Python engine (even when `SDLC_ENGINE=shell`):

```bash
./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db status
./scripts/sdlc.sh db path

./scripts/sdlc.sh db query --columns work_id,registry_status,jira_key,canvas_status
./scripts/sdlc.sh db query --status done --limit 20
./scripts/sdlc.sh db query --search "orchestration"
./scripts/sdlc.sh db query "SELECT work_id, jira_key FROM work_items WHERE has_canvas = 1"

./scripts/sdlc.sh db lookup --work-id FEAT-001-hello-live --json
./scripts/sdlc.sh db lookup --work-id FEAT-001-hello-live --markdown

./scripts/sdlc.sh db export --format json -o /tmp/sdlc-index.json
./scripts/sdlc.sh db export --format sql  -o /tmp/sdlc-index.sql
```

`db query` with raw SQL is **read-only** (single `SELECT` only).

## Session brief embedding

`start-agent-session.sh` soft-loads a **Local SQLite Index (query cache)** section into
the session brief when the Python engine is importable and a `--work-id` is set:

1. Rebuilds `.sdlc/index.sqlite` if missing (`db lookup` → `ensure`/`rebuild`).
2. Embeds `db lookup --work-id … --markdown` under the brief.
3. Mentions that section in the **Resume Prompt** so future agents treat it as
   loaded lookup context.

If the engine is unavailable, the section is omitted and session start still
succeeds. Markdown indexes (`context-index.md`, etc.) remain the primary
progressive-disclosure path; SQLite is an additional Work ID snapshot.

## Schema (v4 — full agent-context graph)

- `work_items` — one row per Work ID (title, statuses, Jira/GitHub, paths, registry)
- `artifacts` — canvas / requirement / feature / analysis / review / sync paths
- `local_sessions` — machine-private `LOCAL-*` sessions under `.sdlc/local-sessions/`
- `work_search` — FTS5 when available (else LIKE fallback)
- `meta` — schema version, rebuild time, source git commit
- Graph nodes: `requirements`, `canvases`, `areas`, `lessons`, `claims`,
  `context_sessions`, `pointers`, `context_entries`, `domain_keywords`,
  `phase_refs`, `project_facts` (+ join `work_areas`)
- `edges` — typed relationships (requirement/canvas/reasons/area/about/for_work/…)

Full graph contract + coverage gate:
[SPIKE-088](agent-context-cleanup/spikes/SPIKE-088-sqlite-v2.md)
(`LocalIndex.capability_coverage()`).

## Relationship to GUIDE

```
markdown + TSV (git, source of truth)
        │
        ▼ rebuild
  .sdlc/index.sqlite   ← you are here (local cache)
        │
        ▼ later (SPIKE-001)
  GUIDE / Neo4j        ← optional RAG / graph retrieval
```

Do not treat the SQLite file as authoritative. If it drifts, `db rebuild`.

## Ops console

Visual status + rebuild live in the ops console:

```bash
./scripts/sdlc.sh console --target .
```

Open the **SQLite** tab for counts, registry breakdown, and rebuild. The **Guide** tab
stores local Embabel Guide connection settings (gitignored under `.sdlc/guide-config.json`)
so you can stage SPIKE-001 config next to the SQLite cache.
