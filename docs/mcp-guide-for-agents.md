# Guide MCP for Cursor and Copilot

When Guide is running locally, agents can retrieve SPDD context two ways:

## 1. Native MCP (preferred in IDE)

Connect the IDE MCP client to Guide SSE:

```bash
./scripts/guide/mcp-config-snippet.sh --cursor
# Merge JSON into Cursor Settings → MCP
```

Default endpoint: `http://localhost:21337/sse` (override with `GUIDE_PORT`).

| MCP tool | Use |
|----------|-----|
| `spdd_workSubgraph` | Canvas + lessons for active Work ID |
| `spdd_areaLessons` | Cross-run lessons for a code area |
| `spdd_findByLabel` | List entities by label (capped) |
| `spdd_projectionStats` | Projection freshness counts |
| `spdd_getLesson` | Full untruncated lesson body by id |

After retro/sync, re-project:

```bash
./sdlc-spdd/scripts/resolve-context-backend.sh --target . --project --work-id <WORK-ID>
```

## 2. CLI delegation (when MCP is not wired)

Same payloads via HTTP — use in agent prompts or terminal:

```bash
# Human-readable (good for chat paste)
./scripts/guide/query-guide.sh --text --work-id FEAT-001-order-status-api

# JSON (scripting)
SDLC_ENGINE=python ./scripts/sdlc.sh context guide-query --work-id FEAT-001-order-status-api

# Explicit MCP tool call
SDLC_ENGINE=python ./scripts/sdlc.sh context mcp-call \
  --tool spdd_getLesson \
  --json '{"id":"pitfall:FEAT-001:engine:retro"}'
```

## Agent instruction (paste into prompts)

When `agent-context/harness/guide-dice.md` is present and Guide is live:

1. Prefer native `spdd_*` MCP tools if connected to `/sse`.
2. Otherwise run: `./scripts/guide/query-guide.sh --text --work-id <WORK-ID>`.
3. For one lesson body: `spdd_getLesson` or `--lesson-id <id>`.
4. Never bulk-read `spdd/memory/lessons.jsonl` when Guide is up.

## CI round-trip gate

```bash
SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh
.venv/bin/pytest -q engine/tests_e2e/test_guide_projection_roundtrip.py
```

Validates: ledger lesson → projection load → HTTP/MCP read → parity.
