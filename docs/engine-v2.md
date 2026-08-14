# SDLC Engine — Python orchestration

The `sdlc_engine` package is the reusable orchestration core for SDLC-SPDD:
pointer, workflow, team registry, archive, the storage v3 context store (ledger,
stage-then-accept, projections), issue sync, local sessions, and the ops console.

![Engine components](diagrams/03-component-engine.svg)

Shell scripts remain the default entry point (`SDLC_ENGINE=shell`). Opt into Python
with `SDLC_ENGINE=python` or `auto`. On-disk formats are shared: `.sdlc/`,
`spdd/memory/lessons.jsonl`, `spdd/memory/registry.jsonl`, canvas paths.

## Layout

```
engine/
  pyproject.toml
  README.md
  src/sdlc_engine/
    cli.py              # argparse CLI (sdlc-engine)
    project.py          # root + sdlc-spdd/ home resolution
    phases.py           # phase/gate tables
    pointer.py
    workflow.py
    registry.py         # registry.jsonl claim/release event log
    lessons_ledger.py   # lessons.jsonl + gitignored stage
    context_store.py    # persist/retrieve/accept/parity
    persistence.py      # CONTEXT_BACKENDS config
    storage_migrate.py  # legacy → ledger migration
    archive.py
    canvas.py
    links.py            # milestone/canvas/registry link parsing
    sync_local.py       # sync-links / sync-roadmap
    issues.py           # Jira/GitHub draft|push|pull|upload-adf|download-adf
    jira_format.py      # markdown ↔ ADF / wiki
    local_sessions.py   # LOCAL-* offline sessions + promote
    db.py               # opt-in SQLite cache (.sdlc/index.sqlite)
    commit_message.py   # diff report for commit drafts
    installer/          # ops console (:5051)
    viewer/             # ADF viewer (:5050)
  tests/
```

## Usage

```bash
# From orchestrator checkout (no install)
PYTHONPATH=engine/src python3 -m sdlc_engine next --root .

# Opt into the Python engine via the existing wrapper (default remains shell)
SDLC_ENGINE=python ./scripts/sdlc.sh next
SDLC_ENGINE=python ./scripts/sdlc.sh claim FEAT-001-demo
SDLC_ENGINE=auto   ./scripts/sdlc.sh next   # python if importable, else shell
./scripts/sdlc.sh next                      # bash default

# Editable install
python3 -m pip install -e './engine[dev]'
sdlc-engine team
sdlc-engine archive --all --dry-run
```

## Workflow commands

```bash
./scripts/sdlc.sh next
./scripts/sdlc.sh claim <WORK-ID>
./scripts/sdlc.sh release <WORK-ID>
./scripts/sdlc.sh advance [--force]
./scripts/sdlc.sh shelf --reason "…"
./scripts/sdlc.sh gate <phase>
./scripts/sdlc.sh quick [--work-id LOCAL-…]
./scripts/sdlc.sh archive <WORK-ID> [--all] [--dry-run]
```

## Milestone / Jira / GitHub sync

```bash
SDLC_ENGINE=python ./scripts/sdlc.sh links
SDLC_ENGINE=python ./scripts/sdlc.sh sync-links [--repair]
SDLC_ENGINE=python ./scripts/sdlc.sh sync-roadmap

SDLC_ENGINE=python ./scripts/sdlc.sh issues draft <WORK-ID> --system jira
SDLC_ENGINE=python ./scripts/sdlc.sh issues push  <WORK-ID> --system jira --apply
SDLC_ENGINE=python ./scripts/sdlc.sh issues pull  <WORK-ID> --system github --apply

SDLC_ENGINE=python ./scripts/sdlc.sh issues upload-adf --issue-key PROJ-123 --file adf/PROJ-123.adf.json --apply
SDLC_ENGINE=python ./scripts/sdlc.sh issues download-adf PROJ-123 --apply
```

Jira Cloud descriptions use **ADF**. See [jira-runbook.md](jira-runbook.md#description-formatting-adf)
and [issue sync and branching](issue-sync-and-branching.md).

## Commit message diff report

Collect the change set the user is about to commit (staged → unstaged → commits
since merge base) so `/sdlc-spdd-commit-message` can draft a message from a
stable engine report. **Generate only** — never creates a commit.

Always routed to the Python engine (even when `SDLC_ENGINE=shell`):

```bash
./scripts/sdlc.sh commit-message
./scripts/sdlc.sh commit-message --hint "wire engine report" --work-id FEAT-008-commit-message-command
./scripts/sdlc.sh commit-message --json
./scripts/sdlc.sh commit-message --base origin/main --max-diff 40000
```

Implementation: `engine/src/sdlc_engine/commit_message.py`.

## Feature sunset snapshot

Collect GitHub PR, GitHub issue, commit, and Jira state for a Work ID and optionally stage
a `session` record (`source=sunset`) into the lesson ledger. Used by
`/sdlc-spdd-sunset`. Remote pulls are best-effort (missing `gh` or Jira
credentials become warnings).

Always routed to the Python engine (even when `SDLC_ENGINE=shell`):

```bash
./scripts/sdlc.sh sunset --work-id FEAT-001-example
./scripts/sdlc.sh sunset --work-id FEAT-001-example --apply
./scripts/sdlc.sh sunset --work-id FEAT-001-example --accept --json
```

Implementation: `engine/src/sdlc_engine/sunset.py`.

## Context store

One committed ledger, regenerable projections ([storage-v3.md](storage-v3.md)):

```bash
# Stage a lesson (gitignored .sdlc/staged/lessons.jsonl)
sdlc-engine context persist-lesson --kind pitfall --work-id FEAT-001-x \
  --area src/billing --body "Legacy orders omit tax field"

# Promote at retro/sync gates
sdlc-engine context accept --work-id FEAT-001-x
sdlc-engine context accept --ids <a,b,c> --discard-rest

# Retrieve — bounded lists, one body at a time
sdlc-engine context retrieve --work-id FEAT-001-x --kind pitfall
sdlc-engine context show "pitfall:FEAT-001-x:src/billing:capture"
sdlc-engine context digest --work-id FEAT-001-x

# Projections: verify / repair parity with sqlite + Guide
sdlc-engine context parity
sdlc-engine context parity --repair

# Backend set (default git + guide; sqlite opt-in)
sdlc-engine context backends
sdlc-engine context backends --set git-pointers,guide-dice,sqlite

# Legacy install migration
sdlc-engine storage status
sdlc-engine storage migrate [--dry-run]
```

## Local SQLite cache (opt-in)

Regenerable query cache in `.sdlc/index.sqlite` (schema v5). See
[local-sqlite-index.md](local-sqlite-index.md).

```bash
./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db query --search "orchestration"
./scripts/sdlc.sh db lookup --work-id FEAT-001-example --markdown
```

## Local / offline work sessions

Machine-private `LOCAL-NNN-slug` sessions under gitignored
`.sdlc/local-sessions/`:

```bash
./scripts/sdlc.sh local start --name scratch-sync --intent "Explore without a FEAT yet"
./scripts/sdlc.sh local capture --summary "Tried approach A"
./scripts/sdlc.sh local list
./scripts/sdlc.sh local promote --type feature --name "Detached Agent Capture"
```

`LOCAL-*` is never written to the team registry. Promote creates canvas +
requirement, then claims the new Work ID (unless `--no-claim`).

## Bridge to shell scripts

Install, upgrade, adapter generation, and some session helpers remain shell.
Call them through:

```bash
python3 -m sdlc_engine shell setup-agent-prompts.sh -- --target /tmp/demo --all
```

## Tests

```bash
PYTHONPATH=engine/src python3 -m pytest -q engine/tests
```

See [TESTING.md](../TESTING.md) for CI jobs and integration flags.

## Related

- [Storage v3](storage-v3.md)
- [Ops console](ops-console.md)
- Package readme: `engine/README.md`
