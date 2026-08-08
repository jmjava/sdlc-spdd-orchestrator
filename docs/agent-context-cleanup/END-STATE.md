# End-state: three projections, one graph

Tracked as [#93](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/93).

## Gate for `main`

**Do not open or merge `integration → main` until this end-state is complete with tests.**  
Intermediate PRs target `cursor/agent-context-cleanup-integration-decf` only.

Status: end-state reached on integration; the one final PR is open as draft
[#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109), awaiting human review.

## Invariant

A fact accepted into agent context is available from:

| Path | Encoding |
|------|----------|
| 1. Lean git | Stay-set docs + compact pointers / ledgers |
| 2. SQLite | Relational tables + typed `edges` (schema v4) |
| 3. Guide | Neo4j DICE `__Entity__` graph + typed relationships |

Soft-fail is about **availability** of a backend, not about shipping different feature matrices (#82).

## Full graph (schema v4)

Must include **all** agent-context capabilities, not only lessons:

| Concern | SQLite | Guide (DICE) |
|---------|--------|--------------|
| Work ↔ requirement | `requirements` + edge `requirement` | doc refs today; first-class TBD |
| Work ↔ REASONS canvas | `canvases` + edge `canvas` | WorkId —`canvas`→ Canvas |
| Requirement ↔ REASONS | edge `reasons` | orchestrator graph (Guide may follow) |
| Analysis / review / sync / retro / progress | `context_entries` + edges | projectable docs / entities |
| Metrics / prompt log / project memory | `context_entries` / `project_facts` | optional projection |
| Domain keywords / phase catalog | `domain_keywords` / `phase_refs` | optional |
| Playbooks / harness / extensions | `context_entries` kinds | optional tooling nodes |
| Legacy feature mirrors | ingested as `*_mirror` / entry kinds | transitional until #86/#80 |
| Areas | `areas` + edges `area` | WorkId —`area`→ Area |
| Lessons | `lessons` + edges `about` | Decision/Pitfall/Pattern —`about`→ Area |
| Claims / sessions / pointers | tables + `for_work` | SQLite-first hot path |

Coverage API: `LocalIndex.capability_coverage()` — must report `complete: true` on a full tree.

## Explicitly not the end-state

- Committing `current-session.md` / feature mirrors as the *only* memory bus  
- SQLite as filename cache only (no relational links)  
- Guide optional-forever while claiming parity  
- Merging to `main` with partial capability coverage  
