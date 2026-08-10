# Testing Strategy

This project treats `/sdlc-spdd-*` command validation as a **confidence stack**, not
100% deterministic automation.

Cursor/Copilot/Claude Code chat runtime is nondeterministic and UI-driven. We verify
what can be proven automatically, then run a short manual smoke for the rest.

## Confidence Stack

| Level | Goal | Fully automatable? | How |
|------|------|---------------------|-----|
| 1. Deterministic CI | Prevent adapter/config drift | Yes | GitHub Actions + validator scripts |
| 2. Post-invocation effects | Prove command side-effects happened | Mostly | `verify-agent-command-effects.sh` |
| 3. Manual chat smoke | Validate real chat invocation path | No | Short guided run in Cursor/Copilot/Claude Code |

## Engine test suites (3 packages)

| Suite | Path | Command | CI |
|-------|------|---------|-----|
| **1 — Unit** | `engine/tests_unit/` | `./scripts/run-test-suites.sh unit` | `test-sdlc-engine.yml` job `suite-1-unit` |
| **2 — Local integration** | `engine/tests_integration/` | `./scripts/run-test-suites.sh integration` | `test-sdlc-engine.yml` job `suite-2-integration` |
| **3 — E2E integration** | `engine/tests_e2e/` | `./scripts/run-test-suites.sh e2e [--guide]` | `test-e2e-playwright.yml`, `test-guide-stack-experimental.yml`, GitHub Issues job |

Local mirror: `./scripts/test-ci-local.sh` (suites 1–3), `./scripts/test-ci-local.sh --guide` (suite 3 includes Guide stack).

### Preflight (run before long suites)

Fail in **seconds** instead of after a 600s Guide wait or hung `/sse` curl:

```bash
./scripts/run-test-suites.sh preflight all          # layout, Python 3.12, stale jobs
./scripts/run-test-suites.sh preflight e2e --guide  # + Guide stack / append-ingest state
./scripts/run-test-suites.sh unit --clean-stale     # auto-preflight + kill stale pytest/curl
```

Probe Guide with `curl -sf --max-time 3 http://127.0.0.1:21337/actuator/health` — **never** bare `curl …/sse` (hangs forever).

If preflight reports missing Python 3.12, install the interpreter first (CI uses **3.12** everywhere):

| OS | Install |
|----|---------|
| **Ubuntu 22.04** | `sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt update && sudo apt install python3.12 python3.12-venv` |
| **Ubuntu 24.04+** | `sudo apt install python3.12 python3.12-venv` |
| **macOS (Homebrew)** | `brew install python@3.12` then `export PATH="$(brew --prefix python@3.12)/bin:$PATH"` |

Then: `./scripts/setup-engine-venv.sh --e2e`

## Local test plan (don’t re-run what already passed)

### Principles

1. **Preflight first** — fail in seconds, not after a 600s Guide wait or hung `/sse` curl.
2. **One suite at a time** — unit → integration → e2e (never jump to e2e while unit is red).
3. **Target failures** — use `--lf` or a single `path::test`; don’t re-run 158 unit tests while fixing one.
4. **Skip green suites** — `all` skips suites already passed at the current commit (stored in `.sdlc/test-suite-state.tsv`).

### Typical session

| Step | Command | ~time |
|------|---------|-------|
| Preflight | `./scripts/run-test-suites.sh preflight all` | 1s |
| Unit (once) | `./scripts/run-test-suites.sh unit` | 2–4 min |
| Fix loop | `./scripts/run-test-suites.sh unit --lf` | seconds |
| Single test | `./scripts/run-test-suites.sh unit -- engine/tests_unit/foo.py::test_bar` | seconds |
| Integration | `./scripts/run-test-suites.sh integration` | 3–6 min |
| E2E | `./scripts/run-test-suites.sh e2e` | 5–15 min |
| E2E + Guide | `./scripts/run-test-suites.sh e2e --guide` | 20–90 min (first ingest) |

### Resume without re-running green work

```bash
# See what is already green at HEAD
./scripts/run-test-suites.sh --state

# Full CI mirror but skip suite 1 if it passed at this commit
./scripts/run-test-suites.sh all

# Unit passed; only run integration + e2e
./scripts/run-test-suites.sh all --from integration

# Force everything (pre-push or after big refactor)
./scripts/run-test-suites.sh all --force

# Forget green markers after rebasing or switching branches
./scripts/run-test-suites.sh --clear-state
```

### When something fails

| Situation | Do this | Don’t do this |
|-----------|---------|----------------|
| One unit test red | `unit -- path::test` then `unit --lf` | `unit` (full 158 tests) |
| Unit green, editing installer | `integration -- path::test` | `all` from scratch |
| Playwright flake | `e2e -- engine/tests_e2e/test_console_playwright.py::test_foo` | `e2e --guide` |
| Guide not up | `preflight e2e --guide` first | bare `curl …/sse` |
| Stale background pytest | `unit --clean-stale` | start another full run |

Shell workflow harness (separate from engine pytest): `./tests/test-sdlc-workflow.sh` — run only when touching `scripts/sdlc.sh` or workflow gates.

**Suite 1** — fast, isolated: mocks, `tmp_path`, no Flask server, no browser, no network.

**Suite 2** — Flask `test_client`: ops console installer API, ADF viewer HTTP, mocked externals.

**Suite 3** — Playwright GUIs, live `gh` Issues sync, optional Guide+Neo4j (`--guide` or `test-guide-stack-live.sh`).


In orchestrator repo:

- `validate-command-adapters` (`.github/workflows/validate-command-adapters.yml`)
- `test-adapter-install` (`.github/workflows/test-adapter-install.yml`)
- `test-upgrade-consolidate` (`.github/workflows/test-upgrade-consolidate.yml`) — storage v3 layout upgrade
- `test-sdlc-pointer` (`.github/workflows/test-sdlc-pointer.yml`)
- `test-sdlc-workflow` (`.github/workflows/test-sdlc-workflow.yml`)
- `test-archive-work` (`.github/workflows/test-archive-work.yml`)
- `test-scripts-lib` (`.github/workflows/test-scripts-lib.yml`)
- `validate-command-spec-generation` (`.github/workflows/validate-command-spec-generation.yml`)
- `test-integration-merge` (`.github/workflows/test-integration-merge.yml`)
- `test-sdlc-engine` (`.github/workflows/test-sdlc-engine.yml`) — Python v2 engine
- `test-e2e-playwright` (`.github/workflows/test-e2e-playwright.yml`) — fast Playwright gate (console + viewer)
- `test-guide-stack-experimental` (`.github/workflows/test-guide-stack-experimental.yml`) — Guide + Neo4j live stack (tier 3)
- `test-live-consumer` (`.github/workflows/test-live-consumer.yml`) — seed/flush consumer matrix; Cursor SDK jobs when `CURSOR_API_KEY` is set
- `test-canvas-readiness` (`.github/workflows/test-canvas-readiness.yml`) — canvas readiness + capture staging smoke
- `test-index-spdd-analysis` (`.github/workflows/test-index-spdd-analysis.yml`)
- `test-resolve-agent-context` (`.github/workflows/test-resolve-agent-context.yml`)
- `validate-canvas` (`.github/workflows/validate-canvas.yml`)
- `validate-diagrams` (`.github/workflows/validate-diagrams.yml`)

### Adapter install regression harness

`./tests/test-adapter-install.sh` installs each assistant adapter (Cursor,
Copilot, Claude Code) into throwaway target directories and asserts:

- Single-assistant installs (`--cursor`, `--copilot`, `--claude`) produce only
  that assistant's files and no others.
- No-flag setup/upgrade keeps the legacy Cursor + Copilot default; Claude Code
  is installed only with `--claude` or `--all`.
- `--all` and `upgrade --all` install all three; Cursor and Copilot files stay
  byte-identical to their templates.
- Upgrade preserves project-owned files such as an existing root `CLAUDE.md`
  and target-local adapter workflow customizations; only the managed
  SDLC-SPDD grounding block inside `CLAUDE.md` is added or refreshed.
- Repeated upgrades do not duplicate the managed `CLAUDE.md` grounding block,
  and `--dry-run` paths do not mutate target files.
- Installed target adapter workflows watch command files, always-on grounding
  files, and the target-local validator script.
- `verify-project-install.sh` passes for every install combination.
- `validate-command-adapters.sh` still **fails** when an adapter guardrail
  is removed, a Required-Behavior step count diverges, or a command file is
  missing (negative tests).
- every assistant's always-on grounding file exists and covers the whole
  ecosystem; validation **fails** if Planning (`session-notes/`), SPDD
  (`spdd/canvas/`), SDLC session context (`.sdlc/sessions/current-session.md`), or an
  assistant grounding file is dropped (negative tests).

Run it locally before changing any install/upgrade script or command template.
The CI workflow also runs `bash -n` over shell scripts before executing the
regression harness.

### Storage v3 upgrade consolidation harness

`./tests/test-framework-install-consolidate.sh` unit-tests consolidate/archive
helpers in `scripts/lib/framework-install.sh` (move/merge/dest-wins, dry-run,
archive leftovers, orchestrator-vs-target agent-context handling, harness seed).

`./tests/test-upgrade-consolidate.sh` is the end-to-end layout suite:

- **A.** Pure legacy sprawl (no `sdlc-spdd/` yet) → single home; root stay-set gone
- **B.** Dual layout merge when home already exists (destination wins conflicts)
- **C.** Idempotent second upgrade
- **D.** `--dry-run` + `--consolidate` no-op leave the tree untouched
- **E.** Orchestrator-shaped target archives `agent-context/`; keeps root `scripts/`
- **F.** Fresh v3 init/setup then upgrade preserves project content
- **G.** Nested helper unit suite

Leftover `agent-context/` trees must land under
`sdlc-spdd/.sdlc/legacy-layout-archive/` (install source is
`templates/agent-context/`). `verify-project-install.sh` must pass after each
real upgrade. CI: `.github/workflows/test-upgrade-consolidate.yml`.

### SDLC pointer harness

`./tests/test-sdlc-pointer.sh` exercises `templates/agent-context/sdlc-pointer.sh`:

- CLI round-trip (`set`/`get`/`reset`)
- Guarded run (`run_against_pointer`) refusal on mismatch
- `SDLC_POINTER_OVERRIDE` bootstrap
- Integration with `start-agent-session.sh` pointer auto-set
- Install path copies the script to target projects

### SDLC workflow + team registry harness

`./tests/test-sdlc-workflow.sh` exercises `templates/agent-context/sdlc-workflow.sh` and team registry:

- Phase/gate tracking, `next`/`advance`/`skip`/`shelf`/`resume`/`sync`
- `sdlc.sh` wrapper delegation
- Guarded `capture` (pointer must match)
- Team `claim`/`release`, stale TTL, branch/PR/Jira notes in `work-registry.tsv`
- Jira Key auto-link from `requirements/milestones/<WORK-ID>.md` on claim

### Archive completed/cancelled work harness

`./tests/test-archive-work.sh` exercises `sdlc.sh archive` / `archive --all`:

- Refuses In Progress work unless `--force`
- **Deletes** Complete/Cancelled canvases, analysis/review/sync artifacts, and matching session briefs from the working tree (git history retains them; storage v3 has no `spdd/*/archive/` folders)
- Leaves `requirements/milestones/<WORK-ID>.md` in place
- Clears the local pointer when it matches the archived Work ID
- Marks `spdd/memory/registry.jsonl` status `archived` (and `sync-team` can mark `cancelled` without removing files)
- `list-work` ignores removed Work IDs (no committed archive directories)

### Shared scripts/lib harness

`./tests/test-scripts-lib.sh` exercises `scripts/lib/*` helpers and
`verify-script-lib-duplicates.sh` (FEAT-001).

### Command spec generation harness

`./tests/test-command-spec-generation.sh` asserts adapters match
`spec/commands/*.spec.md`, that `--check` detects drift, and parity validation still passes (FEAT-002).

`./tests/test-commit-message-command.sh` asserts `/sdlc-spdd-commit-message` adapters
exist with generate-only (no-commit) language, Python engine delegation
(`sdlc.sh commit-message`), and that generator `--check` plus adapter validation
still pass (FEAT-008 / #41). Engine coverage lives in
`engine/tests_unit/test_commit_message.py`.

### Resolve agent context + skills harness

`./tests/test-resolve-agent-context.sh` runs `resolve-agent-context.sh` against
throwaway targets and asserts:

- `--phase code` resolves universal + phase-matching skills from `harness/skills/`
- `#SkillName` / `!SkillName` include and exclude skill files on demand
- `--list-skills` discovers skill names
- `--work-id` loads canvas, analysis, tasks, and ledger progress excerpts (storage v3)
- `--format json` returns paths
- `start-agent-session.sh` embeds Resolved Context and avoids redundant resume prompts
- legacy `playbooks/` + `extensions/` trees migrate idempotently into `harness/skills/`

Run locally after changing `resolve-agent-context.sh`, `scripts/lib/skills.sh`,
harness templates, or `start-agent-session.sh`.

### Integration merge gate

`./tests/test-integration-merge.sh` installs a throwaway `--all` target and
runs workflow CLI, shared lib, skills resolve, claim/next/team/shelf/archive,
nested harnesses, and upgrade (see script sections A–F).

### Python engine harness (v2)

## Run CI locally (`.venv`)

All Python for the engine uses the repo **`.venv`** (Python **3.12** only — same as CI). See `.python-version`.

```bash
# One-time: install python3.12 (Ubuntu 22.04 needs deadsnakes — see table above)
./scripts/setup-engine-venv.sh --e2e

# Full local mirror (suites 1–3; add --guide for Neo4j stack)
./scripts/test-ci-local.sh
./scripts/test-ci-local.sh --guide
```

Equivalent manual steps (always via `.venv/bin/`):

```bash
source .venv/bin/activate
./scripts/run-test-suites.sh unit
./scripts/run-test-suites.sh integration
./scripts/run-test-suites.sh e2e          # Playwright + GitHub (needs gh auth)
./scripts/run-test-suites.sh e2e --guide  # + Guide + Neo4j stack
SDLC_ENGINE=python ./scripts/sdlc.sh version
./tests/test-sdlc-engine-shim.sh
```

GitHub workflow: `.github/workflows/test-sdlc-engine.yml`. Guide stack:
`.github/workflows/test-guide-stack-experimental.yml`.

Guide round-trip (ledger → projection → read + parity + MCP parity):

```bash
SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh
# Or after stack is up:
.venv/bin/pytest -q engine/tests_e2e/test_guide_projection_roundtrip.py
```

Agent Guide queries (Cursor/Copilot): [docs/mcp-guide-for-agents.md](docs/mcp-guide-for-agents.md)

```bash
./scripts/guide/query-guide.sh --text --work-id <WORK-ID>
./scripts/guide/mcp-config-snippet.sh --cursor
```

## Engine pytest (orchestrator repo)

```bash
./scripts/setup-engine-venv.sh --e2e
./scripts/run-test-suites.sh unit
```

Covers pointer, workflow, registry, archive, canvas parsing, link/issue sync,
local/offline sessions, CLI, and mocked Guide client/query helpers.

**Suite 2** (`engine/tests_integration/`) — Flask `test_client` for ADF viewer and ops console installer API, including live ADF start/stop via `/api/adf*`.

**Suite 3** (`engine/tests_e2e/`) — Playwright GUIs, live GitHub Issues, optional Guide+Neo4j.

```bash
./scripts/run-test-suites.sh integration
./scripts/run-test-suites.sh e2e
./scripts/run-test-suites.sh e2e --guide
```

GUI map: [docs/ops-console.md](docs/ops-console.md).

Issue sync confidence:

| Layer | What | How |
|-------|------|-----|
| Unit (always) | Milestone draft → Jira/GitHub push/pull write-back | `engine/tests_unit/test_issues_mocked.py` (fake HTTP + fake `gh`) |
| Integration | Live `gh issue` pull (+ optional create/close) | `engine/tests_e2e/test_issues_github_integration.py` (suite 3) |
| CI | Same, with `issues: write` for create/close cleanup | `test-github-issue-sync` job in `test-sdlc-engine.yml` |

```bash
SDLC_ENGINE=python ./scripts/sdlc.sh sync-links
SDLC_ENGINE=python ./scripts/sdlc.sh sync-links --repair
SDLC_ENGINE=python ./scripts/sdlc.sh sync-roadmap --dry-run
SDLC_ENGINE=python ./scripts/sdlc.sh issues draft <WORK-ID> --system github
./scripts/sdlc.sh local start --name scratch --intent "offline explore"
./scripts/sdlc.sh local promote --type feature --name "Documented title" --dry-run

./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db query --columns work_id,registry_status,jira_key
./scripts/sdlc.sh db query --search "orchestration"

# Live GitHub (suite 3; needs gh auth — included in ./scripts/run-test-suites.sh e2e)
./scripts/run-test-suites.sh e2e
```

### Canvas readiness + capture staging harness

`./tests/test-canvas-readiness.sh` exercises `validate-reasons-canvas.sh` readiness
normalization and a smoke path for `capture-session-memory.sh` staging records
into `.sdlc/staged/lessons.jsonl` (storage v3). Workflow capture integration
is covered by `./tests/test-sdlc-workflow.sh` (Test 7) and the live-consumer
matrix scenarios 03 and 08.

### Index SPDD analysis harness

`./tests/test-index-spdd-analysis.sh` runs `index-spdd-analysis.sh` against
throwaway targets and asserts:

- `domain-index.md` rows for Domain Keywords and Code Areas from the analysis artifact
- `context-index.md` rows with Kind `analysis`
- new code areas appended to `code-areas.md`
- `--dry-run` writes nothing; missing analysis file exits non-zero

Run locally after changing `index-spdd-analysis.sh` or staged analysis records.

### Whole-ecosystem grounding norm (enforced)

Every supported assistant must ship an **always-on grounding file** that loads on
every interaction (not only when a `/sdlc-spdd-*` command runs):

- Cursor: `.cursor/rules/sdlc-spdd.mdc` (`alwaysApply: true`)
- GitHub Copilot: `.github/copilot-instructions.md`
- Claude Code: `CLAUDE.md`

`validate-command-adapters.sh` asserts each present grounding file contains the
shared operating-model anchors (the lifecycle line, `## Operating Model`,
`## Work Rules`) and the Planning + SPDD + SDLC artifacts (`ROADMAP.md`,
`milestone-*.md`, `session-notes/`, `spdd/analysis/`, `spdd/canvas/`,
`.sdlc/sessions/current-session.md`, `spdd/canvas/`, `/sdlc-spdd-analysis`).
This makes whole-ecosystem awareness the norm for all work across every assistant
— and runs in CI both here and inside installed target projects when the target
adapter workflow is installed.

In installed target projects (when both Cursor + Copilot adapters are installed):

- `.github/workflows/validate-sdlc-spdd-adapters.yml`

## Local Smoke Protocol (5-10 minutes)

Use one canonical Work ID and one operation.

1. In chat, run:

       /sdlc-spdd-plan @requirements/<topic>.md @ROADMAP.md @milestone-1.md
       /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md
       /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
       /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

2. In terminal, verify effects:

       ./sdlc-spdd/scripts/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step plan
       ./sdlc-spdd/scripts/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step architect
       ./sdlc-spdd/scripts/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step code --operation T01
       ./sdlc-spdd/scripts/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step review

3. Capture memory and planning sync:

       ./sdlc-spdd/scripts/capture-session-memory.sh --target . --work-id <WORK-ID> --phase code --summary "<summary>" --validation "<tests>" --milestone milestone-1.md --roadmap-note "<progress>" --next "<next command>"
       ./sdlc-spdd/scripts/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step capture --milestone milestone-1.md --require-roadmap

### Live consumer matrix (seed / flush)

Idempotent Cursor-only consumer install exercised against a throwaway git repo.

CI workflow: `.github/workflows/test-live-consumer.yml`

| Job | Needs secret? | What |
|-----|---------------|------|
| `test-live-consumer-shell` | No | `./tests/test-live-consumer-matrix.sh` (incl. SQLite brief scenario 09) |
| `test-live-consumer-cursor-sdk` | `CURSOR_API_KEY` | Persistence test + slash subset; **skipped** if secret unset |

Add the key under **GitHub → Settings → Secrets and variables → Actions** as
`CURSOR_API_KEY` (same Integrations key as local). Cursor Dashboard “runtime /
Cloud Agents” secrets do **not** inject into GitHub Actions.

Note: GitHub forbids `secrets.*` in job-level `if:` expressions (workflow fails
to start). Availability is probed via a tiny job that sets an output from env.

```bash
./tests/test-live-consumer-matrix.sh

# Keep a reopenable tree for manual IDE slash commands:
LIVE_CONSUMER_KEEP=1 ./tests/live-consumer/run-matrix.sh
# then open /tmp/sdlc-spdd-live and follow tests/live-consumer/CURSOR-SLASH-LIVE.md

# REAL Cursor agents (local or CI with secret):
export CURSOR_API_KEY=...   # https://cursor.com/dashboard/integrations
./tests/live-consumer/run-cursor-agent-matrix.sh
./tests/live-consumer/run-cursor-persistence-test.sh
```

Details: [tests/live-consumer/README.md](tests/live-consumer/README.md) and
[tests/live-consumer/cursor-agent/README.md](tests/live-consumer/cursor-agent/README.md).

## Release Confidence Contract

Before release or major merge, require:

- [ ] CI gates green (adapter parity + adapter install/upgrade + canvas + diagrams)
- [ ] One manual smoke run completed in Cursor, Copilot, or Claude Code
- [ ] `verify-agent-command-effects.sh` passes for `plan`, `architect`, `code`, `review`, `capture`
- [ ] Milestone/session-notes sync confirmed for the tested Work ID

## Known Blind Spots (Expected)

- CI cannot execute Cursor/Copilot/Claude Code chat UI itself.
- LLM wording is nondeterministic; we validate artifacts/invariants instead.
- Adapter parity checks enforce structure and guardrails, not semantic quality of every response.
