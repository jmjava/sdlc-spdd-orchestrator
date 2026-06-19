# SPIKE-001 — SDLC-SPDD DICE Entity Schema (draft)

Typed domain entities for leg 3 (domain-graph retrieval) over guide/Neo4j. Validated
against Embabel conventions in `dice/`, `embabel-agent-rag`, and `embabel-agent-rag-neo-drivine`
(ingested in menke corpus + source review 2026-06-19).

Related: `spdd/canvas/SPIKE-001-guide-rag-context-backend.md` (T02 design, T03 ingest)

## Embabel convention alignment (T02 gate)

Reviewed against upstream patterns — not just MCP spot checks.

| Embabel convention | Source | Our design |
|--------------------|--------|------------|
| Entities implement `NamedEntity` (`id`, `name`, `description` required) | `embabel-agent-rag/.../NamedEntity.kt` | ✅ All types implement `NamedEntity` |
| Neo4j label = class simple name + `__Entity__` super-label | `NamedEntityData.ENTITY_LABEL`, `SimpleNamedEntityData` | ✅ Use `WorkId`, `Canvas`, … not `SpddWorkId` prefix labels |
| Schema via `DataDictionary.fromClasses("sdlc-spdd", …)` or `NamedEntity.dataDictionaryFromPackages(...)` | `dice/README.md`, `NamedEntity.dataDictionaryFromPackages` | ✅ Package `com.embabel.spdd.domain` (guide fork module) |
| Relationships via typed properties + `@Semantics(predicate=…)` — **property name becomes Neo4j rel type** | `RelationBasedGraphProjector.kt`, `dice/README.md` §Relations | ✅ Prefer reference properties (`canvas`, `area`, `workId`) over ad-hoc `HAS_*` edge names |
| Persist via `NamedEntityDataRepository.save()` + `mergeRelationship()` | `NamedEntityDataRepositoryGraphRelationshipPersister` | ✅ Spike loader uses repository API, not raw Cypher |
| `SimpleNamedEntityData` acceptable for fast spike without full Kotlin module | `NamedEntityDataRepositoryProxyTest` | ⚠️ OK for T03 prototype; **proper path = Kotlin `NamedEntity` classes** |
| Proposition pipeline (`PropositionExtractor` → `GraphProjectionService`) | `dice/README.md` | ❌ **Not our ingest path** — for conversation text, not structured markdown |
| `ContextId` scopes proposition memory | `dice/README.md` §ContextId | Optional `ContextId("sdlc-spdd-orchestrator")` if we add propositions later; not required for entity-only spike |

**Naming correction from research:** drop `Spdd*` label prefix. Embabel uses domain class
names directly (`Person`, `Composer`, `Work`). Namespace via package
(`com.embabel.spdd.domain.WorkId`), not label prefix.

## Design principles

1. **Join key = Work ID** — every retrievable artifact links back to `FEAT-001-*`, `SPIKE-001-*`, etc.
2. **Auditable edges** — retrieval explains inclusions via typed `@Semantics` relationships.
3. **Minimal spike slice** — seven entity types; expand only if A/B shows gaps.
4. **Dual ingest** — markdown → RAG chunks (leg 2) **and** repository projection → `__Entity__` (leg 3).
5. **Source of truth stays markdown** — entities are a projection, not a second authoring surface.

## Entity types (Kotlin `NamedEntity` — target)

Package: `com.embabel.spdd.domain` (guide fork module, scanned by `entityPackages`)

```kotlin
// Illustrative — finalize in T02
@JsonClassDescription("A unit of SPDD work (FEAT-, SPIKE-, BUG-, REF-)")
data class WorkId(
    override val id: String,           // e.g. "SPIKE-001-guide-rag-context-backend"
    override val name: String,         // slug or short title
    override val description: String,  // one-line goal
    val workType: String,
    val deliveryStage: String,
    val status: String,
    val readiness: String,
    @field:Semantics([With(key = Proposition.PREDICATE, value = "has canvas")])
    val canvas: Canvas? = null,
) : NamedEntity

data class Canvas(
    override val id: String,           // work id or canvas path hash
    override val name: String,
    override val description: String,
    val path: String,
    val readiness: String,
    val updated: String,
) : NamedEntity

data class Operation(
    override val id: String,           // "{workId}:T01"
    override val name: String,         // op id e.g. "T01"
    override val description: String,
    val status: String,
    @field:Semantics([With(key = Proposition.PREDICATE, value = "in canvas")])
    val canvas: Canvas? = null,
) : NamedEntity

data class Area(
    override val id: String,
    override val name: String,
    override val description: String,
) : NamedEntity

data class Decision(
    override val id: String,
    override val name: String,
    override val description: String,  // decision text
    val sourcePath: String,
    @field:Semantics([With(key = Proposition.PREDICATE, value = "about")])
    val area: Area? = null,
    @field:Semantics([With(key = Proposition.PREDICATE, value = "recorded for")])
    val workId: WorkId? = null,
) : NamedEntity

// Pitfall, Pattern — same shape as Decision
```

Neo4j relationship types follow **property names** per Embabel convention:
`canvas`, `area`, `workId` — not `HAS_CANVAS`, `ABOUT`, `RECORDED_FOR`.

## Ingest mapping (leg 3 projection)

| Source | Entities produced | Loader |
|--------|-------------------|--------|
| `spdd/canvas/<WorkID>.md` | WorkId, Canvas, Operation[] | Parse Metadata + Operations → `repository.save()` |
| `agent-context/memory/context-index.md` | Area, WorkId↔Area links | Parse index → entities + `mergeRelationship()` |
| `agent-context/memory/sessions/*.md` | Decision, Pitfall | Parse session outcomes |
| `spdd/analysis/*.md` | Decision, Pattern | Parse findings + Work ID refs |

Leg 2 (RAG): unchanged — `guide.directories` append.
Leg 3: `NamedEntityDataRepository` + `NamedEntityDataRepositoryGraphRelationshipPersister`
(or direct `mergeRelationship` calls) — **not** the proposition extraction pipeline.

## DICE / guide integration (fork)

```kotlin
// Schema registration (Embabel convention)
val schema = DataDictionary.fromClasses(
    "sdlc-spdd",
    WorkId::class.java,
    Canvas::class.java,
    Operation::class.java,
    Area::class.java,
    Decision::class.java,
    Pitfall::class.java,
    Pattern::class.java,
)
// Or: NamedEntity.dataDictionaryFromPackages("com.embabel.spdd.domain")
```

- Wire `DrivineNamedEntityDataRepository` with this `DataDictionary` (already in guide stack).
- Populate `__Entity__` via repository save — enables `entityFullTextSearch` / `queryForEntities`.
- Fork MCP tool wrapping `SearchOperations` entity queries filtered by `WorkId` / `Area`.
- Optional: link `Chunk` URIs to entity `uri` field for cross-leg drill-down.

## Spike validation (T02 / T03)

- [ ] Schema reviewed against Embabel conventions (this doc §Embabel convention alignment).
- [ ] Schema exercised against one real Work ID (e.g. SPIKE-001).
- [ ] Projection loads ≥1 WorkId subgraph via `NamedEntityDataRepository` (not raw Cypher only).
- [ ] `__Entity__` count > 0; domain query returns explainable subgraph.
- [ ] Hybrid retrieval beats embedding-only on auditability.

## Open choices (resolve in T02)

- **Recommended:** Kotlin `NamedEntity` module in guide fork (`com.embabel.spdd.domain`).
- **Prototype fallback:** `SimpleNamedEntityData` + explicit labels — must still include `__Entity__`.
- `Area` closed set vs free-text from index.
- Proposition/`ContextId` layer — defer; entity projection sufficient for spike.

## Status

Draft — Embabel convention review done 2026-06-19; finalize types in T02, implement in T03.
