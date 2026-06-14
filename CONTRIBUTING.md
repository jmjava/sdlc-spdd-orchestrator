# Contributing

Thanks for contributing to SDLC-SPDD Orchestrator.

## Principles

- Keep Markdown and shell scripts as the primary artifacts for MVP
- Preserve safe defaults: no overwrite without `--force`
- Keep no-code agent phases free of application code changes
- Implement one canvas operation per coding session
- Match existing conventions in the repository

## Script Paths: Orchestrator vs Target

This repository and installed target applications use different script paths:

| Context | Where you `cd` | Script path | Examples |
|---------|----------------|-------------|----------|
| **Orchestrator repo** | `sdlc-spdd-orchestrator/` | `./scripts/<name>.sh` | `setup-agent-prompts.sh`, `init-project.sh`, `upgrade-project.sh`, `verify-project-install.sh`, `render-diagrams.sh` |
| **Installed target app** | your application root | `./scripts/sdlc-spdd/<name>.sh` | `start-agent-session.sh`, `capture-session-memory.sh`, `verify-project-install.sh` |

**Rule:** setup/install/upgrade always run from the **orchestrator clone** with `--target /path/to/app`. Daily session scripts run from the **target project** with `--target .` (or omit when already in the app root).

`init-project.sh` copies runtime scripts (including `verify-project-install.sh`) into the target at `scripts/sdlc-spdd/`. Docs must label which context applies — do not use `./scripts/sdlc-spdd/...` in examples meant for the orchestrator repo.

Doc paths follow the same pattern:

| Context | Documentation |
|---------|---------------|
| This orchestrator repo | `docs/*.md` |
| Installed target application | `docs/sdlc-spdd/*.md` |

Generated session briefs reference `docs/sdlc-spdd/…` because they are written for target projects.

## Three-Part Design Mandate

**Planning, SPDD, and SDLC are three required parts — not one documentation theme.**

Before removing folders, skipping install steps, or consolidating docs:

1. Read [Three-part design mandate](docs/three-part-operating-path.md#three-part-design-mandate).
2. Identify which part owns the artifact.
3. **Never delete Planning artifacts** (`ROADMAP.md`, `milestone-*.md`, `requirements/milestones/`, `session-notes/`) to simplify code — they are the Planning part.
4. **Never replace SPDD canvases with planning files** — planning informs; canvas governs.
5. **Never drop SDLC handoffs** — session briefs and memory capture are required.

`requirements/milestones/` is Planning (milestone → plan bridge). `requirements/` is Planning (ad-hoc). Both stay.

### Whole-ecosystem grounding is the norm for every assistant

Every supported assistant **must** ship an always-on grounding file so all work —
not just `/sdlc-spdd-*` command runs — is grounded in the full ecosystem
(Planning + SPDD + SDLC):

- Cursor: `templates/cursor/rules/sdlc-spdd.mdc` (`alwaysApply: true`) → `.cursor/rules/`
- GitHub Copilot: `templates/copilot/copilot-instructions.md` → `.github/copilot-instructions.md`
- Claude Code: `templates/claude/CLAUDE.md` → `CLAUDE.md`

When you add a new assistant or edit these files, keep the shared operating-model
anchors (lifecycle line, `## Operating Model`, `## Work Rules`) and the Planning
(`ROADMAP.md`, `milestone-*.md`, `session-notes/`), SPDD (`spdd/canvas/`), and
SDLC (`agent-context/sessions/`, `agent-context/memory/`) artifacts.
`validate-command-adapters.sh` enforces this in CI; run
`./tests/test-adapter-install.sh` before pushing.

## Documentation Consistency Checklist

Before merging doc or script changes that touch the three-part model (Planning, SPDD, SDLC), verify:

- [ ] **Three-part mandate** — no Planning, SPDD, or SDLC artifacts removed or conflated; see [design mandate](docs/three-part-operating-path.md#three-part-design-mandate)

- [ ] **Operating path** — behavior matches [three-part-operating-path.md](docs/three-part-operating-path.md)
- [ ] **Resume prompt** — docs say paste from `current-session.md`; do not add hand-rolled resume prompt variants
- [ ] **Conflict resolution** — one canonical table in three-part operating path; value guides link there instead of duplicating full tables
- [ ] **Onboarding order** — first-day → three-part → rest (same in `README.md` and `docs/README.md`)
- [ ] **Milestone work map** — section is `## Linked Work` with columns `Work ID | Canvas | Requirement | Status | Notes`; Requirement path is `requirements/milestones/<WORK-ID>.md`
- [ ] **Milestone requirements** — `create-work-from-milestone.sh` writes canonical stubs to `requirements/milestones/`; ad-hoc requirements stay in `requirements/`
- [ ] **Milestone auto-detect** — `capture-session-memory.sh` and `start-agent-session.sh` auto-detect when `--milestone` omitted and Work ID is in `milestone-*.md`
- [ ] **Resync semantics** — `--check-only` does not create a session brief; `--from-canvas`/`--from-feature` reconciles and creates one
- [ ] **Prompt standards** — Session is default; SPDD and Planning are drill-downs; link [Which prompt standard?](docs/session-prompt-standard.md#which-prompt-standard)
- [ ] **Script output** — if a script prints “next step” prompts, they align with the matching prompt standard doc
- [ ] **Diagrams** — if you changed a Mermaid diagram, `./scripts/render-diagrams.sh --check` passes; regenerate committed exports with `./scripts/render-diagrams.sh`
- [ ] **Daily doc roles** — prompts stay in `session-prompt-standard.md`; step table in `workflow.md`; rules/checklists in `daily-runbook.md`; Cursor/Copilot/Claude Code syntax in `initialization-and-invocation.md`; concepts in `useful-concepts-and-commands.md`; commands in `sdlc-spdd-cheat-sheet.md` (link, do not duplicate)
- [ ] **Target docs hub** — `docs/README.md` is orchestrator-only; installed projects use `templates/project-docs/docs-sdlc-spdd-README.md` → `docs/sdlc-spdd/README.md` (do not copy orchestrator `docs/README.md` to targets)
- [ ] **Assistant vs shell** — `/sdlc-spdd-*` is chat (link [How to run assistant commands](docs/initialization-and-invocation.md#how-to-run-assistant-commands)); `./scripts/` is terminal
- [ ] **Script paths** — install/setup from orchestrator `./scripts/`; daily/runtime in target `./scripts/sdlc-spdd/`; label which context in examples

## Diagrams

Diagrams are authored as Mermaid blocks inside the Markdown docs (the top-level `README.md` adoption-path diagram is the main one). Rendered exports live in `docs/diagrams/` as SVG and PNG for environments that do not render Mermaid (PDF exports, some viewers).

Rendering is reproducible and uses a system-installed Chrome/Chromium — no browser download:

    ./scripts/render-diagrams.sh            # render SVG + PNG to docs/diagrams
    ./scripts/render-diagrams.sh --check    # validate only (good for CI), non-zero exit on failure

Override the browser with `PUPPETEER_EXECUTABLE_PATH` if auto-detection fails. Launch flags live in `scripts/mermaid-puppeteer.json`. Label rendering uses `scripts/mermaid-config.json` (`htmlLabels: false`) so SVGs display in IDE previews.

CI: `.github/workflows/validate-diagrams.yml` runs `./scripts/render-diagrams.sh --check` on PRs that touch docs or diagram scripts.

## Development Setup

1. Clone the repository
2. Make changes in focused PRs
3. Run canvas validation when touching canvas files:

       ./scripts/validate-reasons-canvas.sh examples/spring-boot-order-api/spdd/canvas/FEAT-001-order-status-api.md

4. Test scripts with `--dry-run` when adding file-writing behavior
5. Test runtime scripts from `./scripts/` in this repo; confirm `init-project.sh` still copies them to `scripts/sdlc-spdd/` in targets
6. Run `./scripts/verify-project-install.sh --target <test-app>` after init changes; Planning checks must include `requirements/milestones/`
7. Follow the confidence stack in `TESTING.md` (CI gates + local smoke + planning sync checks) for command/prompt/script changes

## Pull Requests

- Link related REASONS Canvas or work ID when applicable
- Fill in the PR template checklist
- Keep scope minimal and reviewable
- Run through the documentation consistency checklist when touching docs or session scripts

## Attribution

When borrowing ideas from SDLC Agents or OpenSPDD, preserve attribution and avoid vendoring large upstream portions.

## Planned / Not Installed

`templates/agent-overlays/` exists for future per-role overlays but is **not** copied by install scripts today. Target projects use Cursor commands, Copilot prompts, Claude Code commands, and playbooks. See [design-decisions.md](docs/design-decisions.md).
