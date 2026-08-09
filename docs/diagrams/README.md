# System Diagrams (PlantUML)

Canonical architecture diagrams for the SDLC-SPDD Orchestrator, storage v3.
PlantUML is the single diagram toolchain for this repo. The `.puml` files in
this folder are the sources of truth; rendered `.svg` exports are committed
alongside them so diagrams display everywhere (GitHub, IDEs, PDF exports).

| Diagram | Type | Shows |
|---|---|---|
| [01-context.puml](01-context.puml) | C4 context | Developer, AI agent, framework, Guide DICE, git remote |
| [02-container.puml](02-container.puml) | C4 container | Adapters, contracts, ledger, scripts, engine, runtime inside `sdlc-spdd/` |
| [03-component-engine.puml](03-component-engine.puml) | C4 component | `sdlc-engine` modules and how they touch ledger, sqlite, Guide |
| [04-lifecycle-flow.puml](04-lifecycle-flow.puml) | Activity | Init → Analysis → Plan → Architect → Code → API Test → Review → Retro → Sync with storage gates |
| [05-storage-model.puml](05-storage-model.puml) | Class | `LessonRecord`, `LessonsLedger`, registry events, projections |
| [06-stage-then-accept.puml](06-stage-then-accept.puml) | Sequence | Quiet captures to `.sdlc/staged/`, accept promotes to the committed ledger |
| [07-retrieval-flow.puml](07-retrieval-flow.puml) | Sequence | Session-start digest and on-demand, per-phase retrieval |
| [08-projection-parity.puml](08-projection-parity.puml) | Sequence | One write path; sqlite + Guide as regenerable projections; `context parity` |
| [09-install-layout.puml](09-install-layout.puml) | WBS | Single-folder `sdlc-spdd/` install layout and adapter stubs |
| [10-dice-object-graph.puml](10-dice-object-graph.puml) | Object | Guide DICE entities/edges and the `spdd_*` MCP surface |
| [11-daily-loop.puml](11-daily-loop.puml) | Activity | Claim → session → phases → capture → accept loop |
| [12-context-backend-resolution.puml](12-context-backend-resolution.puml) | Activity | Runtime probe: files baseline vs guide-dice augmentation |
| [13-guide-rag-legs.puml](13-guide-rag-legs.puml) | Component | RAG chunks + entity graph ingested from the same ledger |
| [14-ops-console.puml](14-ops-console.puml) | Component | Ops console :5051, ADF viewer :5050, optional Guide + Neo4j |

## Rendering

Requires Java. The render script fetches the PlantUML jar into
`~/.cache/plantuml/` on first use (override with `PLANTUML_JAR`):

    ./scripts/render-diagrams.sh            # render all .puml to SVG here
    ./scripts/render-diagrams.sh --check    # validate only (CI)

C4 diagrams include the [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML)
stdlib from the network at render time.

Regenerate the committed `.svg` files whenever a `.puml` source changes.
Do not edit rendered images by hand.
