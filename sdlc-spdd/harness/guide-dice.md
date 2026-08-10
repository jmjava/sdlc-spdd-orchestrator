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
./scripts/resolve-context-backend.sh --target .
# CONTEXT_BACKEND=guide-dice  → Guide is live; augment with the tools below
# CONTEXT_BACKEND=files       → use the file-based indexes only (normal, not an error)
```

The committed lessons ledger (`spdd/memory/lessons.jsonl`) and on-demand
`sdlc-engine context retrieve` remain the baseline either way; DICE augments
them, it never replaces them. No SDLC-SPDD command may fail because Guide is
absent or down.

## When live, prefer these for retrieval

| MCP tool | HTTP equivalent | Use |
|---|---|---|
| `spdd_workSubgraph` | `GET /api/v1/data/spdd-projection/work/{workId}` | Canvas, areas, decisions, pitfalls, patterns for the active Work ID |
| `spdd_areaLessons` | `GET /api/v1/data/spdd-projection/area?name={area}` | Cross-run lessons before touching a code area |
| `spdd_findByLabel` | — | List entities of one label (capped) |
| `spdd_projectionStats` | `GET /api/v1/data/spdd-projection/stats` | Sanity-check projection freshness |
| `spdd_getLesson` | `GET /api/v1/data/spdd-projection/lesson/{id}` | Full untruncated lesson body |

## CLI delegation (Cursor / Copilot without MCP wired)

When native MCP is unavailable, agents **must** use the same tools via CLI:

```bash
./scripts/guide/query-guide.sh --text --work-id <WORK-ID>
./scripts/guide/query-guide.sh --area engine/tests
SDLC_ENGINE=python ./scripts/sdlc.sh context mcp-call --tool spdd_getLesson --json '{"id":"<lesson-id>"}'
```

MCP config snippet: `./scripts/guide/mcp-config-snippet.sh --cursor`  
Details: [docs/mcp-guide-for-agents.md](../../docs/mcp-guide-for-agents.md)

## Keeping the graph current (persist side)

After retro/sync updates the markdown artifacts, re-project so the next run
retrieves fresh entities:

```bash
./scripts/resolve-context-backend.sh --target . --project --work-id <WORK-ID>
```

This is a no-op (exit 0) when Guide is not reachable.

## Configuration

- `endpoint:` line above — base URL of the Guide instance for this install.
- `GUIDE_BASE_URL` / `GUIDE_PORT` env vars override the endpoint at runtime.
- To disable DICE for this install, delete this file.
