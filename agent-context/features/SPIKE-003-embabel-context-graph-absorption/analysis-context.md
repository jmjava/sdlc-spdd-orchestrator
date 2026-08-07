# Analysis: SPIKE-003-embabel-context-graph-absorption

## Metadata

- **Work ID:** SPIKE-003-embabel-context-graph-absorption
- **Requirement:** `requirements/milestones/SPIKE-003-embabel-context-graph-absorption.md`
- **Canvas:** `spdd/canvas/SPIKE-003-embabel-context-graph-absorption.md`
- **Research:** `spdd/analysis/SPIKE-003-embabel-context-graph-absorption-research.md`
- **Timestamp:** 2026-08-07T20:42:00Z
- **Branches:** orchestrator `cursor/embabel-context-graph-research-65ca`; Guide
  `cursor/embabel-context-graph-absorption-fdca`
- **Prerequisite:** SPIKE-001 provisional GO; Guide tag `sdlc-spdd-projection-v1`

## Domain Keywords

- Embabel Guide fork
- context graph / DICE domain graph
- NamedEntity / `__Entity__`
- upstream absorption
- git-incremental ingest
- `spdd_*` MCP
- SearchOperations entity APIs
- fork sync

## Code Areas

- Guide `com.embabel.guide.spdd` — SPDD context-graph package (fork)
- Guide `com.embabel.guide.rag` — git-incremental + maintenance (fork)
- Guide `docs/spdd-*.md` — absorption / operator docs
- Orchestrator `docs/dice-projection-runbook.md`, `docs/guide-flow.md` — dogfood path
- Orchestrator `spdd/analysis/SPIKE-001-*` — prior contract

## Existing Concepts

### SPIKE-001 delivered the graph

SPIKE-001 designed the SDLC-SPDD DICE slice, implemented markdown→`__Entity__`
projection on `jmjava/guide`, exposed HTTP + `spdd_*` MCP retrieve, and provisionally
shipped the optional orchestrator backend (`CONTEXT_BACKEND=guide-dice`). Markdown
indexes remain the default when Guide is absent.

### What was still “fork work” in SPIKE-001 research

Confirmational research (2026-06-19) found Guide MCP exposed `docs_*` only; library
`SearchOperations` entity APIs were not on Guide MCP; `__Entity__` stayed empty until
custom projection. The fork filled the **SPDD-specific** gap. It did **not** add a
generic Embabel domain-graph MCP.

### SPIKE-002 is a sibling, not a blocker

Local LLM + embedding format research shares the Guide substrate but answers a different
question. Absorption of the context graph must not wait on or expand into model work.

## New Concepts (this spike)

### Absorption vs implementation

| Term | Meaning here |
|------|----------------|
| Context graph | Typed `__Entity__` + typed-edge retrieve used for auditable context |
| Absorption | Long-term home for that capability (upstream / fork / module / hybrid) |
| Upstreamable slice | Fork delta with Embabel-general value and low SPDD coupling |

### Classification outcome

Full matrix: research artifact. Summary:

1. **SPDD package (`spdd_*`)** — keep on `jmjava/guide` (high coupling).
2. **Git-incremental RAG + maintenance** — best first upstream candidate.
3. **Generic entity MCP** — preferred Embabel-native graph story if upstream engages;
   design separately from SPDD prefixes.
4. **Extract library module** — defer until a second consumer exists.

## Decision

**Hybrid keep-fork for the SPDD context graph; optional follow-on to upstream
git-incremental ingest and ops hardening.**

| Question | Answer |
|----------|--------|
| Upstream entire SPIKE-001 fork now? | **No** |
| Is `jmjava/guide` the durable home for `com.embabel.guide.spdd`? | **Yes** |
| Should orchestrator keep pinning the fork tag? | **Yes** (`sdlc-spdd-projection-v1` or successors) |
| First upstreamable slice? | Git-incremental directory ingest + RAG maintenance |
| Generic context-graph MCP? | Follow-on FEAT if Embabel wants it; not a rename of `spdd_*` |

## Remaining gaps (severity)

| Gap | Severity | Owner |
|-----|----------|-------|
| Entity↔chunk join not on HTTP/MCP | Medium | Guide fork FEAT |
| `Operation` / Keyword / Session not projected | Low–medium | Guide fork FEAT after demand |
| Stale “DynamicType” note in Guide branch summary | Low | Fixed this spike in Guide docs |
| Informal upstream sync | Medium | Documented sync process in Guide absorption doc |
| SPIKE-001 T06 final keep/rollback still field-pending | Medium | Continues on SPIKE-001; not blocked by SPIKE-003 |

## Follow-on FEAT sketch (only if recommendation accepted)

1. **FEAT (Guide upstream):** git-incremental directory ingest + maintenance APIs → PR to
   `embabel/guide` (or series of small PRs with ops hardening).
2. **FEAT (optional, Embabel-shaped):** generic entity retrieve MCP
   (`entitySubgraph` / `findByLabel` without SPDD prefix) over `NamedEntityDataRepository`
   / `SearchOperations`; keep `spdd_*` as a thin façade or migrate command packs later.
3. **FEAT (fork):** expose `findChunksForEntity` on projection HTTP/MCP for stronger DICE
   joins.
4. **Non-FEAT process:** merge upstream `main` into `jmjava/guide` on a cadence; retag
   when projection contract changes.

## Non-Goals confirmed

- No production rewrite of projection.
- No required Guide dependency.
- No SPIKE-002 scope creep.

## Next

1. Human accept/reject of hybrid recommendation.
2. If accept: intake FEAT for git-incremental upstream; keep SPDD package fork-local.
3. Continue SPIKE-001 field dogfood independently.
