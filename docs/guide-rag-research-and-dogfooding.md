# Guide RAG Research and Dogfooding

How this repository uses [Embabel Guide](https://github.com/embabel/guide) and Neo4j as a
**local research backend** during SPDD analysis, and how the orchestrator dogfoods its own
workflow while improving itself.

This page is for **framework contributors** working in `sdlc-spdd-orchestrator`. Target
projects that install SDLC-SPDD do **not** receive Guide profiles, Neo4j data, or MCP wiring —
only the resulting docs, scripts, and templates.

## Why Guide?

During `/sdlc-spdd-analysis`, agents need grounded context from external references (docgen
API, course-builder patterns, SPDD articles, context-engineering reading) without pasting
large documents into every prompt.

Guide ingests curated URLs and local directories into a Neo4j graph with full-text and vector
search. The **embabel-dev MCP** server (`docs_vectorSearch`, `docs_textSearch`) exposes that
corpus to Cursor mid-session so analysis artifacts can cite retrieved chunks instead of memory.

Architecture and experiment design: [SPIKE-001 canvas](../spdd/canvas/SPIKE-001-guide-rag-context-backend.md).
Reference URL catalog: [SPIKE retrieval corpus](../spdd/analysis/SPIKE-retrieval-reference-corpus.md).

## Corpus layers (append, do not wipe)

Profiles live under `~/github/jmjava/guide/scripts/user-config/`. Each profile is an
**append** pass on the same Neo4j store. Run **one ingest at a time** on port `21337`.

| Profile | Purpose | Key content |
|---------|---------|-------------|
| `menke` | Code half of corpus | Local Embabel/DICE fork repos |
| `menke-2` | Reference reading | SPDD, context engineering, evals URLs (~24 docs) |
| `menke-3` | Framework depth | Shell, task runners, VS Code manifests, harness, craft, RAG |
| `menke-4` | Docgen consumer | `documentation-generator/src` + course-builder text `docs/` paths |

Example (menke-4 on top of prior passes):

```bash
cd ~/github/jmjava/guide
GUIDE_PROFILE=menke-4 GUIDE_PORT=21337 SERVER_PORT=21337 \
  GUIDE_INGEST_LOG=/tmp/menke-4-ingest.log ./scripts/append-ingest.sh
```

Confirm startup log: `Starting Guide with profiles: menke-4`. Wait for ingest completion
before relying on MCP search.

Config files (local only, not checked into this repo):

- `application-menke.yml`
- `application-menke-2.yml`
- `application-menke-3.yml`
- `application-menke-4.yml`

## MCP research during analysis

1. Ensure Guide is running on `:21337` with the corpus that covers your Work ID.
2. Connect **embabel-dev MCP** in Cursor.
3. During `/sdlc-spdd-analysis`, query for domain concepts and exact CLI flags:

   | Need | Tool | Example query |
   |------|------|---------------|
   | Concepts, patterns | `docs_vectorSearch` | `docgen yaml-generate hints narration_from_source` |
   | Exact flags, paths | `docs_textSearch` | `+setup-docgen-venv +docgen-engine.path` |
   | SPDD method | `docs_vectorSearch` | `SPDD REASONS canvas workflow` |

4. Record findings in `spdd/analysis/<WORK-ID>-analysis.md` with citations to retrieved
   chunk titles/URIs.
5. Run `./scripts/sdlc-spdd/index-spdd-analysis.sh --target . --work-id <WORK-ID>` so
   keywords feed decision-memory indexes.

Starter queries by Work ID theme:

- **Docgen / narrated docs:** `docgen init yaml-generate`, `hints project-context`
- **Retrieval spikes:** `context engineering evals hybrid retrieval`
- **Framework scripts:** `setup-agent-prompts validate-command-adapters`

## Dogfooding on this repo

`sdlc-spdd-orchestrator` is the framework **and** its first customer:

| Layer | What we dogfood | Where it shows up |
|-------|-----------------|-------------------|
| **SPDD workflow** | Requirements → canvas → analysis → plan → architect → code | `requirements/milestones/`, `spdd/canvas/`, `spdd/analysis/` |
| **Docgen toolchain** | `documentation-generator` + `docs/demos/` bundle | [CHORE-001](../spdd/canvas/CHORE-001-docgen-initial-documentation.md); `scripts/setup-docgen-venv.sh` |
| **Guide RAG** | Layered `menke-*` profiles + MCP during analysis | This doc; SPIKE-001 |
| **Posture guard** | Shipped `templates/` stay free of internal dev language | `scripts/check-posture-boundary.sh` |

Work IDs for framework self-improvement are tracked in [milestone-1.md](../milestone-1.md)
and [ROADMAP.md](../ROADMAP.md). That planning narrative stays in this repo — it does not
install into target applications.

### Example: CHORE-001 (docgen initial documentation)

1. Ingest menke-4 (docgen source + course-builder docs patterns).
2. `/sdlc-spdd-analysis` with MCP queries for `yaml-generate`, hints, bootstrap scripts.
3. Analysis artifact: `spdd/analysis/CHORE-001-docgen-initial-documentation-analysis.md`.
4. Plan → architect → code operations scaffold `docs/demos/` and this operator doc.

The docgen library intentionally has **no in-repo dogfood bundle**; consumer repos
(course-builder, then this orchestrator) are the integration test. See
[documentation-generator](https://github.com/jmjava/documentation-generator) README.

## What not to ship to target projects

| Artifact | Stays local / orchestrator-only |
|----------|----------------------------------|
| Guide `application-menke-*.yml` profiles | Yes |
| Neo4j data directory | Yes |
| embabel-dev MCP server config | Yes |
| `.venv/` + `scripts/docgen-engine.path` | Yes (orchestrator dev) |
| `docs/demos/` regenerable outputs (`audio/`, `media/`, `recordings/`) | Gitignored |
| `spdd/analysis/` research notes | Orchestrator repo only |

Target projects receive: `templates/`, install scripts, `docs/sdlc-spdd/` hub, and whatever
docs/scripts result from completed chores — never the research graph or ingest configs.

## Related docs

| Doc | Role |
|-----|------|
| [SPIKE-001 canvas](../spdd/canvas/SPIKE-001-guide-rag-context-backend.md) | DICE hybrid retrieval architecture (experiment) |
| [SPIKE retrieval corpus](../spdd/analysis/SPIKE-retrieval-reference-corpus.md) | menke-2 URL catalog |
| [Context loading and scaling](context-loading-and-scaling.md) | Tier-1 vs on-demand agent context |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Orchestrator vs target paths; posture boundary |
| [Workflow](workflow.md) | Step 5: `/sdlc-spdd-analysis` in the 15-step sequence |

## Narrated demos (docgen)

After [CHORE-001](../spdd/canvas/CHORE-001-docgen-initial-documentation.md) lands, the
docgen bundle lives at `docs/demos/`. Bootstrap:

```bash
./scripts/setup-docgen-venv.sh
source .venv/bin/activate
cd docs/demos
docgen --config docgen.yaml --help
```

See `docs/demos/README.md` for the full operator guide (created as part of the same chore).
