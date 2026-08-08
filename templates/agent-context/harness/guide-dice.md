# Guide DICE context backend (optional)

endpoint: http://localhost:21337

The presence of this file opts this install into the Guide DICE backend: a
Neo4j entity graph (WorkId, Canvas, Area, Operation, Decision, Pitfall,
Pattern connected by typed edges) served by an
[Embabel Guide](https://github.com/embabel/guide) instance, populated from
this repo's SPDD markdown by the projection API.

Presence of this file is **not** a promise that Guide is running. Resolution
is always two-step and happens at runtime:

```bash
./sdlc-spdd/scripts/resolve-context-backend.sh --target .
# CONTEXT_BACKEND=guide-dice  → Guide is live; augment with the tools below
# CONTEXT_BACKEND=files       → use ledger retrieval only (normal, not an error)
```

The committed lessons ledger (`spdd/memory/lessons.jsonl`, queried via
`sdlc-engine context retrieve`) remains the baseline either way; DICE augments
it, it never replaces it. No SDLC-SPDD command may fail because Guide is
absent or down.

## When live, prefer these for retrieval

| MCP tool | HTTP equivalent | Use |
|---|---|---|
| `spdd_workSubgraph` | `GET /api/v1/data/spdd-projection/work/{workId}` | Canvas, areas, decisions, pitfalls, patterns for the active Work ID |
| `spdd_areaLessons` | `GET /api/v1/data/spdd-projection/area?name={area}` | Cross-run lessons before touching a code area |
| `spdd_findByLabel` | — | List entities of one label (capped) |
| `spdd_projectionStats` | `GET /api/v1/data/spdd-projection/stats` | Sanity-check projection freshness |

## Keeping the graph current (persist side)

After retro/sync accepts staged lessons into the ledger, re-project so the
next run retrieves fresh entities:

```bash
./sdlc-spdd/scripts/resolve-context-backend.sh --target . --project --work-id <WORK-ID>
```

This is a no-op (exit 0) when Guide is not reachable.

## Configuration

- `endpoint:` line above — base URL of the Guide instance for this install.
- `GUIDE_BASE_URL` / `GUIDE_PORT` env vars override the endpoint at runtime.
- To disable DICE for this install, delete this file.
