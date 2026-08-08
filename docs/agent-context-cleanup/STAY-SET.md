# Stay-in-git inventory

Tracked as [#81](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/81).

## Stays (versioned contracts + SPDD progress)

| Artifact | Path | Role |
|----------|------|------|
| Requirements (→ Jira) | `requirements/milestones/<WORK-ID>.md`, `requirements/` | Human-accepted scope; engine/Jira source |
| REASONS Canvas | `spdd/canvas/<WORK-ID>.md` | Governs SPDD execution + progress |
| SPDD governance siblings | `spdd/analysis/`, `spdd/reviews/`, `spdd/sync/` | Analysis / review / sync evidence |
| Planning narrative | `ROADMAP.md`, `milestone-*.md`, `session-notes/` | Story layer (outside `agent-context/`, still git) |

## Leaves commit surface (`agent-context/` runtime — migrate via #80)

| Artifact | Path |
|----------|------|
| Session briefs | `agent-context/sessions/**`, `current-session.md` |
| Feature mirrors | `agent-context/features/<WORK-ID>/{reasons-canvas,requirement,analysis-context,progress-log}.md` |
| Ephemeral locks | `agent-context/.work-registry.lock` |

## Lean encodings (stay or compact ledger — spikes)

These must remain available on path 1 with **full feature parity** (#82); representation is decided in spikes, not omitted:

| Capability | Spike |
|------------|-------|
| Lessons learned | [#83](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/83) |
| Work registry / claims | [#84](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/84) |
| Resume / session | [#85](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/85) |
| Git pointer records | [#87](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/87) |

Install/config that likely stays (not session noise): `agent-context/harness/`, `playbooks/`, `extensions/`, workflow scripts — confirm during #80/#86.
