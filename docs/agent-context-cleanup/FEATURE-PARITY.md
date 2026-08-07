# Triple-path feature parity

Tracked as [#82](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/82).

## Rule

While paths run in parallel, **each path exposes the same capability set**.  
“Thin-in-git” = lean representation, not a degraded product.

## Capability matrix (required)

| Capability | Git (lean) | SQLite (relational) | Guide (DICE) |
|------------|------------|---------------------|--------------|
| Requirements + REASONS linkage | Stay-set files | `requirements`/`canvases` + `reasons` edge | WorkId / Canvas (+ refs) |
| Analysis / review / sync / retro / progress | Stay-set + lean entries | `context_entries` + edges | Projectable docs |
| Domain / phase / memory / prompt / tooling | Indexes + ledgers | keywords / phase_refs / facts / entries | Optional |
| Work registry / claim | Lean ledger or compact file (#84) | Claim tables | WorkId + claim model |
| Resume / session context | Pointer only on accept (#85) | Session tables + session entries | Optional; SQLite-first hot path |
| Lessons (decision/pitfall/pattern) | Lean stay-set (#83) | Lesson tables | Decision/Pitfall/Pattern + edges |
| Cross-run lessons by area | Index / ledger query | SQL by area | `about` / `spdd_areaLessons` |
| Persist fan-out | Write lean form | Upsert | Project / sync |
| Retrieve assemble | Reconstruct from stay-set + pointers | `graph_for_work` / coverage | HTTP/MCP subgraph |

Gate: `capability_coverage().complete` must be true for a full tree before `main`.

## Soft-fail

If Guide is down, git + SQLite still cover the matrix.  
If SQLite is missing, git + Guide still cover the matrix.  
Missing backend ≠ missing feature in the design.
