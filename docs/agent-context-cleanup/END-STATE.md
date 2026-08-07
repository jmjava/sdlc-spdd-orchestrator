# End-state: three projections, one graph

Tracked as [#93](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/93).

## Invariant

A fact accepted into agent context (claim, resume pointer, lesson, work↔area link, …) is available from:

| Path | Encoding |
|------|----------|
| 1. Lean git | Stay-set docs + compact pointers / ledgers |
| 2. SQLite | Relational tables + foreign keys / join tables |
| 3. Guide | Neo4j DICE `__Entity__` graph + typed relationships |

Soft-fail is about **availability** of a backend, not about shipping different feature matrices (#82).

## Link model (same edges, two machine stores)

The SQLite schema (v3) encompasses **all sections**: requirements, REASONS canvases, and context parts, with typed edges between them.

| Concern | SQLite | Guide (DICE) |
|---------|--------|--------------|
| Work ↔ requirement | `requirements` + edge `requirement` | (doc path today; first-class Requirement TBD) |
| Work ↔ REASONS canvas | `canvases` + edge `canvas` | WorkId —`canvas`→ Canvas |
| Requirement ↔ REASONS | edge `reasons` | (orchestrator graph; Guide may follow) |
| Work / req / canvas ↔ areas | `areas` + edges `area` | WorkId —`area`→ Area |
| Lessons ↔ area / sections | `lessons` + edges `about` | Decision / Pitfall / Pattern —`about`→ Area |
| Lessons ↔ work | edge `recorded_for` + `work_id` | lesson —`recorded for`→ WorkId |
| Cross-run area lessons | `WHERE area = ?` / edge walk | `spdd_areaLessons` / incoming `about` |
| Registry / claim | `claims` + edge `for_work` | WorkId (+ claim model per #84) |
| Resume / session / pointer | session/pointer tables + `for_work` | optional; SQLite-first per #85 |

## Explicitly not the end-state

- Committing `current-session.md` / feature mirrors as the memory bus  
- SQLite as filename cache only (no relational links)  
- Guide optional-forever while claiming parity  
