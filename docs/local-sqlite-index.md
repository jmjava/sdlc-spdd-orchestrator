# Local SQLite index (opt-in cache)

An **optional**, fully regenerable local query cache at `.sdlc/index.sqlite`
(gitignored, schema **v5**). Uses Python's stdlib `sqlite3` — no database
server. It is a pure projection of the committed ledger and contract files:
one write path, rebuilt on demand, never a source of truth.
See [Storage v3](storage-v3.md) for the full model.

## What it is / is not

| Is | Is not |
|----|--------|
| Opt-in cache under `.sdlc/index.sqlite` (gitignored) | A default backend — enable via `CONTEXT_BACKENDS` |
| Fast local `SELECT` / full-text over ledger, registry, canvases | The working store — that is the [Guide DICE graph](guide-flow.md) |
| Rebuilt any time from `spdd/memory/lessons.jsonl` + `registry.jsonl` + contracts | Something you commit, merge, or sync between machines |
| Optional JSON/SQL export for inspection | A replacement for the committed JSONL system of record |

**Multi-user sync stays git:** the lessons ledger, registry events, canvases,
and milestone requirements. Each machine rebuilds its own SQLite file.

## Enabling

Add `sqlite` to the backend set (default is git + guide):

```bash
export CONTEXT_BACKENDS=git-pointers,guide-dice,sqlite
# or set "backends" in .sdlc/persistence-config.json
```

When enabled, `capture` / `accept` keep the cache in sync automatically, and
`sdlc-engine context parity [--repair]` verifies it against the ledger.

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

`start-agent-session.sh` soft-loads a **Local SQLite Index (query cache)**
section into the session brief when the Python engine is importable and a
`--work-id` is set. If the engine (or the cache) is unavailable, the section is
omitted and session start still succeeds — the ledger digest and on-demand
retrieval (`sdlc-engine context retrieve|show|digest`) are the primary path;
SQLite is an extra Work ID snapshot.

## Schema (v5)

- `work_items` — one row per Work ID (title, statuses, Jira/GitHub, paths, registry)
- `lessons` — ledger records (accepted + staged flag), rebuilt from
  `spdd/memory/lessons.jsonl` and `.sdlc/staged/lessons.jsonl`
- `claims` — registry state derived from `spdd/memory/registry.jsonl`
- `artifacts` — canvas / requirement / analysis / review / sync paths
- `local_sessions` — machine-private `LOCAL-*` sessions under `.sdlc/local-sessions/`
- `work_search` — FTS5 when available (else LIKE fallback)
- `meta` — schema version, rebuild time, source git commit
- Graph nodes + typed `edges` (work / requirement / canvas / area / lesson /
  keyword; relations like `canvas`, `reasons`, `area`, `about`,
  `recorded_for`) — aligned with the Guide DICE edge names

## Relationship to Guide

Both are projections of the same ledger — see the
[parity diagram](diagrams/08-projection-parity.svg):

- **Guide DICE graph** — the working store; cross-work retrieval, MCP tools,
  RAG legs. Default backend when reachable.
- **SQLite** — local, offline, zero-install convenience queries. Opt-in.

Do not treat the SQLite file as authoritative. If it drifts:
`./scripts/sdlc.sh db rebuild` or `sdlc-engine context parity --repair`.

## Ops console

Visual status + rebuild live in the ops console:

```bash
./scripts/sdlc.sh console --target .
```

Open the **SQLite** tab for counts, registry breakdown, rebuild, and a
filterable work browser. Click a Work ID to read the requirement / canvas /
analysis from git (`POST /api/sqlite/work`); the cache is only the index.
The **Guide** tab stores local Guide connection settings (gitignored under
`.sdlc/guide-config.json`). See [ops-console.md](ops-console.md).
