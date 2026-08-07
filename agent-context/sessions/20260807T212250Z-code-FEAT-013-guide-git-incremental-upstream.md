# SDLC-SPDD Agent Session

## Metadata

- Timestamp: 2026-08-07T21:22:50Z
- Target: /agent/repos/sdlc-spdd-orchestrator
- Work ID: FEAT-013-guide-git-incremental-upstream
- Phase: code
- Jira: draft
- Active milestone: none
- Recommended command: /sdlc-spdd-code @spdd/canvas/FEAT-013-guide-git-incremental-upstream.md operation T02
- Optional verify: /sdlc-spdd-verify @spdd/canvas/FEAT-013-guide-git-incremental-upstream.md
- Canvas sync state: in sync
- Previous session brief: /agent/repos/sdlc-spdd-orchestrator/agent-context/sessions/20260619T031638Z-plan-FEAT-001-shared-script-library.md

## Workflow State

Local phase + gate tracking (not committed). Refresh with `./scripts/sdlc.sh next` or `/sdlc-spdd-whereami`.

| Field | Value |
|-------|-------|
| Work ID | FEAT-013-guide-git-incremental-upstream |
| Workflow status | active |
| Phase | code (5/10) |
| Readiness | ready-for-coding |
| Jira | draft |
| Next operation | ### T02 - Produce clean Layer B branch vs embabel/guide main |
| Assistant command | /sdlc-spdd-code @spdd/canvas/FEAT-013-guide-git-incremental-upstream.md operation T02 |
| After this phase | `./scripts/sdlc.sh advance` |
| Capture (guarded) | `./scripts/sdlc.sh capture --summary "<summary>"` |
| Orient / status | `./scripts/sdlc.sh next` or `/sdlc-spdd-whereami` |

Pending gates:
- Review completed
- Safeguards checked
- Retro completed

Tracker follow-up:
- Tracker link: Jira draft exists for FEAT-013-guide-git-incremental-upstream but `- Key:` is unset. Ask the user for the issue key (or confirm none applies) before coding or claiming tracker progress. Then run `./scripts/sdlc.sh claim FEAT-013-guide-git-incremental-upstream --jira KEY` (or set `- Key:` under `## Jira` and re-claim). Do not invent a key.

## Framework Orientation

New agents: load these first so you know how to operate within the SDLC-SPDD framework before doing any work.

- Operating model + work rules: the always-on grounding file (.cursor/rules/sdlc-spdd.mdc, .github/copilot-instructions.md, or CLAUDE.md) is loaded on every request.
- How the framework works: docs/sdlc-spdd/three-part-operating-path.md, docs/sdlc-spdd/ten-thousand-foot-view.md.
- Session + context-loading rules: docs/sdlc-spdd/context-loading-and-scaling.md#bootstrap-and-index-based-loading (bootstrap layers, index catalog, retrieval, capture).
- Resolve phase skills/extensions: ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code

## Hybrid Operating Model

- SDLC Agents side: use the phase-specific role, load only relevant context, preserve handoffs, and capture learning.
- SPDD side: treat the REASONS Canvas as the governing prompt contract and keep prompt artifacts synchronized with code.

## Artifact Status

| Artifact | Path | Status |
|----------|------|--------|
| Feature workspace | /agent/repos/sdlc-spdd-orchestrator/agent-context/features/FEAT-013-guide-git-incremental-upstream | present |
| Feature canvas | /agent/repos/sdlc-spdd-orchestrator/agent-context/features/FEAT-013-guide-git-incremental-upstream/reasons-canvas.md | present |
| Canonical canvas | /agent/repos/sdlc-spdd-orchestrator/spdd/canvas/FEAT-013-guide-git-incremental-upstream.md | present |
| Progress log | /agent/repos/sdlc-spdd-orchestrator/agent-context/features/FEAT-013-guide-git-incremental-upstream/progress-log.md | present |
| Review report | /agent/repos/sdlc-spdd-orchestrator/spdd/reviews/FEAT-013-guide-git-incremental-upstream-review.md | missing |
| Sync log | /agent/repos/sdlc-spdd-orchestrator/spdd/sync/FEAT-013-guide-git-incremental-upstream-sync.md | missing |
| Retro | /agent/repos/sdlc-spdd-orchestrator/agent-context/features/FEAT-013-guide-git-incremental-upstream/retro.md | missing |

## Roadmap and Milestone Context

| Artifact | Path | Status |
|----------|------|--------|
| Roadmap | ROADMAP.md | present |
| Today's session notes | session-notes/2026-08-07.md | present |

Milestone docs:

- requirements/milestones/milestone-1/MILESTONE-1.md

## Persistent Memory To Read

Use **Resolved Context** below first (static + area-filtered index rows). For manual lookup:

- agent-context/memory/context-index.md — filter by Area when you know the code area
- agent-context/memory/domain-index.md — filter by Keyword during analysis
- agent-context/memory/session-index.md — session-only view (newest first)
- agent-context/memory/code-areas.md — canonical area categories

Do not read session-history.md top-to-bottom or load whole memory logs when index rows already point at the relevant entries.

## Resolved Context

Phase-specific extensions, playbooks, Work ID artifacts, and area-filtered index matches for **code** (from resolve-agent-context.sh):

### Static and phase files

| Kind | Path |
|------|------|
| extension | agent-context/extensions/_all-agents/example-manifest-extension.md |
| playbook | agent-context/playbooks/java-feature-playbook.md |
| playbook | agent-context/playbooks/bugfix-playbook.md |
| playbook | agent-context/playbooks/refactor-playbook.md |
| spdd | spdd/canvas/FEAT-013-guide-git-incremental-upstream.md |
| spdd | spdd/analysis/FEAT-013-guide-git-incremental-upstream-analysis.md |
| file | agent-context/features/FEAT-013-guide-git-incremental-upstream/progress-log.md |
| file | agent-context/features/FEAT-013-guide-git-incremental-upstream/analysis-context.md |

Code areas: guide com.embabel.guide.rag — git-incremental + maintenance guide guideproperties / application.yml — gitingestion config block guide securityconfig — permit-all for new operator routes guide tests under src/test/.../rag guide docs: docs/spdd-upstream-absorption.md orchestrator cross-links: guide-integration-spike.md, docs/dice-projection-runbook.md

Refresh after adding extensions, code areas, or  skills:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code --work-id FEAT-013-guide-git-incremental-upstream
    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code --text "#TDD #java"



## Git Status

     M .cursor/rules/sdlc-spdd.mdc
     M agent-context/features/FEAT-013-guide-git-incremental-upstream/reasons-canvas.md
     M agent-context/sdlc-workflow.sh
     M agent-context/work-registry.tsv
     M docs/what-spdd-brings.md
     M scripts/start-agent-session.sh
     M spdd/canvas/FEAT-013-guide-git-incremental-upstream.md
     M templates/claude/CLAUDE.md
     M templates/copilot/copilot-instructions.md
     M templates/cursor/rules/sdlc-spdd.mdc
     M templates/reasons-canvas/bugfix-template.md
     M templates/reasons-canvas/feature-template.md
     M templates/reasons-canvas/refactor-template.md
     M templates/reasons-canvas/spike-template.md
    ?? .cursor/commands/sdlc-spdd-verify.md
    ?? agent-context/.work-registry.lock
    ?? templates/cursor/sdlc-spdd-verify.md

## Resume Prompt

Use this prompt at the start of the new agent session. See docs/sdlc-spdd/session-prompt-standard.md for the full prompt contract.

    For FEAT-013-guide-git-incremental-upstream, read @agent-context/sessions/current-session.md first.
    
    Load only the files listed under **Resolved Context** in that brief for the code phase (SDLC Agents progressive disclosure).
    
    Continue in the code phase using the hybrid SDLC Agents + SPDD workflow.
    Recommended command: /sdlc-spdd-code @spdd/canvas/FEAT-013-guide-git-incremental-upstream.md operation T02
    Optional freeform verify (does not advance T##): /sdlc-spdd-verify @spdd/canvas/FEAT-013-guide-git-incremental-upstream.md
    
    Tracker link: Jira draft exists for FEAT-013-guide-git-incremental-upstream but `- Key:` is unset. Ask the user for the issue key (or confirm none applies) before coding or claiming tracker progress. Then run `./scripts/sdlc.sh claim FEAT-013-guide-git-incremental-upstream --jira KEY` (or set `- Key:` under `## Jira` and re-claim). Do not invent a key.

## Session Notes

Add notes here during the session, then persist them with:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id FEAT-013-guide-git-incremental-upstream --phase code --summary "<summary>" --validation "<validation>" --next "<next command>"
