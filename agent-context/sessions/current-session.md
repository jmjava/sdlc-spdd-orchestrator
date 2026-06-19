# SDLC-SPDD Agent Session

## Metadata

- Timestamp: 2026-06-19T03:16:38Z
- Target: /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator
- Work ID: FEAT-001-shared-script-library
- Phase: plan
- Active milestone: milestone-1.md
- Recommended command: /sdlc-spdd-plan @spdd/analysis/FEAT-001-shared-script-library-analysis.md
- Canvas sync state: no canvas found
- Previous session brief: /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/agent-context/sessions/current-session.md

## Framework Orientation

New agents: load these first so you know how to operate within the SDLC-SPDD framework before doing any work.

- Operating model + work rules: the always-on grounding file (.cursor/rules/sdlc-spdd.mdc, .github/copilot-instructions.md, or CLAUDE.md) is loaded on every request.
- How the framework works: docs/sdlc-spdd/three-part-operating-path.md, docs/sdlc-spdd/ten-thousand-foot-view.md.
- Session + context-loading rules: docs/sdlc-spdd/context-loading-and-scaling.md#bootstrap-and-index-based-loading (bootstrap layers, index catalog, retrieval, capture).
- Resolve phase skills/extensions: ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase plan

## Hybrid Operating Model

- SDLC Agents side: use the phase-specific role, load only relevant context, preserve handoffs, and capture learning.
- SPDD side: treat the REASONS Canvas as the governing prompt contract and keep prompt artifacts synchronized with code.

## Artifact Status

| Artifact | Path | Status |
|----------|------|--------|
| Feature workspace | /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/agent-context/features/FEAT-001-shared-script-library | missing |
| Feature canvas | /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/agent-context/features/FEAT-001-shared-script-library/reasons-canvas.md | missing |
| Canonical canvas | /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/spdd/canvas/FEAT-001-shared-script-library.md | missing |
| Progress log | /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/agent-context/features/FEAT-001-shared-script-library/progress-log.md | missing |
| Review report | /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/spdd/reviews/FEAT-001-shared-script-library-review.md | missing |
| Sync log | /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/spdd/sync/FEAT-001-shared-script-library-sync.md | missing |
| Retro | /home/ubuntu/github/jmjava/sdlc-spdd-orchestrator/agent-context/features/FEAT-001-shared-script-library/retro.md | missing |

## Roadmap and Milestone Context

| Artifact | Path | Status |
|----------|------|--------|
| Roadmap | ROADMAP.md | present |
| Today's session notes | session-notes/2026-06-19.md | missing |

Milestone docs:

- milestone-1.md

## Persistent Memory To Read

Use **Resolved Context** below first (static + area-filtered index rows). For manual lookup:

- agent-context/memory/context-index.md — filter by Area when you know the code area
- agent-context/memory/domain-index.md — filter by Keyword during analysis
- agent-context/memory/session-index.md — session-only view (newest first)
- agent-context/memory/code-areas.md — canonical area categories

Do not read session-history.md top-to-bottom or load whole memory logs when index rows already point at the relevant entries.

## Resolved Context

Phase-specific extensions, playbooks, Work ID artifacts, and area-filtered index matches for **plan** (from resolve-agent-context.sh):

### Static and phase files

| Kind | Path |
|------|------|
| file | ROADMAP.md |
| file | requirements/milestones/FEAT-004-prompt-optimization-ledger.md |

Refresh after adding extensions, code areas, or  skills:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase plan --work-id FEAT-001-shared-script-library
    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase plan --text "#TDD #java"

## Git Status

     M CONTRIBUTING.md
 M README.md
 M docs/useful-concepts-and-commands.md
?? .github/workflows/check-posture-boundary.yml
?? ROADMAP.md
?? agent-context/sessions/
?? milestone-1.md
?? requirements/
?? scripts/check-posture-boundary.sh
?? spdd/

## Resume Prompt

Use this prompt at the start of the new agent session. See docs/sdlc-spdd/session-prompt-standard.md for the full prompt contract.

    For FEAT-001-shared-script-library, read @agent-context/sessions/current-session.md first.
    
    Load only the files listed under **Resolved Context** in that brief for the plan phase (SDLC Agents progressive disclosure).
    Also read @spdd/analysis/FEAT-001-shared-script-library-analysis.md before planning.
    
    Continue in the plan phase using the hybrid SDLC Agents + SPDD workflow.
    Recommended command: /sdlc-spdd-plan @spdd/analysis/FEAT-001-shared-script-library-analysis.md

## Session Notes

Add notes here during the session, then persist them with:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id FEAT-001-shared-script-library --phase plan --summary "<summary>" --validation "<validation>" --next "<next command>"
