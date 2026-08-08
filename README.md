# SDLC-SPDD Orchestrator

A multi-assistant scaffold for disciplined AI-assisted delivery — Planning + SPDD
(REASONS canvases) + SDLC phase commands — for Cursor, GitHub Copilot, and Claude Code.

**Latest release:** [`v2.0.0a6`](https://github.com/jmjava/sdlc-spdd-orchestrator/releases/tag/v2.0.0a6)
([#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109))

## What's new (`v2.0.0a6`)

The agent-context cleanup program is on `main`. Runtime noise left the commit stream;
contracts and progress stay lean and queryable.

| Change | What you get |
| ------ | ------------ |
| **Lean stay-set** | Requirements + REASONS canvases + compact memory under `spdd/memory/` (lessons, pointers, context-index, progress entries) |
| **Hot sessions** | Session briefs in gitignored `.sdlc/sessions/` (not `agent-context/sessions/`) |
| **Triple-path context** | Persist/retrieve across **git pointers + SQLite + optional Guide** — soft-fail secondaries; toggle with `CONTEXT_BACKENDS` or the ops console **Persistence** tab |
| **Quiet mode** | `SDLC_QUIET=1` / harness marker — product work without T## dogfood gravity |
| **Work-scoped resolve** | Shared progress ledgers inject as `.sdlc/resolved/progress-<WORK-ID>.md` excerpts |

Program docs: [docs/agent-context-cleanup/](docs/agent-context-cleanup/)

## Current focus

**ADF template library + Vue3 ops console** — turn planning iterations into templated
Jira ADF (header/body/footer combos) and replace the Flask dogfood UI with Vue3.

- Plan: [docs/adf-template-library-and-vue3-console.md](docs/adf-template-library-and-vue3-console.md)
- Branch / PR: [`cursor/adf-templates-vue3-console-decf`](https://github.com/jmjava/sdlc-spdd-orchestrator/tree/cursor/adf-templates-vue3-console-decf) · [#114](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/114)

## Local tools

Two localhost apps (Flask today; Vue3 console is the migration target). Prefer shell
install scripts for production targets; the ops console is experimental dogfood UI.

| UI | Port | Start | Job |
| -- | ---- | ----- | --- |
| **Ops console** | `5051` | `./scripts/sdlc.sh console --target /path/to/app` | Install/upgrade, **Persistence**, SQLite, rollback, optional Guide stack, launch ADF Viewer |
| **ADF Viewer** | `5050` | `./scripts/sdlc.sh viewer` | Edit `adf/*.adf.json`, explicit Jira sync |

```bash
python3 -m pip install -e './engine[viewer]'
./scripts/sdlc.sh console --target .          # http://127.0.0.1:5051/
./scripts/sdlc.sh viewer --root . --port 5050 # http://127.0.0.1:5050/
```

Details: [docs/ops-console.md](docs/ops-console.md) · [docs/adf-viewer.md](docs/adf-viewer.md)

**Demo videos:** [GitHub Pages intros](https://jmjava.github.io/sdlc-spdd-orchestrator/)

## How the three parts fit

| Part | Answers | Artifacts |
| ---- | ------- | --------- |
| **Planning** | _Why_ the work matters | `ROADMAP.md`, milestones, `requirements/`, `session-notes/` |
| **SPDD** | _What_ to build (and not) | `spdd/canvas/<WORK-ID>.md`, `spdd/analysis/`, `spdd/reviews/` |
| **SDLC** | _Who acts when_ / handoffs | phase commands, `.sdlc/sessions/`, `spdd/memory/`, workflow CLI |

Optional Guide Neo4j projection is just another **context backend** (off by default;
files + SQLite still work). See [docs/guide-flow.md](docs/guide-flow.md) only if you
opt in — it is not required to use this framework.

> We dogfood the framework on itself via Work IDs under [`spdd/canvas/`](spdd/canvas/)
> and [`requirements/milestones/`](requirements/milestones/). Roadmap posture:
> [ROADMAP.md](ROADMAP.md).

## How commands work

| Kind | Looks like | Where |
| ---- | ---------- | ----- |
| **Assistant** (AI chat) | `/sdlc-spdd-init`, `/sdlc-spdd-plan @requirements/foo.md` | Cursor / Copilot / Claude Code chat in the **target** project |
| **Shell — install** | `./scripts/setup-agent-prompts.sh --target …` | Terminal in the **orchestrator** clone |
| **Shell — daily use** | `./scripts/sdlc-spdd/sdlc.sh next` | Terminal in an **installed target** |
| **Shell — dogfood** | `./scripts/sdlc.sh next` | Terminal in this repo |

**`/sdlc-spdd-*` is not a terminal command.** Full detail:
[How to run assistant commands](docs/initialization-and-invocation.md#how-to-run-assistant-commands).

## Quick start (~5 minutes)

From this repo, point `--target` at your application:

```bash
git clone https://github.com/jmjava/sdlc-spdd-orchestrator.git
cd sdlc-spdd-orchestrator

./scripts/setup-agent-prompts.sh --target /path/to/your/project --all
./scripts/verify-project-install.sh --target /path/to/your/project
```

Open the **target** in your assistant and run `/sdlc-spdd-init` in chat.

Then: [First day with SDLC-SPDD](docs/first-day-with-sdlc-spdd.md).

Upgrade an existing install (does not overwrite app source, canvases, or notes):

```bash
./scripts/upgrade-project.sh --target /path/to/your/project --all
```

## Day-one flow

Chat commands are `/sdlc-spdd-*`; shell lines use `./scripts/sdlc-spdd/` in a target
(or `./scripts/sdlc.sh` when dogfooding this repo).

```bash
/sdlc-spdd-init

./scripts/sdlc-spdd/sdlc.sh claim FEAT-001-my-feature
./scripts/sdlc-spdd/sdlc.sh start
# Paste Resume Prompt from .sdlc/sessions/current-session.md — load only Resolved Context

/sdlc-spdd-analysis @requirements/my-feature.md @ROADMAP.md
/sdlc-spdd-plan @spdd/analysis/FEAT-001-my-feature-analysis.md
/sdlc-spdd-architect @spdd/canvas/FEAT-001-my-feature.md
/sdlc-spdd-code @spdd/canvas/FEAT-001-my-feature.md operation T01
/sdlc-spdd-review @spdd/canvas/FEAT-001-my-feature.md

./scripts/sdlc-spdd/sdlc.sh capture --work-id FEAT-001-my-feature --phase code \
  --summary "Completed T01" --validation "tests passed"
```

Orient anytime: `./scripts/sdlc-spdd/sdlc.sh next` or `/sdlc-spdd-whereami`.

## Context loading (every session)

Progressive disclosure — not whole-directory dumps.

1. **Tier 1** — small always-on grounding (`.cursor/rules/sdlc-spdd.mdc`, Copilot instructions, or `CLAUDE.md`).
2. **Tier 2** — `sdlc.sh start` writes `.sdlc/sessions/current-session.md` with a **Resolved Context** table (phase files, extensions, Work ID artifacts, area-filtered index rows, work-scoped progress excerpt).
3. Paste the **Resume Prompt**; load only listed files.
4. **Capture** grows lean memory (`spdd/memory/…`) + SQLite for the next run.

```bash
./scripts/sdlc-spdd/sdlc.sh claim <WORK-ID>
./scripts/sdlc-spdd/sdlc.sh start
./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code --work-id <WORK-ID>
```

More: [Context loading and scaling](docs/context-loading-and-scaling.md)

## Core assistant commands

| Command | Use it for |
| ------- | ---------- |
| `/sdlc-spdd-whereami` | Orient: registry, Work ID, phase, gates, next command |
| `/sdlc-spdd-init` | Initialize project context |
| `/sdlc-spdd-analysis` | Domain keywords, scoped scan, analysis artifact |
| `/sdlc-spdd-plan` | Create REASONS Canvas from accepted analysis |
| `/sdlc-spdd-architect` | Harden the canvas before coding |
| `/sdlc-spdd-code` | Implement one approved operation |
| `/sdlc-spdd-api-test` | Generate API test script |
| `/sdlc-spdd-review` | Compare implementation to the canvas |
| `/sdlc-spdd-prompt-update` | Update the canvas when acceptance criteria change |
| `/sdlc-spdd-retro` | Capture reusable learnings |
| `/sdlc-spdd-sync` | Reconcile accepted drift back into prompt artifacts |
| `/sdlc-spdd-commit-message` | Draft a paste-ready commit message from the diff |

## Core scripts

| Script | Use it for |
| ------ | ---------- |
| `scripts/setup-agent-prompts.sh` | Install into a target |
| `scripts/upgrade-project.sh` | Upgrade framework-owned files |
| `scripts/sdlc-spdd/sdlc.sh` | Daily CLI: `next`, `claim`, `resume`, `advance`, `capture`, `team`, `list-work`, `db`, `console`, … |
| `scripts/sdlc-spdd/start-agent-session.sh` | Hot session brief + Resume Prompt |
| `scripts/sdlc-spdd/capture-session-memory.sh` | Persist summary / lessons / progress |
| `scripts/sdlc-spdd/resolve-agent-context.sh` | Progressive disclosure paths |
| `scripts/sdlc-spdd/verify-agent-command-effects.sh` | Lean-first side-effect checks |

Python engine: `pip install -e './engine[dev]'` then `sdlc-engine …`
(workflow, context persist/retrieve, issue sync, ADF helpers).

## Repository layout

| Path | Purpose |
| ---- | ------- |
| `docs/` | Guides, runbooks, [agent-context cleanup](docs/agent-context-cleanup/), research |
| `scripts/` | Install, upgrade, validation, target runtime templates |
| `engine/` | Python orchestration engine (`sdlc-engine`) + ops console / ADF viewer |
| `templates/` | Canvas / assistant command / project-doc templates |
| `spdd/` | Canvases, analysis, reviews, lean `memory/` stay-set |
| `agent-context/` | Install harness, playbooks, extensions (not the hot session bus) |
| `requirements/` | Milestone / Work ID requirements (Jira-oriented) |

## Documentation map

**Start here**

1. [First day with SDLC-SPDD](docs/first-day-with-sdlc-spdd.md)
2. [Three-part operating path](docs/three-part-operating-path.md)
3. [Installing into your project](docs/installing-into-your-project.md)
4. [Daily runbook](docs/daily-runbook.md)
5. [Agent-context cleanup](docs/agent-context-cleanup/) — lean stay-set + triple-path
6. [Ops console](docs/ops-console.md) · [ADF Viewer](docs/adf-viewer.md)

**Also useful**

- [Useful concepts and commands](docs/useful-concepts-and-commands.md)
- [Local SQLite index](docs/local-sqlite-index.md)
- [Jira runbook](docs/jira-runbook.md) · [Jira-compatible requirements](docs/jira-compatible-requirements-format.md)
- [Changelog](CHANGELOG.md) · full index in [docs/README.md](docs/README.md)

## What this is not

Not a compiled multi-agent runtime, and not a replacement for Cursor, Copilot,
Claude Code, Jira, or OpenSPDD. It is a repository-based operating model that makes
AI-assisted work more governable, reviewable, and reusable.

## License

MIT

## Attribution

Inspired by [SDLC Agents](https://github.com/dsilahcilar/sdlc-agents) and
[OpenSPDD](https://github.com/gszhangwei/open-spdd). Not an official extension of
either project.
