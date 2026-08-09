# Installing into Your Project

Use this guide to install SDLC-SPDD Orchestrator into an application repository.

## Ops console (EXPERIMENTAL)

> **Experimental.** The visual ops console (`installer` / `console` / `dashboard`) is an
> orchestrator-dev convenience for dogfooding installs, SQLite, rollback, local
> Embabel Guide + Neo4j, and launching the ADF Viewer. It is **not** the supported
> consumer install path. Prefer `setup-agent-prompts.sh` / `upgrade-project.sh` /
> `verify-project-install.sh` for production installs.

Canonical explanation of **both GUIs** (console `:5051` + ADF Viewer `:5050`) and
how Guide fits: **[Ops console and ADF Viewer](ops-console.md)**.

```bash
python3 -m pip install -e './engine[viewer]'
./scripts/sdlc.sh console --target /path/to/app   # http://127.0.0.1:5051/
# aliases: installer · dashboard · ./scripts/visual-installer.sh
```

The console opens on the **Dashboard** tab by default. Other tabs: Install/Upgrade ·
Persistence · SQLite · Rollback · Guide · ADF (viewer process only).
Optional Guide stack: [DICE projection runbook](dice-projection-runbook.md) and [Guide flow](guide-flow.md).

## Which Install Path Should I Use?

| Situation | Use |
|-----------|-----|
| Prefer a UI for install or upgrade (experimental) | `./scripts/sdlc.sh console --target /path/to/app` — see [ops-console.md](ops-console.md) |
| New project with no SDLC-SPDD files | `setup-agent-prompts.sh --all` |
| Existing project initialized by an older orchestrator version | `upgrade-project.sh --all` |
| Cursor only | `init-project.sh --cursor` |
| GitHub Copilot only | `init-project.sh --copilot` |
| Claude Code only | `init-project.sh --claude` |
| Cursor, Copilot, and Claude Code | `setup-agent-prompts.sh --all` |

For backward compatibility, omitting assistant flags installs or upgrades Cursor
and GitHub Copilot only. Use `--all` or `--claude` when you want Claude Code
files.

## Fresh Install

From the orchestrator repository:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all

This installs a single framework home at `<repo>/sdlc-spdd/` (or at the repo root
when dogfooding this orchestrator). See the [install layout diagram](diagrams/09-install-layout.svg).

**Under `sdlc-spdd/`:**

- `requirements/` and `requirements/milestones/` (milestone-derived requirement stubs)
- `spdd/canvas/`, `spdd/tasks/`, `spdd/reviews/`, `spdd/sync/`
- `spdd/memory/lessons.jsonl` and `spdd/memory/registry.jsonl` (committed ledgers — never hand-edit)
- `harness/` — phase index, quality gates, validation rules
- `harness/skills/` — `#SkillName` skill files (for example `#TDD`, `#java-feature`)
- `ROADMAP.md`, milestone definition, `session-notes/`
- `scripts/` — workflow CLI and session scripts (`sdlc.sh`, `start-agent-session.sh`, …)

**At the repo root (adapter stubs):**

- `.cursor/commands/` and `.cursor/rules/sdlc-spdd.mdc`
- `.github/copilot-instructions.md` and `.github/prompts/`
- `CLAUDE.md` and `.claude/commands/`
- `.github/workflows/validate-sdlc-spdd-adapters.yml` (when both Cursor and Copilot adapters are installed)
- `docs/sdlc-spdd/` — target-local doc hub (`docs/sdlc-spdd/README.md`)

**Gitignored runtime** (created on first use, not committed):

- `.sdlc/sessions/` — hot briefs (`current-session.md`)
- `.sdlc/staged/lessons.jsonl` — captures awaiting accept
- `.sdlc/index.sqlite` — opt-in query cache
- `.sdlc/pointer`, `.sdlc/workflows/` — local Work ID pointer and phase/gate tracking

Under **`sdlc-spdd/scripts/`** (framework-owned; update via `upgrade-project.sh`):

- `sdlc.sh` (workflow CLI wrapper — `next`, `claim`, `capture`, `accept`, …)
- `start-agent-session.sh`
- `resync-agent-session.sh`
- `capture-session-memory.sh`
- `create-work-from-milestone.sh`
- `sync-roadmap-from-spdd.sh`
- `summarize-session-notes.sh`
- `validate-command-adapters.sh`
- `verify-agent-command-effects.sh`
- `verify-project-install.sh`

## Fresh Install for One Assistant

Cursor:

    ./scripts/init-project.sh --target /path/to/app --cursor

GitHub Copilot:

    ./scripts/init-project.sh --target /path/to/app --copilot

Claude Code:

    ./scripts/init-project.sh --target /path/to/app --claude

All three:

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot --claude

## Optional: Guide DICE Context Backend

Not every install has a Guide + Neo4j instance. Add `--with-guide` to opt an install
into the optional Guide DICE entity graph:

    ./scripts/init-project.sh --target /path/to/app --cursor --with-guide

This writes `sdlc-spdd/harness/guide-dice.md` (endpoint + tool reference).
Even with the marker present, availability is resolved at **runtime**:

    ./sdlc-spdd/scripts/resolve-context-backend.sh --target .
    # CONTEXT_BACKEND=guide-dice  → Guide is live; commands augment with spdd_* MCP tools
    # CONTEXT_BACKEND=files       → ledger-only context (normal, not an error)

Commands never fail because Guide is absent or down. To opt in later, copy
`templates/agent-context/harness/guide-dice.md` into
`sdlc-spdd/harness/`; to opt out, delete it. Full setup:
[dice-projection-runbook.md](dice-projection-runbook.md).

## Preview Before Installing

    ./scripts/init-project.sh --target /path/to/app --cursor --copilot --claude --dry-run

or:

    ./scripts/setup-agent-prompts.sh --target /path/to/app --all --dry-run

## Upgrade an Existing Install

If the project already has SDLC-SPDD files from an older version:

    ./scripts/upgrade-project.sh --target /path/to/app --all --dry-run
    ./scripts/upgrade-project.sh --target /path/to/app --all

The upgrade script updates framework-owned files and preserves application source,
requirements, canvases, reviews, sync logs, and the lessons ledger. Legacy memory
layouts are converted by `sdlc-engine storage migrate`; consolidating scattered
paths into `sdlc-spdd/` uses `upgrade --consolidate` — see
[Framework upgrade](framework-upgrade.md).

Backups of overwritten framework files are stored under:

    /path/to/app/.sdlc-spdd-upgrade-backups/<timestamp>/

## After Install

Open `/path/to/app` in Cursor, a Copilot-enabled editor, or Claude Code.

In **AI chat** (not the terminal), initialize project context. `/sdlc-spdd-init` is an assistant command, not a shell command — see [How to run assistant commands](initialization-and-invocation.md#how-to-run-assistant-commands).

**Cursor:** Chat → `/sdlc-spdd-init`

**Copilot:** Chat → `/sdlc-spdd-init` or `#prompt:sdlc-spdd-init`

**Claude Code:** `/sdlc-spdd-init`

    /sdlc-spdd-init

Optional — orient and claim from the **terminal**:

    cd /path/to/app
    ./sdlc-spdd/scripts/sdlc.sh claim <WORK-ID>
    ./sdlc-spdd/scripts/sdlc.sh next

Or create a first session brief:

    ./sdlc-spdd/scripts/sdlc.sh start
    # or: ./sdlc-spdd/scripts/start-agent-session.sh --target . --phase init

Then ask:

    Read @.sdlc/sessions/current-session.md and continue with /sdlc-spdd-init.

## Verify the Install

`init-project.sh` and `upgrade-project.sh` run verification automatically at the end of a successful install or upgrade.

From your **installed target project** (`cd` into the app):

    ./sdlc-spdd/scripts/verify-project-install.sh --target .

With assistant adapters:

    ./sdlc-spdd/scripts/verify-project-install.sh --target . --require-cursor
    ./sdlc-spdd/scripts/verify-project-install.sh --target . --require-copilot
    ./sdlc-spdd/scripts/verify-project-install.sh --target . --require-claude
    ./sdlc-spdd/scripts/verify-project-install.sh --target . --require-cursor --require-copilot --require-claude

From the orchestrator repository during development:

    ./scripts/verify-project-install.sh --target /path/to/app

The script asserts the **three-part scaffold**, with emphasis on Planning artifacts:

| Part | Verified paths |
|------|----------------|
| **Planning** | `requirements/`, `requirements/milestones/`, `session-notes/`, `ROADMAP.md`, `milestone-*.md` |
| **SPDD** | `spdd/canvas/`, `spdd/tasks/`, `spdd/reviews/`, `spdd/sync/`, `spdd/memory/lessons.jsonl`, `spdd/memory/registry.jsonl` |
| **SDLC** | `harness/`, `harness/skills/`, runtime scripts including `sdlc.sh`, gitignored `.sdlc/` layout |

Exit code `0` means the install is complete. Non-zero lists missing items and suggests re-running setup.

## What Not to Edit by Hand

Avoid hand-editing generated framework prompt files unless you intend to keep local customizations:

- `.cursor/commands/sdlc-spdd-*.md` (includes `sdlc-spdd-whereami`)
- `.cursor/rules/sdlc-spdd.mdc`
- `.github/prompts/sdlc-spdd-*.prompt.md`
- `.github/copilot-instructions.md`
- `.claude/commands/sdlc-spdd-*.md`
- `CLAUDE.md`
- `sdlc-spdd/scripts/*.sh`
- `docs/sdlc-spdd/*.md`
- `spdd/memory/lessons.jsonl` and `spdd/memory/registry.jsonl` (written only by `accept` and `claim`/`release`)

Team-specific process guidance and custom skills belong in:

- `sdlc-spdd/harness/skills/` — add `.md` skill files; request with `#SkillName`
- project docs outside `docs/sdlc-spdd/`

**Local agent state** (gitignored, do not commit): `.sdlc/pointer`, `.sdlc/workflows/`, `.sdlc/sessions/`, `.sdlc/staged/`.

Keep application-specific documentation outside `docs/sdlc-spdd/` so framework upgrades can refresh SDLC-SPDD docs safely.

## Troubleshooting

If slash commands do not appear:

1. Confirm the files were installed.
2. Reload the editor window.
3. For Copilot, run `Chat: Run Prompt` and choose the prompt file.
4. Confirm the project root is the folder opened in the editor.

If an upgrade overwrote local prompt customizations:

1. Check `.sdlc-spdd-upgrade-backups/<timestamp>/`.
2. Compare the old prompt to the new prompt.
3. Move team-specific guidance into `harness/skills/` where possible.

## Read Next

- [Ops console and ADF Viewer](ops-console.md)
- [First day with SDLC-SPDD](first-day-with-sdlc-spdd.md)
- [Agent session scripts](agent-session-scripts.md)
- [Framework upgrade](framework-upgrade.md)
