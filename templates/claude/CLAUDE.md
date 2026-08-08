<!-- BEGIN SDLC-SPDD MANAGED CLAUDE GROUNDING -->
# SDLC-SPDD Claude Code Instructions

Use these instructions for every Claude Code request in this workspace.

## Operating Model

This repository uses SDLC-SPDD: SDLC Agents-style lifecycle roles backed by SPDD REASONS Canvas design contracts.

Default lifecycle (Fowler SPDD + SDLC hybrid):

    Initialize -> Analysis -> Plan -> Architect -> Code -> API Test -> Review -> Retro -> Sync

The matching slash commands live in `.claude/commands/`:

    /sdlc-spdd-init
    /sdlc-spdd-analysis
    /sdlc-spdd-plan
    /sdlc-spdd-architect
    /sdlc-spdd-code
    /sdlc-spdd-api-test
    /sdlc-spdd-review
    /sdlc-spdd-commit-message
    /sdlc-spdd-prompt-update
    /sdlc-spdd-retro
    /sdlc-spdd-sync
    /sdlc-spdd-whereami

## Workflow Commands

Manage your Work ID and lifecycle phase without leaving chat:

    /sdlc-claim <WORK-ID>        Claim a work item (sets pointer + team registry)
    /sdlc-shelf [reason]         Shelf current work (pause temporarily)
    /sdlc-advance [--to PHASE]   Advance to next phase gate
    /sdlc-next                   Show next action for current work
    /sdlc-team                   See team work registry

Workflow state is tracked in `.sdlc/` (local, private) and `spdd/memory/registry.jsonl` (shared, via `sdlc.sh claim/release`).

Preserve context by reading relevant artifacts before answering:

- `requirements/`
- `spdd/analysis/`
- `spdd/canvas/`
- `spdd/tasks/`
- `spdd/reviews/`
- `spdd/sync/`
- `spdd/memory/lessons.jsonl` (committed ledger — never edit by hand)
- `spdd/memory/registry.jsonl` (committed registry — managed via `sdlc.sh claim/release`)
- `ROADMAP.md`
- `milestone-*.md` (root) and/or `requirements/milestones/milestone-N/MILESTONE-N.md`
- `session-notes/`
- `agent-context/harness/`

Use progressive disclosure ([SDLC Agents](https://github.com/dsilahcilar/sdlc-agents)): load only the artifacts relevant to the current Work ID, phase, and operation. Never list or read whole directories — use indexes. See `docs/sdlc-spdd/sdlc-agents-and-the-framework.md`.

## Context Loading

Load context on demand, not by bulk-reading directories. Keep working context small and relevant regardless of project size. See `docs/sdlc-spdd/context-loading-and-scaling.md`.

1. Start at `.sdlc/sessions/current-session.md` (gitignored hot brief with a Related Past Work digest) to resume the active Work ID and phase. For a quick orientation, run `./scripts/sdlc-spdd/sdlc.sh next` or invoke `/sdlc-spdd-whereami`.
2. Retrieve by relevance, not recency. Query with `sdlc-engine context retrieve --work-id <ID> [--area A] [--kind K]`, load bodies only for relevant record ids via `sdlc-engine context show <record-id>`, or use `sdlc-engine context digest --work-id <ID>`. A Work ID's contracts are `spdd/canvas/<WORK-ID>.md` and phase artifacts under `spdd/` — read those directly; use retrieval for cross-work lessons.
3. Never bulk-read `spdd/memory/lessons.jsonl` or whole directories. Staged records live in `.sdlc/staged/lessons.jsonl` (gitignored); agents stage via `./scripts/sdlc.sh capture ...` (or `sdlc-engine context persist-lesson`) and promote at retro/sync with `./scripts/sdlc.sh accept --work-id <ID>`. Work registry events live in `spdd/memory/registry.jsonl` (via `sdlc.sh claim/release` — never hand-edited). For static playbooks and harness files, use `./scripts/sdlc-spdd/resolve-agent-context.sh --phase <phase>`. When sqlite cache is enabled, `./scripts/sdlc.sh db query` may supplement retrieval. After `/sdlc-spdd-analysis`, run `index-spdd-analysis.sh <WORK-ID>` to stage an analysis record.

Optional Guide DICE backend: on-demand retrieval is always the baseline. If
`agent-context/harness/guide-dice.md` exists, resolve the backend at runtime
with `./scripts/sdlc-spdd/resolve-context-backend.sh --target .` and, only
when it reports `CONTEXT_BACKEND=guide-dice`, augment retrieval with the
`spdd_*` MCP tools (`spdd_workSubgraph`, `spdd_areaLessons`, `spdd_findByLabel`,
`spdd_projectionStats`). Never assume Guide is present, and never fail a
command because it is not.

Per-phase context budget:

- plan: the requirement, `spdd/analysis/<WORK-ID>-analysis.md`, `ROADMAP.md`, active milestone definition (root `milestone-*.md` or `requirements/milestones/milestone-N/`)
- analysis: the requirement (Scope Lock first), one retrieval query (`--kind analysis`), scoped code areas only
- architect: the Work ID canvas, retrieval query (`--kind decision`), `agent-context/harness/`
- code: the Work ID canvas, retrieval query (`--kind pitfall`); progress via `./scripts/sdlc.sh capture`
- api-test: the Work ID canvas Requirements/Operations, implemented endpoints for this Work ID
- review: the Work ID canvas, the diff, retrieval query (`--kind pattern`), `agent-context/harness/quality-gates.md`
- retro / sync: the Work ID canvas, review/sync artifacts, retrieval to avoid duplicate lessons; accept staged records

## Work Rules

- Use a Work ID for each unit of work, such as `FEAT-001-order-status-api`.
- Prefer prefixes: FEAT, BUG, REF, SPIKE, DOC, TEST, CHORE.
- Planning, architecture, retro, and sync requests must not modify application source code unless explicitly requested.
- Coding requests should implement exactly one approved operation from the canvas.
- Follow the canvas sections: Requirements, Entities, Approach, Structure, Operations, Norms, Safeguards.
- Update progress, review, retro, and sync artifacts when the active SDLC skill calls for it.
- Preserve useful project memory via `./scripts/sdlc.sh capture` and `./scripts/sdlc.sh accept` (never edit `spdd/memory/lessons.jsonl` by hand).
- Ask clarifying questions only when needed to prevent incorrect work; otherwise state assumptions in the canvas or staged session capture.
- For behavior or requirement changes, update the REASONS Canvas before changing code.
- For non-behavioral refactors, review the code change and then sync the canvas back to implementation reality.
- Treat `#SkillName` markers as explicit skill requests and `!SkillName` markers as exclusions. Resolve paths with `./scripts/sdlc-spdd/resolve-agent-context.sh --text "<prompt>"` or `--phase <phase>`; load only returned files. Record selected skills in the canvas or staged session capture when relevant.

## Context-Preserving Questions

When the user asks a question, answer using the current Work ID and relevant artifacts when available. If a Work ID is not provided, ask for it or infer it from the active files and say what you inferred.

Good question patterns:

    For FEAT-001, read @spdd/canvas/FEAT-001-order-status-api.md and answer: what operation should I do next?

    For BUG-003, run `sdlc-engine context digest --work-id BUG-003` and compare with the current diff. What context am I missing before coding?

    Using the current canvas and `sdlc-engine context retrieve --work-id <ID> --kind pitfall`, what risks should I check before review?
<!-- END SDLC-SPDD MANAGED CLAUDE GROUNDING -->
