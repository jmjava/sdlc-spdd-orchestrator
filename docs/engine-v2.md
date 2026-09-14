# SDLC Engine — Python orchestration

The `sdlc_engine` package is the reusable orchestration core for SDLC-SPDD:
pointer, workflow, team registry, archive, the storage v3 context store (ledger,
stage-then-accept, projections), issue sync, local sessions, and the ops console.

![Engine components](diagrams/03-component-engine.svg)

**One engine (REF-003).** `sdlc_engine` is the only workflow implementation.
`scripts/sdlc.sh` (installed as `sdlc-spdd/scripts/sdlc.sh`) is a thin
dispatcher that execs `python -m sdlc_engine --root <root> <verb>`; there is no
bash workflow twin and no `SDLC_ENGINE` / `SDLC_GATE_ENGINE` switch (setting
either makes `sdlc.sh` exit 2). Python `WorkflowEngine.gate_check` is the
system under test for every gate. Shell remains only for install/upgrade
packaging and the session-brief renderers (`start-agent-session.sh`,
`capture-session-memory.sh`), which call back into the engine for all state.

Storage v3 is the only layout: everything lives under the project's
`sdlc-spdd/` home — `sdlc-spdd/.sdlc/` (gitignored runtime),
`sdlc-spdd/spdd/memory/lessons.jsonl`, `sdlc-spdd/spdd/memory/registry.jsonl`,
canvases under `sdlc-spdd/spdd/canvas/`. See [storage-v3.md](storage-v3.md).

## Layout

```
engine/
  pyproject.toml
  README.md
  src/sdlc_engine/
    cli.py              # entry point (sdlc-engine / python -m sdlc_engine)
    cli_parser.py       # argparse builders
    commands/           # handlers by concern
      state.py          #   next/status/advance/gate/skip/shelf/pointer/shell
      team.py           #   claim/release/team/list-work/sync-team/archive
      context.py        #   context store, start/capture/complete/accept, session bridge
      integrations.py   #   links/sync-links/sync-roadmap/issues/commit-message/sunset
      storage.py        #   db, local sessions, work init-from-adf, viewer/installer/template
    session.py          # session bridge used by start-agent-session/capture-session-memory
    timeutil.py         # shared UTC stamps
    io_util.py          # JSON/path helpers
    placeholders.py     # TBD/TODO/NONE/N/A sentinels
    project.py          # root + sdlc-spdd/ home resolution
    phases.py           # phase/gate tables
    pointer.py
    workflow.py
    registry.py         # registry.jsonl claim/release event log
    lessons_ledger.py   # lessons.jsonl + gitignored stage
    context_store.py    # persist/retrieve/accept/parity
    persistence.py      # CONTEXT_BACKENDS config
    integration_config.py # Jira/GitHub tracker config (.sdlc/integrations-config.json)
    quiet.py            # quiet/product-test mode
    archive.py          # storage v3: remove completed work from the tree
    canvas.py
    links.py            # milestone/canvas/registry link parsing
    sync_local.py       # sync-links / sync-roadmap
    issues.py           # Jira/GitHub draft|push|pull|upload-adf|download-adf
    jira_format.py      # markdown ↔ ADF / wiki
    local_sessions.py   # LOCAL-* offline sessions + promote
    db.py               # LocalIndex facade + public re-exports
    db_schema.py        # SQLite DDL + graph constants
    db_rebuild.py       # full-index rebuild / ingest
    db_query.py         # lookup / find / export
    commit_message.py   # diff report for commit drafts
    installer/          # ops console (:5051); dashboard.py landing-tab helpers
      process_util.py   # shared tcp/pid/run helpers
    viewer/             # ADF viewer (:5050)
  tests_unit/
  tests_integration/
  tests_e2e/
```

## Usage

```bash
# Orchestrator checkout: create the 3.12 venv once, then use the dispatcher
./scripts/setup-engine-venv.sh
./scripts/sdlc.sh next
./scripts/sdlc.sh claim FEAT-001-demo

# Equivalent direct invocation
PYTHONPATH=engine/src python3.12 -m sdlc_engine next --root .

# Installed target: sdlc-spdd/scripts/sdlc.sh finds <target>/.venv/bin/python
# or python3.12 on PATH with sdlc-engine installed
python3.12 -m pip install -e '/path/to/orchestrator/engine[dev]'
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
./scripts/sdlc.sh gate --phase <phase> [--work-id <WORK-ID>]
./scripts/sdlc.sh quick [--work-id LOCAL-…]
./scripts/sdlc.sh archive [<WORK-ID>] [--all] [--dry-run] [--force]
```

## Session verbs

`start`, `capture`, `complete`, `accept` are engine verbs. `capture` and
`complete` forward their remaining options to `capture-session-memory.sh`;
`session *` are the callbacks those scripts use for workflow state.

```bash
./scripts/sdlc.sh start --work-id FEAT-001-demo --phase code
./scripts/sdlc.sh capture --summary "Wired the endpoint" --validation "unit green"
./scripts/sdlc.sh complete --summary "T01 done" \
  --verify-command "pytest -q" --verify-exit 0 --verify-result pass
./scripts/sdlc.sh accept --list
./scripts/sdlc.sh accept --work-id FEAT-001-demo --commit
./scripts/sdlc.sh session brief --work-id FEAT-001-demo
./scripts/sdlc.sh session recommend --work-id FEAT-001-demo --phase code
```

## Milestone / Jira / GitHub sync

```bash
./scripts/sdlc.sh links
./scripts/sdlc.sh sync-links [--repair]
./scripts/sdlc.sh sync-roadmap

./scripts/sdlc.sh issues draft <WORK-ID> --system jira
./scripts/sdlc.sh issues push  <WORK-ID> --system jira --apply
./scripts/sdlc.sh issues pull  <WORK-ID> --system github --apply

./scripts/sdlc.sh issues upload-adf --issue-key PROJ-123 --file adf/PROJ-123.adf.json --apply
./scripts/sdlc.sh issues download-adf PROJ-123 --apply
```

Jira Cloud descriptions use **ADF**. See [jira-runbook.md](jira-runbook.md#description-formatting-adf)
and [issue sync and branching](issue-sync-and-branching.md).

## Commit message diff report

Collect the change set the user is about to commit (staged → unstaged → commits
since merge base) so `/sdlc-spdd-commit-message` can draft a message from a
stable engine report. **Generate only** — never creates a commit.

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

# Ad hoc day: omit --work-id; do not invent FEAT-ADHOC
sdlc-engine context persist-lesson --kind pitfall --area notify \
  --source adhoc-prompt --body "Retry without an idempotency key double-posts."

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
```

Pre-v3 layouts (`agent-context/`, root `spdd/`, `work-registry.tsv`) are not
migrated: `upgrade-project.sh` refuses them and the console reports
`unsupported`. Remove the legacy paths (git history keeps them) and re-run
`init-project.sh`.

## Local SQLite cache (opt-in)

Regenerable query cache in `sdlc-spdd/.sdlc/index.sqlite` (schema v5). See
[local-sqlite-index.md](local-sqlite-index.md).

```bash
./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db query --search "orchestration"
./scripts/sdlc.sh db lookup --work-id FEAT-001-example --markdown
```

## Local / offline work sessions

Machine-private `LOCAL-NNN-slug` sessions under gitignored
`sdlc-spdd/.sdlc/local-sessions/`:

```bash
./scripts/sdlc.sh local start --name scratch-sync --intent "Explore without a FEAT yet"
./scripts/sdlc.sh local capture --summary "Tried approach A"
./scripts/sdlc.sh local list
./scripts/sdlc.sh local promote --type feature --name "Detached Agent Capture"
```

`LOCAL-*` is never written to the team registry. Promote creates canvas +
requirement, then claims the new Work ID (unless `--no-claim`).

## Bridge to shell scripts

Install, upgrade, adapter generation, and the session-brief renderers remain
shell (they hold no workflow state). Call them through:

```bash
python3 -m sdlc_engine shell setup-agent-prompts.sh -- --target /tmp/demo --all
```

## Tests

```bash
./scripts/run-test-suites.sh unit          # engine/tests_unit
./scripts/run-test-suites.sh integration   # engine/tests_integration (Flask test clients)
./tests/test-sdlc-workflow.sh              # bash harnesses drive the installed dispatcher
```

See [TESTING.md](../TESTING.md) for CI jobs and integration flags.

## Related

- [Storage v3](storage-v3.md)
- [Ops console](ops-console.md)
- Package readme: `engine/README.md`
