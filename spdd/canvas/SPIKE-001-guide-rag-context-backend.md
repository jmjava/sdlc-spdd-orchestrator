# REASONS Canvas: SPIKE-001-guide-rag-context-backend - Guide as a DICE hybrid context backend

## Metadata

- Work ID: SPIKE-001-guide-rag-context-backend
- Work Type: Spike
- Status: Draft
- Readiness: Needs Analysis
- Created: 2026-06-19
- Updated: 2026-06-19 (reframed around DICE domain-graph hybrid)
- Owner:
- Target Project: sdlc-spdd-orchestrator (self / dogfood)
- Stack: Bash + Markdown harness ↔ JVM (Embabel guide) + Neo4j graph + RAG, over MCP (SSE)
- Source System: Roadmap
- Roadmap: ROADMAP.md
- Milestone:
- Delivery stage: make it fast (optimization) — **spike, parked behind FEAT-004/005**
- Time-box: 1–2 focused sessions
- Related PR:

## R - Requirements

### User Goal

Find out whether a **DICE-style hybrid** retrieval over guide's Neo4j — combining our
existing lexical index, embedding discovery, and a typed **domain graph** — selects
better prompt context than today's markdown lookup, before committing to the dependency.

### Business / Product Goal

De-risk the make-it-fast retrieval direction with evidence. Produce a go / no-go
decision and, if go, the shape of the follow-on feature(s).

### Framing: the three retrieval legs (Domain-Integrated Context Engineering)

Per Rod Johnson's **DICE (Domain-Integrated Context Engineering)** — typed domain
objects, not generic chunks, should drive context. The SDLC-SPDD domain already exists
(Work ID, Operation, Canvas, REASONS sections, Decision, Pitfall, Pattern, code-area,
phase, metric Kind). The hybrid uses three complementary legs over one join key (the
domain model):

1. **Lexical/area index (current)** — deterministic, auditable, exact identifiers.
2. **Embedding discovery (guide RAG)** — synonym/paraphrase reach to find entry points.
3. **Domain graph (DICE)** — typed nodes + relationships in Neo4j (`WorkID —touches→ Area`,
   `Decision —about→ Area`, `Operation —in→ Canvas`); retrieve by following domain structure.
   **Verified 2026-06-19: this leg is fork work** — guide exposes no generic domain-graph
   traversal over MCP (only a code-structure signature graph; see Verification below).

### Hypothesis

A domain-graph-led hybrid (lexical + embedding + DICE relationships) surfaces more
relevant prior decisions, pitfalls, patterns, and canvases than markdown
`context-index.md` lookup, at comparable or lower context cost — while staying
auditable (retrieval explained by domain links, not opaque cosine).

### Decision Criteria (what "done" means)

- [ ] One real Work ID run across the modes: (a) current resolver, (b) embedding-only RAG, (c) DICE hybrid (graph + lexical + embedding).
- [ ] Outcomes compared on the FEAT-004 ledger (rework count, review-result) + approximate context tokens.
- [ ] Auditability check: can each included item be explained by a domain link / matched term (not just a similarity score)?
- [ ] Written go / no-go with trade-offs (retrieval value vs. JVM+Neo4j+domain-modeling cost).
- [ ] If go: a sketch of follow-on FEAT(s) — domain-graph schema, corpus/ingest wiring, retrieval seam, optional live write tool.

### Non-Goals

- No production integration; no required dependency; default markdown-first path unchanged.
- No new guide features beyond what a throwaway experiment needs.

### Assumptions

- guide can ingest arbitrary directories (`guide.directories` + `guide.git-ingestion`) — confirmed in its `DataManager.loadReferences()`.
- guide exposes semantic-search MCP tools (`docs_*`: `textSearch`, `vectorSearch`, `broadenChunk`, `zoomOut`) over its Neo4j `ContentElement` store — **confirmed live 2026-06-19**. It does **not** expose generic domain-graph traversal (that leg is fork work).
- Neo4j (guide's store) is a graph DB, so it can hold a DICE domain graph alongside RAG chunks — confirmed it is Neo4j.
- The SDLC-SPDD domain model is already implicit in our artifacts; the spike maps a minimal slice of it to typed nodes/edges, not the whole thing.
- FEAT-004 ledger is available as the scoreboard (or co-stubbed for the experiment).

### Open Questions

- Does retrieval plug in at the assistant layer (Cursor calls guide MCP mid-session) or via a resolver shim? (Lean: assistant layer.)
- Store-as-we-go via batch append-ingest of `agent-context/memory/` vs. a live `remember()` write tool in the fork?
- Minimal DICE domain slice worth modeling first (likely Work ID ↔ Area ↔ Decision/Pitfall/Pattern) vs. full model.
- ~~Does Embabel/guide already expose domain-graph retrieval, or is that fork work?~~ **Resolved 2026-06-19 (via guide MCP): fork work.** Built-in graph retrieval is code-specific (`embabel_agent_findClassSignature*`, `findPackageSignature`); there is no generic typed-domain traversal tool. The DICE leg must be built (Neo4j projection + a fork retrieval tool/agent).

### Verification (2026-06-19, against live guide MCP @ `:21337` + direct Neo4j query)

Exercised the actual MCP tool surface and the underlying Neo4j store:

- **Connectivity:** `helloBanner` → `Embabel Agent MCP SYNC Server 0.4.0-SNAPSHOT` (Cursor → mcp-remote → guide SSE works).
- **Tool surface:** lexical = `docs_docs_textSearch` (BM25/Lucene); embedding = `docs_docs_vectorSearch` (+ `broadenChunk`/`zoomOut` for progressive disclosure). Leg 3 (generic domain-graph traversal) is **not exposed** — only code-structure tools (`embabel_agent_findClassSignature*`, `findPackageSignature`). ⚠️ fork work.
- **Store contents (prior ingest is present — store is NOT empty):** `ContentElement` 13,562 · `Chunk` 9,503 · `Document` 1,465 (+ Section hierarchy). Corpus = the **`dice` project source** (`file:///…/jmjava/dice/src/main/kotlin/com/embabel/dice/…`) plus embabel repos (per the `menke` profile dirs).
- **Leg 1 (lexical) works against current data:** direct `db.index.fulltext.queryNodes('embabel-content-fulltext-index','embabel agent')` returns scored chunks. ✅
- **Leg 2 (embedding):** `embabel-content-index` (VECTOR on `Chunk.embedding`) is ONLINE with embeddings present. ✅
- **Leg 3 (domain/entity graph):** `__Entity__` fulltext+vector indexes are defined but `__Entity__` count = **0** — knowledge-graph layer is empty; no SDLC-SPDD (or any) domain graph in the store today.
- **⚠️ MCP retrieval is currently blocked by an index-name mismatch from the upstream sync, NOT by missing data:** existing indexes are `embabel-content-fulltext-index` / `embabel-content-index` (**hyphens**), but synced guide 0.4.0-SNAPSHOT / drivine 0.0.46 queries `embabel_content_fulltext_index` / `embabel_content_index` (**underscores**) — hence the `docs_*` tools error "no such index". Fix before any A/B: create indexes under the expected (underscore) names, or re-ingest with the current version so it names them itself.

## E - Entities

### Application Components

- guide (Embabel): RAG ingestion + `docs_*` semantic-search MCP tools, SSE at `http://localhost:21337/sse` (this instance; guide's in-app default port is 1337)
- Orchestrator memory: `agent-context/memory/`, `spdd/canvas/`, `spdd/analysis/`
- Cursor as the MCP client; FEAT-004 ledger as the measurement

### External Systems

- Neo4j (local docker compose `embabel-neo4j`, or Embabel Hub)

### Data / Persistence

- Neo4j `ContentElement` RAG store (chunks + ONNX embeddings)
- Reference corpus (curated reading) cataloged in `spdd/analysis/SPIKE-retrieval-reference-corpus.md`, ingested via guide profile `menke-2`
- DICE domain graph in the same Neo4j: typed nodes (WorkID, Area, Canvas, Operation, Decision, Pitfall, Pattern) + relationships
- Throwaway / local only for the spike

### Domain Entities (minimal DICE slice)

- WorkID, Area, Canvas, Operation, Decision, Pitfall, Pattern
- Relationships: `WorkID —touches→ Area`, `Decision/Pitfall/Pattern —about→ Area`, `Operation —in→ Canvas`, `WorkID —has→ Canvas`

## A - Approach

### Proposed Approach (experiment)

1. Stand up a local guide; set `guide.directories` to the orchestrator's `agent-context/memory/` (+ `spdd/`); run append-ingest (embedding leg).
2. Build a minimal DICE domain slice in the same Neo4j: project our existing index data (Work ID ↔ Area ↔ Decision/Pitfall/Pattern, Canvas, Operation) into typed nodes/edges (domain-graph leg).
3. Connect Cursor to guide's MCP SSE endpoint; confirm both semantic search and domain-graph traversal return relevant orchestrator memory.
4. Pick one real Work ID. Run a plan/coding session across modes: (a) today's lexical resolver, (b) embedding-only RAG, (c) DICE hybrid (graph-led + lexical + embedding).
5. Record each on the FEAT-004 ledger (rework, review-result) + approximate context tokens, and check auditability (every included item explainable by a domain link/term).
6. Write the go / no-go with trade-offs; if go, sketch the follow-on FEAT(s) including the domain-graph schema.

### Alternatives Considered

- Stay markdown-first only (the no-go baseline).
- Live `remember()` write tool now (deferred — only if the spike says go).

### Risks

- Embabel MCP / Hub setup friction (the server has errored before — verify connection first).
- Small-sample A/B is indicative, not conclusive — treat as directional evidence.

## S - Structure

### Files To Add

- A short findings note (e.g. `spdd/analysis/SPIKE-001-guide-rag-context-backend-analysis.md`) capturing setup, the A/B, and the recommendation.

### Files To Modify

- None in the framework (spike is exploratory; no production wiring).

### Documentation Structure

- Findings + decision recorded in the analysis note and this canvas's Sync Notes.

## O - Operations

### T01 - Stand up guide + ingest orchestrator memory (embedding leg)

- Status: Not Started
- Description: Local guide instance; point `guide.directories` at orchestrator memory; append-ingest; verify store stats.
- Files: (guide config; no orchestrator changes)
- Validation: Ingestion summary shows orchestrator memory loaded

### T02 - Build a minimal DICE domain slice in Neo4j (domain-graph leg)

- Status: Not Started
- Description: Project existing index data into typed nodes/edges (Work ID ↔ Area ↔ Decision/Pitfall/Pattern, Canvas, Operation); confirm graph traversal returns linked context.
- Files: (Neo4j load script / queries; no orchestrator changes)
- Validation: Domain query returns items linked to a known Work ID/area

### T03 - Connect Cursor to guide MCP + sanity retrieval (both legs)

- Status: Not Started
- Description: Link guide's SSE MCP into Cursor; confirm semantic search and domain-graph traversal both return relevant orchestrator memory.
- Files: (Cursor MCP config)
- Validation: Relevant results for a known Work ID/area via each leg

### T04 - Compare modes on one real Work ID and record on the ledger

- Status: Not Started
- Description: Run a session across (a) lexical resolver, (b) embedding-only, (c) DICE hybrid; capture rework/review-result/tokens + auditability.
- Files: spdd/analysis/SPIKE-001-guide-rag-context-backend-analysis.md
- Validation: All modes recorded; metrics comparable

### T05 - Write go / no-go recommendation

- Status: Not Started
- Description: Summarize evidence + trade-offs; if go, sketch follow-on FEAT(s) including the domain-graph schema.
- Files: spdd/analysis/SPIKE-001-guide-rag-context-backend-analysis.md, this canvas Sync Notes
- Validation: Clear decision with rationale

## N - Norms

### General

- Time-boxed: stop at the decision, do not slide into building the integration.
- No production dependency added during the spike.
- Markdown-first default path stays intact.

## S - Safeguards

- This is exploratory: do not wire guide into the default resolver or installers under this Work ID.
- Keep all Neo4j/guide setup local/throwaway; no secrets committed.
- If the spike says "go", the real integration is a separate FEAT with its own canvas.
- Posture/optimization framing stays internal; nothing ships to target projects from this spike.

## Review Checklist

- [ ] Question answered with evidence
- [ ] Decision criteria met
- [ ] Trade-offs documented
- [ ] Go / no-go recorded
- [ ] Follow-on FEAT(s) sketched if go
- [ ] No production wiring left behind
- [ ] No secrets committed

## Sync Notes

Spike to de-risk the make-it-fast retrieval direction via a **DICE (Domain-Integrated
Context Engineering)** hybrid over guide/Neo4j: lexical index + embedding discovery +
typed domain graph, with the domain model as the shared join key. Converges with the
Embabel GOAP idea: guide/Neo4j = retrieval substrate, the DICE domain graph = structure,
FEAT-004 ledger = scoreboard, GOAP = optional selection policy. Keeps retrieval
auditable (domain links, not opaque similarity). Record the decision here.

## Final Status

- Status:
- Completed Date:
- PR:
- Follow-Up Tasks:
