# SPIKE-085: Session resume without git noise

GitHub: [#85](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/85)  
Status: **proposal accepted for implementation**

## Decision

| State | Location |
|-------|----------|
| Hot session briefs | `.sdlc/sessions/` only (gitignored) — never `agent-context/sessions/` for new writes |
| Resume rows | SQLite `context_sessions` |
| Accepted checkpoint | Optional git pointer `kind=resume` (#87) |

`start-agent-session.sh` should prefer `.sdlc/sessions/current-session.md`. Legacy `agent-context/sessions/` is read-only fallback until upgrade deletes/archives it.
