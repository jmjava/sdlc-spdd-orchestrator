# Research: SPIKE-003-embabel-context-graph-absorption

Design verification against the live Guide fork delta (`jmjava/guide` @
`sdlc-spdd-projection-v1` / `a6e3246`) versus upstream `embabel/guide` `main`
(`67f5e9d`, fetched 2026-08-07).

**Goal:** classify the SPIKE-001 “context graph” surfaces for absorption — not re-prove
RAG ingest or re-run SPIKE-001 A/B.

## Baseline

| Ref | Commit / tip | Notes |
|-----|--------------|-------|
| Upstream | `embabel/guide` `main` @ `67f5e9d` | No `com.embabel.guide.spdd`, no git-incremental directory ingest |
| Fork tip / pin | `jmjava/guide` `main` / tag `sdlc-spdd-projection-v1` @ `a6e3246` | SPIKE-001 projection + ops deltas |
| Diff | `upstream/main...a6e3246` | **39 files, +2838 / −22** |

Orchestrator pin and dogfood path remain documented in
`docs/dice-projection-runbook.md`.

## Layer inventory

### Layer A — SPDD context-graph package (opt-in)

| Path | Role |
|------|------|
| `src/main/kotlin/.../spdd/domain/SpddDomain.kt` | `NamedEntity` types + `@Semantics` |
| `SpddEntityDictionary.kt` | `DataDictionary.fromClasses("sdlc-spdd", …)` |
| `SpddMarkdownProjectionService.kt` | Markdown → `__Entity__` + typed edges; read APIs |
| `SpddProjectionController.kt` | Operator HTTP |
| `SpddDomainTools.kt` + `SpddProjectionConfiguration.kt` | MCP `spdd_*` |
| `SpddProjectionResult.kt` | DTOs |
| Tests + `src/test/resources/spdd-fixture/` | Contract tests + fixture |

**Coupling:** SPDD directory conventions (`spdd/canvas/*.md`,
`agent-context/memory/context-index.md`) and SPDD label vocabulary.
**Flag:** `guide.spdd-projection.enabled` (default false).
**Library APIs used:** public `NamedEntityData` / `NamedEntityDataRepository` /
`DataDictionary` / `McpToolExport` — no private Embabel hooks.

### Layer B — Git-incremental RAG + maintenance (generally useful)

| Path | Role |
|------|------|
| `GitIncrementalDirectorySupport.java` | Diff directory ingest against last git revision |
| `GitIngestionRevisionStore.java` | Revision state file |
| `DataManager.java` hooks | Wire incremental path into `loadReferences()` |
| `RagContentMaintenanceService.kt` + controllers/handlers | Purge preview/purge + revision reset |
| Tests + script updates (`append-ingest.sh`, examples) | Operator ergonomics |

**Coupling:** Guide directory ingest generally — **not** SPDD-specific.
**Flag:** `guide.git-ingestion.enabled` (default false).

### Layer C — Cross-cutting (active with or without flags)

| Change | Why it exists |
|--------|----------------|
| `GuideProperties` `spddProjection` + `gitIngestion` blocks | Config surface |
| `SecurityConfig` permit-all for new operator routes | Same local-ops posture as `load-references` |
| `application.yml` Neo4j Spring auth + port env wiring | Health/driver credential alignment |
| `PersonaSeedingService` resilience | Fail actionable on missing KSP DSL; don’t abort RAG/MCP |
| `pom.xml` neo-drivine timestamp pin + enforcer KSP files | Agent 0.3.5 vs floating 0.1.2-SNAPSHOT; build fail-fast |
| Docs `spdd-*.md` | Fork developer / operator docs |

## Upstreamability matrix

| Slice | Embabel-general value | SPDD coupling | Upstream friction | Recommendation |
|-------|----------------------|---------------|-------------------|----------------|
| A. `com.embabel.guide.spdd` package + `spdd_*` MCP | Medium (shows DICE on Guide) | **High** (SPDD paths/labels) | Medium (naming, docs, product fit) | **Keep on `jmjava/guide`** for now; do not upstream as-is |
| A′. Generic entity MCP wrapping `SearchOperations` / repository reads | **High** | Low if schema-agnostic | Medium (API design) | **Candidate follow-on FEAT** — separate from SPDD prefix |
| B. Git-incremental directory ingest + maintenance | **High** | None | Low–medium | **Best first upstream PR** from the fork |
| C. Neo4j Spring auth alignment / KSP enforcer / persona resilience | Medium–high (ops) | None | Low | Upstream with B or as small ops PRs |
| C′. neo-drivine timestamp pin | Low (version lag) | None | **High** (upstream may already move) | Keep fork-local until Guide agent version catches up |
| Gaps: entity↔chunk join on HTTP/MCP | High for DICE story | Medium | Medium | Implement on fork first; strengthens any future upstream narrative |
| Gaps: Operation / Keyword / Session projection | Medium | High | Low (fork-only) | Fork FEAT after dogfood demand |

## What “context graph” means here

In this spike, **context graph** = the typed Neo4j `__Entity__` layer plus typed-edge
retrieve used as auditable prompt context (SPIKE-001 leg 3), not Embabel’s conversation
proposition pipeline and not generic RAG chunks alone.

| Surface today | Upstream Guide | Fork (`sdlc-spdd-projection-v1`) |
|---------------|----------------|-----------------------------------|
| `docs_*` chunk MCP | Yes | Yes |
| Generic domain-graph MCP | No | No |
| SPDD typed projection + `spdd_*` | No | Yes (opt-in) |
| Entity↔chunk join on MCP/HTTP | No | Store-level only (not exposed) |

## Recommendation (2026-08-07)

**Hybrid / keep-fork for the SPDD context graph; upstream the reusable ingest ops.**

1. **Absorb locally (durable):** treat `jmjava/guide` `com.embabel.guide.spdd` as the
   supported home for the SDLC-SPDD context graph; keep pin
   `sdlc-spdd-projection-v1` (or successor tags) from the orchestrator.
2. **Upstream first slice (optional FEAT):** git-incremental directory ingest + RAG
   maintenance endpoints + related ops hardening — valuable without SPDD naming.
3. **Do not upstream `spdd_*` as the Embabel-native graph API.** If Embabel wants a
   generic context-graph MCP, design schema-agnostic tools (label/id/rel walk) in a
   follow-on FEAT; SPDD projection can remain a Guide (or consumer) module on top.
4. **Sync process:** periodically merge `embabel/guide` `main` into `jmjava/guide`;
   re-tag when projection contract changes; document candidates in
   `docs/spdd-upstream-absorption.md` (Guide).

### Decision table

| Criterion | Verdict |
|-----------|---------|
| Immediate PR of entire fork to `embabel/guide` | **No-go** |
| Keep SPDD package on `jmjava/guide` | **Go** |
| Upstream git-incremental ingest | **Go (follow-on)** |
| Generic entity MCP before SPDD upstream | **Preferred path if Embabel engagement** |
| Extract separate library module now | **Defer** until a second consumer appears |

## Evidence commands

```bash
cd /path/to/jmjava/guide
git fetch upstream main
git rev-parse HEAD upstream/main
git diff --stat upstream/main...HEAD
git diff --name-status upstream/main...HEAD
```

Observed (2026-08-07): `HEAD=a6e3246`, `upstream/main=67f5e9d`, 39 files,
+2838/−22.

## Explicit non-goals confirmed

- Not SPIKE-002 (Ollama / embedding dim).
- Not replacing markdown-first indexes.
- Not rewriting `SpddMarkdownProjectionService` in this spike.
