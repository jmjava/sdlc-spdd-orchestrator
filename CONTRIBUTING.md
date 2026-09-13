# Contributing

Thanks for contributing to SDLC-SPDD Orchestrator.

## Principles

- Keep Markdown and shell scripts as the primary artifacts for MVP
- Preserve safe defaults: no overwrite without `--force`
- Keep no-code agent phases free of application code changes
- Implement one canvas operation per coding session
- Match existing conventions in the repository

## Developer Notes: How the Project Evolves (Kent Beck)

The framework evolves through Kent Beck's progression — **make it work → make it
right → make it fast** — applied to the project as a whole, not to individual
branches. This is a planning posture, not a branching strategy: we stay on one
line of work and advance the framework through the stages in order. The
authoritative stage table and current state live in
[ROADMAP.md → Delivery posture](sdlc-spdd/ROADMAP.md#delivery-posture-kent-beck-make-it-work--make-it-right--make-it-fast).

**Where we are now:** transitioning from *make it work* (the MVP functions end to
end) to *make it right* — refactoring the existing framework for readability,
maintainability, and extensibility. Prompt optimization, and the measurement that
drives it, is *make it fast* and comes last.

What this means when you contribute:

1. **Name the stage your change serves.** In the PR and any REASONS Canvas, say
   whether the work is making it work, right, or fast. Use the
   [Stage classification rubric](sdlc-spdd/ROADMAP.md#stage-classification-rubric) — including
   its one-line litmus and the worked example — to decide. It is the single
   source of truth for how work is categorized.
2. **Default new framework work to "make it right" (a refactor).** Near-term work
   makes the code and docs we already have easier to read, change, and extend; it
   does not add new optimization capability.
3. **Prompt optimization is "make it fast" and comes last.** This includes the
   measurement that supports it (the optimization ledger, leading indicators). Do
   not start it until the framework is structurally right.
4. **Do not optimize an unmeasured system** — but build that measurement as the
   first step *of* "make it fast", not as a make-it-right prerequisite that jumps
   the queue.

### Boundary: the development posture never ships

The make-it-work/right/fast posture is **how we develop the orchestrator** — it is
not a model we impose on projects that *use* the framework. Target teams have their
own roadmaps and priorities. Keep our internal posture out of everything that
installs into a target project.

- **Shipped surfaces (must stay neutral):** `templates/**`, every `docs/*.md`
  that is *not* listed as orchestrator-only in
  `scripts/lib/shipped-docs-boundary.sh` (installed as `docs/sdlc-spdd/`), the
  grounding files
  (`templates/{claude/CLAUDE.md,copilot/copilot-instructions.md,cursor/rules/sdlc-spdd.mdc}`),
  and the `templates/agent-context/` harness files that install copies.
- **Internal-only surfaces (posture allowed):** `sdlc-spdd/ROADMAP.md` (dogfood home —
  targets get `templates/project-docs/ROADMAP.md` instead), this `CONTRIBUTING.md`, the repo-root
  `README.md`, and orchestrator-only docs such as
  `docs/contributing-command-specs.md`, `docs/contributing-skills.md`,
  `docs/engine-v2.md`, `docs/dice-projection-runbook.md`, and
  `docs/mcp-guide-for-agents.md`.
- **Never** put `make it work/right/fast`, `Kent Beck`, or `Delivery posture/stage`
  language into a shipped surface. The posture lives only in the internal files above.
- **Framework capabilities may ship, but described neutrally.** The
  prompt-optimization ledger (FEAT-004) is a legitimate, optional capability — when
  its docs/templates ship, they describe *what it does* ("record whether a prompt
  change improved an outcome"), never *our* reason for building it.

This boundary is enforced in CI by `./scripts/check-posture-boundary.sh`.

See [design-decisions.md](docs/design-decisions.md) for the architectural "why"
behind these choices. (That file ships to targets, so it must not carry posture
language either.)

## Script Paths: Orchestrator vs Target

This repository and installed target applications use different script paths:

| Context | Where you `cd` | Script path | Examples |
|---------|----------------|-------------|----------|
| **Orchestrator repo** | `sdlc-spdd-orchestrator/` | `./scripts/<name>.sh` | `setup-agent-prompts.sh`, `init-project.sh`, `upgrade-project.sh`, `verify-project-install.sh`, `render-diagrams.sh` |
| **Installed target app** | your application root | `./sdlc-spdd/scripts/<name>.sh` | `start-agent-session.sh`, `capture-session-memory.sh`, `verify-project-install.sh` |

**Rule:** setup/install/upgrade always run from the **orchestrator clone** with `--target /path/to/app`. Daily session scripts run from the **target project** with `--target .` (or omit when already in the app root).

`init-project.sh` copies runtime scripts (including `verify-project-install.sh`) into the target at `sdlc-spdd/scripts/`. Docs must label which context applies — do not use `./sdlc-spdd/scripts/...` in examples meant for the orchestrator repo.

Doc paths follow the same pattern:

| Context | Documentation |
|---------|---------------|
| This orchestrator repo | `docs/*.md` |
| Installed target application | `docs/sdlc-spdd/*.md` |

Generated session briefs reference `docs/sdlc-spdd/…` because they are written for target projects.

## Command adapters and extensions

When changing assistant commands or the extension mechanism:

| Task | Guide |
|------|-------|
| Edit Cursor/Copilot/Claude command text | [docs/contributing-command-specs.md](docs/contributing-command-specs.md) — edit `spec/commands/`, then `./scripts/generate-command-adapters.sh` |
| Add harness skills | [docs/contributing-skills.md](docs/contributing-skills.md) |
| Run the integration merge gate | [TESTING.md](TESTING.md#integration-merge-gate) — `./tests/test-integration-merge.sh` |

## Three-Part Design Mandate

**Planning, SPDD, and SDLC are three required parts — not one documentation theme.**

Before removing folders, skipping install steps, or consolidating docs:

1. Read [Three-part design mandate](docs/three-part-operating-path.md#three-part-design-mandate).
2. Identify which part owns the artifact.
3. **Never delete Planning artifacts** (`sdlc-spdd/ROADMAP.md`, `milestone-*.md`, `sdlc-spdd/requirements/milestones/`, `sdlc-spdd/session-notes/`) to simplify code — they are the Planning part.
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
(`sdlc-spdd/ROADMAP.md`, `milestone-*.md`, `sdlc-spdd/session-notes/`), SPDD (`sdlc-spdd/spdd/canvas/`), and
SDLC (`.sdlc/sessions/`, `spdd/memory/lessons.jsonl`) runtime.
`validate-command-adapters.sh` enforces this in CI; run
`./tests/test-adapter-install.sh` before pushing.

## Documentation Consistency Checklist

Before merging doc or script changes that touch the three-part model (Planning, SPDD, SDLC), verify:

- [ ] **Workflow CLI** — daily runbook, first-day walkthrough, cheat sheet, and session prompt standard teach `sdlc.sh` (`next`, `claim`, `capture`) not raw scripts alone
- [ ] **Workflow chat commands** — `/sdlc-claim`, `/sdlc-shelf`, `/sdlc-advance`, `/sdlc-next`, `/sdlc-team` appear alongside shell equivalents where users start/claim/orient
- [ ] **Pointer + team registry** — docs explain `.sdlc/pointer` / `.sdlc/workflows/` (local) vs `work-registry.tsv` (committed); claim/release commit reminder present
- [ ] **Whereami / next** — `/sdlc-next` and `/sdlc-spdd-whereami` in assistant orientation tables (README, cheat sheet, cursor/copilot/claude usage)
- [ ] **Jira draft** — milestone `## Jira` convention referenced from runbook, cheat sheet, planning prompts where Jira drafts appear
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
- [ ] **Diagrams** — if you changed PlantUML under `docs/diagrams/*.puml`, `./scripts/render-diagrams.sh --check` passes; regenerate committed SVG exports with `./scripts/render-diagrams.sh`
- [ ] **Daily doc roles** — prompts stay in `session-prompt-standard.md`; step table in `workflow.md`; rules/checklists in `daily-runbook.md`; Cursor/Copilot/Claude Code syntax in `initialization-and-invocation.md`; concepts in `useful-concepts-and-commands.md`; commands in `sdlc-spdd-cheat-sheet.md` (link, do not duplicate)
- [ ] **Target docs hub** — `docs/README.md` is orchestrator-only; installed projects use `templates/project-docs/docs-sdlc-spdd-README.md` → `docs/sdlc-spdd/README.md` (do not copy orchestrator `docs/README.md` to targets)
- [ ] **Assistant vs shell** — `/sdlc-spdd-*` is chat (link [How to run assistant commands](docs/initialization-and-invocation.md#how-to-run-assistant-commands)); `./scripts/` is terminal
- [ ] **Script paths** — install/setup from orchestrator `./scripts/`; daily/runtime in target `./sdlc-spdd/scripts/`; label which context in examples

## Diagrams

System architecture diagrams are **PlantUML** sources in `docs/diagrams/*.puml`. Rendered SVG exports live in `docs/diagrams/` for viewers that do not render PlantUML inline.

    ./scripts/render-diagrams.sh            # render SVG to docs/diagrams
    ./scripts/render-diagrams.sh --check    # validate only (CI), non-zero exit on failure

Requires Java. The PlantUML jar is fetched to `~/.cache/plantuml` on first use.

CI: `.github/workflows/validate-diagrams.yml` runs `./scripts/render-diagrams.sh --check` on PRs that touch diagram sources.

## Development Setup

1. Clone the repository
2. Make changes in focused PRs
3. Run canvas validation when touching canvas files:

       ./scripts/validate-reasons-canvas.sh examples/spring-boot-order-api/spdd/canvas/FEAT-001-order-status-api.md

4. Test scripts with `--dry-run` when adding file-writing behavior
5. Test runtime scripts from `./scripts/` in this repo; confirm `init-project.sh` still copies them to `sdlc-spdd/scripts/` in targets
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
