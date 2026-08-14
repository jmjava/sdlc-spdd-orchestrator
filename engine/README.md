# SDLC Engine (v2)

Python orchestration engine for the SDLC-SPDD operating model.

Shell scripts remain the **v1 compatibility surface**. This package is the
**v2 reusable core**: pointer, workflow phases/gates, team registry, archive,
and a stable CLI/API that assistants and tools can call without bash.

## Status

Alpha (`2.0.0a6`). Core workflow commands are implemented in Python and covered
by pytest. Install/upgrade/adapter generation still use the existing shell
scripts; the engine can shell out to them via `sdlc-engine shell …` when needed.

## Quick start

Requires **Python 3.12** (see repo `.python-version`). From the orchestrator repo:

```bash
sudo apt install python3.12 python3.12-venv   # once
./scripts/setup-engine-venv.sh --e2e
source .venv/bin/activate

# CLI entry
sdlc-engine next
sdlc-engine claim FEAT-001-demo
sdlc-engine archive --all --dry-run
```

Or without activating the venv:

```bash
.venv/bin/python -m sdlc_engine next --root .
```

Prefer the engine from the existing wrapper (shell remains the default):

```bash
SDLC_ENGINE=python ./scripts/sdlc.sh next
SDLC_ENGINE=auto ./scripts/sdlc.sh next   # python if importable, else shell

# Local/offline sessions + SQLite index always use the Python engine (even with SDLC_ENGINE=shell)
./scripts/sdlc.sh local start --name scratch --intent "explore without a FEAT"
./scripts/sdlc.sh local promote --type feature --name "Documented title"
./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db query --search "orchestration"
./scripts/sdlc.sh db lookup --work-id FEAT-001-example --markdown
./scripts/sdlc.sh commit-message --hint "summarize current changes"
./scripts/sdlc.sh sunset --work-id FEAT-001-example --apply
```

## Package layout

| Module | Responsibility |
|--------|----------------|
| `project` | Resolve project root and artifact paths |
| `phases` | Phase order, gates, recommended assistant commands |
| `pointer` | `.sdlc/pointer` get/set/reset + guarded run |
| `workflow` | Resume/advance/skip/shelf/sync/next/status |
| `registry` | `work-registry.tsv` claim/release/team/list-work |
| `archive` | Remove Complete/Cancelled work artifacts (git history retains them) |
| `canvas` | Final Status + next-operation inference |
| `links` / `sync_local` | Milestone↔canvas↔registry drift check/repair + ROADMAP sync |
| `issues` | Draft/push/pull Jira (`JIRA_*`) or GitHub (`gh`) from milestone sections |
| `jira_format` | Markdown ↔ ADF; optional ADF→wiki shim (`adf_to_wiki`) for Server/DC — raw ADF is default on Cloud v3 |
| `issues` CLI | `draft` / `push` / `pull` / `upload-adf` / `download-adf` — explicit only; `--description-format adf\|wiki` |
| `local_sessions` | `LOCAL-*` offline sessions + promote into documented Work IDs |
| `db` | Regenerable local SQLite index (`.sdlc/index.sqlite`) before GUIDE |
| `commit_message` | Staged/unstaged/ahead-of-base diff report for commit-message drafts |
| `sunset` | Close-out snapshot: GitHub PR + commits + Jira → lesson ledger |
| `viewer` | ADF WYSIWYG editor for checked-in `adf/*.json` (optional `[viewer]` / Flask) |
| `installer` / `console` / `dashboard` | **EXPERIMENTAL** ops console: install/upgrade, SQLite, rollback, Guide+Neo4j, ADF viewer lifecycle (optional `[viewer]` / Flask) |
| `cli` | `sdlc-engine` / `python -m sdlc_engine` |

Two local GUIs + Guide map: [docs/ops-console.md](../docs/ops-console.md)
(Guide pin for console dogfood: **`jmjava/orch-guide`** tag **`sdlc-spdd-projection-v2`**).  
ADF editor runbook: [docs/adf-viewer.md](../docs/adf-viewer.md).

```bash
python3 -m pip install -e './engine[dev,viewer]'
./scripts/sdlc.sh console --target /path/to/app --port 5051   # ops UI
./scripts/sdlc.sh viewer --root /path/to/app --port 5050      # ADF editor
```

## Compatibility

- File formats stay identical (`.sdlc/`, `work-registry.tsv`, canvas paths).
- Shell `sdlc.sh` can delegate to this engine (`SDLC_ENGINE=auto|python|shell`).
- Target projects can keep using bash until they opt into the engine.

## Tests

```bash
python3 -m pip install -e './engine[dev,viewer]'
pytest -q engine/tests_unit
```

Or without install (viewer tests need Flask):

```bash
PYTHONPATH=engine/src python3 -m pytest -q engine/tests_unit_unit
```

Three suites — see [TESTING.md](../TESTING.md#engine-test-suites-3-packages):

```bash
./scripts/run-test-suites.sh unit          # engine/tests_unit
./scripts/run-test-suites.sh integration # engine/tests_integration (+ installer cov)
./scripts/run-test-suites.sh e2e         # engine/tests_e2e (Playwright, gh, optional --guide)
```

## Design notes

See [docs/engine-v2.md](../docs/engine-v2.md) and
`spdd/canvas/FEAT-006-python-orchestration-engine.md`.
