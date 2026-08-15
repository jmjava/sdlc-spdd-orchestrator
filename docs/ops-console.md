# Ops console and ADF Viewer (local GUIs)

Two **separate** localhost Flask apps. They do not share a process. Guide is
optional and wires through the ops console + slash-command context backend — not
through the ADF editor. The ADF Viewer does **not** talk to Guide (Jira/GitHub sync only).

> **Experimental.** The ops console is an orchestrator dogfood UI. Supported
> consumer installs still use `setup-agent-prompts.sh` / `upgrade-project.sh` /
> `verify-project-install.sh`. APIs and UI may change without a migration guide.

## Quick map

| UI | Default URL | Start | Responsibility |
|----|-------------|-------|----------------|
| **Ops console** | `http://127.0.0.1:5051/` | `./scripts/sdlc.sh console --target <path>` | **Dashboard** (default tab), install/upgrade, persistence backends, SQLite, rollback, Guide+Neo4j lifecycle, **Jira link & sync**, ADF templates API, **start/stop** ADF Viewer |
| **Vue3 console (dev)** | `http://127.0.0.1:5173/` | `cd console-ui && npm run dev` (proxies `/api` → `:5051`) | Same tabs as `sdlc.sh console` (Dashboard default, Persistence, Templates, Install, SQLite, Rollback, Guide, Issues, ADF); see [adf-template-library-and-vue3-console.md](adf-template-library-and-vue3-console.md) |
| **ADF Viewer** | `http://127.0.0.1:5050/` | `./scripts/sdlc.sh viewer` or console **ADF** tab | Edit `adf/*.adf.json`, Jira/GitHub prepare/apply sync |

Aliases for the console: `installer`, `dashboard`. Wrapper: `./scripts/visual-installer.sh`.

```bash
python3 -m pip install -e './engine[viewer]'   # Flask extra
./scripts/sdlc.sh console --playground          # disposable seed + in-process Guide/Jira/GitHub fakes
./scripts/sdlc.sh console --target /path/to/app
./scripts/sdlc.sh viewer --root /path/to/app --port 5050
```

## How they relate (and Guide)

![Ops console and companion services](diagrams/14-ops-console.svg)

| Concern | Where it lives |
|---------|----------------|
| Framework install into a target repo | Console **Install / Upgrade** tab or shell scripts |
| At-a-glance work + memory status | Console **Dashboard** tab (landing page) |
| Local Work ID SQLite cache | Console **SQLite** tab or `./scripts/sdlc.sh db …` |
| Upgrade backup restore | Console **Rollback** tab |
| Start/stop Neo4j + Guide, ingest, projection, purge | Console **Guide** tab |
| Ledger parity check / repair | Console **Persistence** tab |
| Edit ticket ADF / sync Jira or GitHub | **ADF Viewer only** |
| Optional retrieval for analysis/code/… | Guide + `harness/guide-dice.md` |

## Ops console tabs

The top **Path** field is the target project for install/SQLite/rollback/Guide and
the `--root` passed when starting the ADF Viewer.

| Tab | What it does |
|-----|----------------|
| **Dashboard** | **Default landing tab.** Active Work ID, phase, gates, suggested next command, accepted vs staged lesson counts, backend status, integration shortcuts. Work ID / suggestions / activity jump to SQLite, Templates, Issues, or ADF with that id filled. |
| **Install / Upgrade** | Detect fresh vs upgrade; run setup/upgrade/verify (dry-run supported) |
| **Persistence** | Toggle `CONTEXT_BACKENDS` backends (`git-pointers`, `sqlite`, `guide-dice`); optional Guide URL + notes → `.sdlc/persistence-config.json`. **Check ledger parity** and **Parity + repair** buttons call `sdlc-engine context parity`. Operator guide: [triple-path-context.md](triple-path-context.md) |
| **Templates** | Render ADF combos for a Work ID with markdown + JSON preview; optional write to `adf/<work-id>.adf.json` and open the ADF Viewer on that file |
| **SQLite** | `.sdlc/index.sqlite` status + rebuild, plus a filterable work browser that jumps to Templates / Issues / ADF |
| **Rollback** | List `.sdlc-spdd-upgrade-backups/<timestamp>/` and restore |
| **Guide** | Config (`.sdlc/guide-config.json`), ensure `jmjava/orch-guide` @ `sdlc-spdd-projection-v2`, Neo4j/Guide start/stop, projection load, ingest/purge operators. Dual-repo Cloud Agent: defaults `guide_home` to sibling `../guide` and treats an already-open Bolt (`/opt/neo4j`) as Neo4j up (no Compose required). |
| **Jira** | Link a **manually created** Jira key to a Work ID (requirement + canvas + registry); prepare/apply **pull** and **push** (update only — no issue create) |
| **ADF** | Start / stop / restart viewer process; open URL. Editing stays in the viewer |

Use `--no-browser` in CI/headless. `--port` / `--host` / `--lan` match the viewer CLI.

## ADF Viewer (summary)

- Default ticket folder: `<root>/adf/` (browse can open other directories).
- Split WYSIWYG + raw JSON; autosave; explicit Jira/GitHub prepare/apply (never auto).
- Full runbook: [adf-viewer.md](adf-viewer.md).

Console **ADF → Start viewer** runs `python -m sdlc_engine.viewer --root <Path> …`
and records pid/port under `.sdlc/adf-viewer-runtime.json`.

CLI equivalents for tracker sync:

```bash
sdlc-engine issues upload-adf --issue-key PROJ-123 --file adf/PROJ-123.adf.json --apply
sdlc-engine issues download-adf PROJ-123 --apply
```

See [Issue sync and branching](issue-sync-and-branching.md).

## Guide integration (optional)

1. **Dogfood stack** — console **Guide** tab (or [dice-projection-runbook.md](dice-projection-runbook.md)).
2. **Opt in an install** — `init-project.sh … --with-guide` writes
   `harness/guide-dice.md`.
3. **Runtime resolve** — `resolve-context-backend.sh` emits `CONTEXT_BACKENDS=…`
   (comma-separated set). Explicit env/config is authoritative: a disabled
   `guide-dice` is never re-added from the harness marker.

Slash commands never fail because Guide is down. End-to-end flow:
[guide-flow.md](guide-flow.md). Local stack: [dice-projection-runbook.md](dice-projection-runbook.md).
Agent MCP/CLI: [mcp-guide-for-agents.md](mcp-guide-for-agents.md).

Default dogfood ports (editable in console): Guide `21337`, Neo4j Bolt `7687` /
HTTP `7474`. Override Guide git ref with `GUIDE_GIT_REF` (default tag
`spdd-projection-v3` on `jmjava/orch-guide`).

## Tests

| Tier | Suite | Command |
|------|-------|---------|
| 1 | Unit | `pytest -q engine/tests_unit` |
| 2 | Local integration (installer API) | `pytest -q engine/tests_integration` |
| 3 | E2E Playwright (Vue3 ops console + ADF Viewer) | `./scripts/run-test-suites.sh e2e` (builds `console-ui` when needed) |
| 3 | Guide + Neo4j live stack | `SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh` |
| 3 | Vue3 Playwright live Guide stack (opt-in) | `SDLC_GUIDE_STACK_LIVE=1 pytest -q engine/tests_e2e/test_vue3_console_live_playwright.py -m guide_live --run-guide-live` |
| 3 | Vue3 Playwright live ADF viewer (opt-in) | `SDLC_ADF_VIEWER_LIVE=1 pytest -q engine/tests_e2e/test_vue3_console_live_playwright.py -m adf_viewer_live --run-adf-viewer-live` |

CI: `./scripts/test-ci-local.sh` mirrors tier 1+2 via `.venv`.
Guide live stack: `./scripts/test-ci-local.sh --guide` or `test-guide-stack-experimental.yml`.
The experimental workflow skips live Guide+Neo4j (and Vue `guide_live`) when
`repo.embabel.com` is unreachable; ADF viewer live still runs.
Fast Playwright-only gate: `test-e2e-playwright.yml`.

## Related

- [Installing into your project](installing-into-your-project.md)
- [ADF Viewer](adf-viewer.md)
- [Local SQLite index](local-sqlite-index.md)
- [Engine README](../engine/README.md)
- [TESTING.md](../TESTING.md)
