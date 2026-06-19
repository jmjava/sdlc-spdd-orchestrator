# SPIKE-001 — Confirmational Research (2026-06-19)

Design verification against the live guide MCP store (`:21337`) and Embabel/DICE
code corpus. Purpose: validate the **spike design** before ingesting orchestrator
memory or running the A/B — not merely confirm URLs are present.

Related: `spdd/canvas/SPIKE-001-guide-rag-context-backend.md`

## Method

- Live MCP: `helloBanner`, `docs_textSearch`, `docs_vectorSearch`, `broadenChunk`,
  `embabel_agent_findClassSignatureBySimpleName`
- Direct Neo4j queries for index state, entity counts, embedding model
- Corpus: menke code repos (~1,416 docs) + menke-2 reference URLs (24 docs);
  9,664 chunks; all `all-MiniLM-L6-v2` (384-dim)

## Design claims — verdicts

| Claim | Verdict | Evidence from store |
|-------|---------|---------------------|
| Three-leg hybrid (lexical + embedding + domain graph) is sound | **Confirmed** | `SearchOperations` exposes `chunkFullTextSearch`, `chunkSimilaritySearch`, `entityFullTextSearch`, `queryForEntities`; RAG literature in corpus advocates combining strategies |
| Neo4j dual role (vector + graph) | **Confirmed** | DICE docs: chunks for RAG + proposition/entity graph in same DB |
| MCP exposes legs 1–2 only; leg 3 is fork work | **Confirmed** | MCP: `docs_*` + code signatures only; no typed-domain traversal tool |
| Assistant-layer retrieval (Cursor → MCP mid-session) | **Confirmed** | Context-engineering corpus treats retrieval as per-turn pipeline; MCP as agent tool surface |
| FEAT-004 ledger / evals as scoreboard | **Confirmed** | Hamel evals corpus: error analysis, binary pass/fail; generic similarity insufficient for product evals |
| GOAP as optional policy on top of retrieval | **Confirmed** | Embabel agent docs: GOAP/A* planner, goals/actions/conditions — native, not wired to guide MCP retrieval |
| Hybrid beats markdown lookup (hypothesis) | **Plausible, unproven** | Fowler SPDD + context-engineering corpus validate the problem; A/B still required |
| Auditability via domain links, not cosine | **Partial** | DICE `Memory` API supports structured/confidence queries; embedding leg alone is opaque — legs 1+3 must justify inclusions |
| DICE leg = SDLC-SPDD domain graph | **Refined** | Store DICE = proposition memory (conversation → entities), not WorkID/Canvas — reuse **projection pattern**, custom domain slice |
| Batch append-ingest for spike | **Confirmed lean** | Matches `DataManager`; DICE also has live proposition extraction — defer for spike |
| Index-name mismatch blocked MCP | **Resolved** | Fresh re-ingest: `embabel_content_fulltext_index` / `embabel_content_index` ONLINE (underscore) |

## MCP spot-checks (design-relevant queries)

| Query | Leg | Result |
|-------|-----|--------|
| SPDD / REASONS canvas | text | Fowler article, mgks.dev `/spdd-*` workflow — strong |
| Context engineering + evals | vector | Sourcegraph guide, Henry Vu FAQ, four-pillars framing — strong |
| DICE domain graph | vector | Proposition extraction, graph projection pipeline — code/docs, not SDLC-SPDD graph |
| GOAP + retrieval | vector | Embabel planning module (GOAP/A*), RAG reference docs |
| Orchestrator Work IDs (FEAT-004) | vector | **No hits** — expected until orchestrator memory ingest (T01) |
| Decision memory (Fowler via broadenChunk) | broaden | SPDD "decision memory" + "raising automation ratio" — aligns with spike goals |

## Leg 3 state

- `__Entity__` count: **0** (indexes defined, no populated knowledge graph)
- Entity vector write path in code: noted as not yet populated in some repositories
- Fork work unchanged: project SDLC-SPDD slice (WorkID ↔ Area ↔ Canvas ↔ Operation)

## Embabel repo convention review (2026-06-19)

Source review of ingested repos (`dice`, `embabel-agent-rag`, `embabel-agent-rag-neo-drivine`)
plus MCP corpus queries. Recorded in `SPIKE-001-dice-entity-schema.md` §Embabel convention alignment.

| Convention check | Result |
|------------------|--------|
| `NamedEntity` contract (`id`, `name`, `description`) | ✅ Adopted |
| Label = class simple name + `__Entity__` | ✅ Adopted — dropped `Spdd*` prefix |
| `DataDictionary.fromClasses` / `dataDictionaryFromPackages` | ✅ Adopted |
| `@Semantics` on properties for graph rel types | ✅ Adopted — property name = rel type |
| `NamedEntityDataRepository` persist path | ✅ Adopted for T03 |
| Proposition extraction pipeline for ingest | ❌ Rejected — wrong path for structured markdown |
| `SimpleNamedEntityData` spike shortcut | ⚠️ Prototype only; Kotlin classes preferred |

## Design refinements recorded

1. Leg 3 = custom SDLC-SPDD Neo4j projection using DICE patterns, not DICE proposition schema.
2. **Leg 3 requires explicit DICE entity design** — `SPIKE-001-dice-entity-schema.md`; Embabel convention review done; use `WorkId` not `SpddWorkId`.
3. Dual ingest: RAG chunks (leg 2) + entity projection (leg 3); directory ingest alone leaves `__Entity__` empty.
4. Auditability criterion: embedding leg for **discovery**; lexical + graph for **justification**.
5. GOAP is a selection policy layer, not a retrieval substitute.
6. Orchestrator memory ingest is for the **experiment**, not for validating the architecture.

## Still open (requires experiment)

- Finalize `Spdd*` entity schema (T02) and projection ingest (T03)
- A/B on one real Work ID across (a) lexical resolver, (b) embedding-only, (c) hybrid
- Fork domain-query MCP tool wrapping `SearchOperations` entity APIs
- GOAP wiring (optional, post-spike)
