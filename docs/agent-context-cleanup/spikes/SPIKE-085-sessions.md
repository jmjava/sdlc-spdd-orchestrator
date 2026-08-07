# SPIKE-085: Session resume without git noise

GitHub: [#85](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/85)  
Status: **implemented**

## Decision

| State | Location |
|-------|----------|
| Hot session briefs | `.sdlc/sessions/` only (gitignored) — never `agent-context/sessions/` for new writes |
| Resume rows | SQLite `context_sessions` (upserted from `start-agent-session.sh`) |
| Accepted checkpoint | Optional git pointer `kind=resume` (#87) |

`start-agent-session.sh` writes `.sdlc/sessions/current-session.md`.  
`capture-session-memory.sh` prefers that path; legacy `agent-context/sessions/` is read-only fallback until upgrade archives it.
