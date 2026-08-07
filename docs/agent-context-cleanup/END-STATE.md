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

| Concern | SQLite | Guide (DICE) |
|---------|--------|--------------|
| Work ↔ canvas / requirements | FKs / joins | WorkId —`canvas`→ Canvas (+ doc refs) |
| Work ↔ areas | join table | WorkId —`area`→ Area |
| Lessons | lesson rows + work_id + area_id | Decision / Pitfall / Pattern; WorkId —lesson→; lesson —`about`→ Area |
| Cross-run area lessons | `WHERE area = ?` | `spdd_areaLessons` / incoming `about` |
| Registry / claim | claim table or columns | WorkId (+ claim model per #84) |
| Resume / session | session tables (hot path) | optional; SQLite-first per #85 |

## Explicitly not the end-state

- Committing `current-session.md` / feature mirrors as the memory bus  
- SQLite as filename cache only (no relational links)  
- Guide optional-forever while claiming parity  
