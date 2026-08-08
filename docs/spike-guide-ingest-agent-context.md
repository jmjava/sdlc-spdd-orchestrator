# SPIKE — Guide ingest for agent-context store

> **Historical T01 operator notes** (menke-5 / early spike branches).  
> **Current on `main`:** [Guide flow](guide-flow.md), [DICE projection runbook](dice-projection-runbook.md)
> (Guide tag `sdlc-spdd-projection-v2`), and [ops console](ops-console.md) Guide tab.  
> **Canonical analysis:** `spdd/analysis/SPIKE-001-guide-rag-context-backend-analysis.md`

Original exploration for [SPIKE-001](../spdd/canvas/SPIKE-001-guide-rag-context-backend.md)
**T01**: ingest orchestrator `agent-context/` and `spdd/` into Guide/Neo4j
(leg 2 — RAG chunks) so MCP search can reach Work IDs and analysis artifacts.

Target projects still never receive Guide profiles or Neo4j data — only the optional
`guide-dice` harness marker when installed with `--with-guide`.

## Guide branches (pair with this orchestrator spike)

| Leg | Guide branch | What it adds |
|-----|--------------|--------------|
| **2 — RAG chunks** | `ingest-to-hub` | Git incremental ingest + operator purge API |
| **3 — DICE projection** | `cursor/spike-spdd-dice-projection-17f4` | `POST /api/v1/data/spdd-projection/load` → `__Entity__` |

For the full SPIKE-001 experiment (legs 2 + 3), use the **leg 3 spike branch** — it includes
`ingest-to-hub` plus SPDD entity projection. **Not** the DICE proposition pipeline
(conversation → propositions).

```bash
cd ~/github/jmjava/guide
git fetch origin cursor/spike-spdd-dice-projection-17f4
git checkout cursor/spike-spdd-dice-projection-17f4
```

Copy `scripts/user-config/application-menke-5-spdd-projection.yml.example` →
`application-menke-5.yml` (enables `guide.spdd-projection.enabled: true` alongside menke-5
directories).

Leg 2 only (no entity graph): stay on `ingest-to-hub` without `spdd-projection.enabled`.

MCP is bundled with Guide on the same process (`/sse` on `GUIDE_PORT`, default `1337`; this
repo's research stack uses `21337` to avoid clashing with other local services).

## Corpus layering (append, do not wipe)

| Profile | Layer | Content |
|---------|-------|---------|
| `menke` | Code | Local Embabel/DICE fork repos |
| `menke-2` | Reference | SPDD, context engineering, evals URLs |
| `menke-3` | Framework depth | Scripts, manifests, harness, craft |
| `menke-4` | Docgen consumer | documentation-generator + course-builder docs |
| **`menke-5`** | **Orchestrator context** | `agent-context/memory/`, `spdd/canvas/`, `spdd/analysis/` |

Run **one profile at a time** on the same Neo4j store. See
[guide-rag-research-and-dogfooding](guide-rag-research-and-dogfooding.md) for menke-1–4.

## One-time setup

1. Ensure menke-1–4 (or the subset you need) are already ingested on port `21337`.
2. Copy the profile template into guide (paths are gitignored in guide):

   ```bash
   cp templates/guide-profiles/application-menke-5-orchestrator-context.yml.example \
      ~/github/jmjava/guide/scripts/user-config/application-menke-5.yml
   ```

3. Edit `application-menke-5.yml` if your orchestrator clone is not at
   `~/github/jmjava/sdlc-spdd-orchestrator`.

## Append ingest (leg 2)

From the orchestrator repo (this spike branch):

```bash
./scripts/guide/append-orchestrator-context.sh
```

Or manually from guide:

```bash
cd ~/github/jmjava/guide
GUIDE_PROFILE=menke-5 GUIDE_PORT=21337 SERVER_PORT=21337 \
  GUIDE_INGEST_LOG=/tmp/menke-5-ingest.log ./scripts/append-ingest.sh
```

Wait for the **INGESTION COMPLETE** banner. First run ingests the full trees; subsequent
appends with `git-ingestion.enabled` only process changed files (for example after
`sdlc.sh capture` updates `agent-context/memory/`).

### Re-ingest one directory after a bad partial run

With Guide running on `:21337`:

```bash
curl -s -X POST http://localhost:21337/api/v1/data/git-ingestion/revision/reset \
  -H 'Content-Type: application/json' \
  -d '{"directory":"~/github/jmjava/sdlc-spdd-orchestrator/agent-context/memory"}' | jq .
```

Then re-run `append-orchestrator-context.sh`.

## Verify MCP (legs 1–2)

Connect **embabel-dev MCP** in Cursor to `http://localhost:21337/sse`.

| Check | Tool | Example query |
|-------|------|---------------|
| Work ID in store | `docs_vectorSearch` | `SPIKE-001 guide RAG context backend` |
| Index rows | `docs_textSearch` | `+context-index +agent-context/memory` |
| Canvas prose | `docs_vectorSearch` | `FEAT-004 prompt optimization ledger` |
| Prior decision memory | `docs_vectorSearch` | `decision memory Fowler SPDD` |

**Before menke-5:** orchestrator Work IDs return no hits (confirmed in SPIKE-001 research).
**After menke-5:** expect hits on `spdd/canvas/SPIKE-001-*.md`, `agent-context/memory/context-index.md`,
and analysis files under `spdd/analysis/`.

Record spot-check results in
`spdd/analysis/SPIKE-001-guide-ingest-agent-context-exploration.md`.

## Leg 3 — entity projection (structured markdown → `__Entity__`)

After Guide runs on the leg 3 spike branch with `spdd-projection.enabled: true`:

```bash
# From orchestrator repo (defaults to repo root; pass fixture path for T07)
./scripts/guide/project-spdd-entities.sh
./scripts/guide/project-spdd-entities.sh examples/retrieval-fixture
```

Expect non-zero entity counts from `GET /api/v1/data/spdd-projection/stats`. Re-run after
`sdlc.sh capture` updates `context-index.md` or canvases. Leg 2 append-ingest is independent.

See `spdd/analysis/SPIKE-001-dual-ingest-model.md` and guide `docs/spdd-projection-ingest.md`.

## Verify setup (T01 + T07)

```bash
./scripts/guide/verify-spike-guide-setup.sh
./tests/test-retrieval-fixture-resolver.sh
```

## T05 A/B fixture drill

```bash
# Mode (a) resolver baseline
./scripts/guide/run-retrieval-ab-fixture.sh --capture-a

# Mode (b) after menke-fixture MCP queries — save URIs, then:
./scripts/guide/run-retrieval-ab-fixture.sh --check-mcp path/to/mcp-results.tsv
```

Record metrics in `spdd/analysis/SPIKE-001-retrieval-ab-ledger.md`.

## What this spike does not cover

- **DICE proposition pipeline** — conversation → propositions; wrong ingest for REASONS canvases.
  Leg 3 uses structured markdown projection instead (`SPIKE-001-dual-ingest-model.md`).
- **MCP domain-graph traversal (leg 3 retrieval)** — T04 fork; projection load is T03.
- **Production wiring** — no changes to `resolve-agent-context.sh` or default installers.
- **A/B vs markdown resolver** — T05; run after ingest is stable.

## Related

| Doc | Role |
|-----|------|
| [SPIKE-001 canvas](../spdd/canvas/SPIKE-001-guide-rag-context-backend.md) | Full hybrid retrieval experiment |
| [Dual ingest model](../spdd/analysis/SPIKE-001-dual-ingest-model.md) | Leg 2 RAG + leg 3 projection coexistence |
| [guide-rag-research-and-dogfooding](guide-rag-research-and-dogfooding.md) | menke-1–4 operator guide |
| [Context loading and scaling](context-loading-and-scaling.md) | Tier-1 vs on-demand markdown path (baseline) |
