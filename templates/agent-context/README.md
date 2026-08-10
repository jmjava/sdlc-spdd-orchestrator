# Agent Context

Workflow scripts, harness skills, and quality gates for SDLC-SPDD agents in the
orchestrator repo (storage v3 dogfood layout).

## Layout

| Path | Role |
|------|------|
| `harness/` | `phase-index.md`, quality gates, validation rules |
| `harness/skills/` | Phase-matching and `#SkillName` skills — resolve with `resolve-agent-context.sh` |
| `sdlc-pointer.sh`, `sdlc-workflow.sh`, `sdlc-team-registry.sh` | Workflow CLI (also installed under `scripts/` in targets) |

Committed memory lives under **`spdd/memory/`** (`lessons.jsonl`, `registry.jsonl`).
Hot session brief: **`.sdlc/sessions/current-session.md`** (gitignored).

See [docs/storage-v3.md](../docs/storage-v3.md).

## Quick commands

```bash
./scripts/sdlc.sh list-work
./scripts/sdlc.sh claim <WORK-ID>
./scripts/start-agent-session.sh --target . --work-id <WORK-ID> --phase code
./scripts/resolve-agent-context.sh --phase code --work-id <WORK-ID>
```

## SDLC pointer

```bash
./scripts/sdlc.sh next
./scripts/sdlc.sh claim <WORK-ID>
./scripts/sdlc.sh shelf --reason "blocked"
./scripts/sdlc.sh resume <WORK-ID>
```

Pointer state: `.sdlc/pointer` (gitignored). Set automatically when
`start-agent-session.sh --work-id` runs.

## SDLC workflow

Phase and gate tracking under `.sdlc/workflows/` (gitignored). Committed
contracts (`spdd/canvas/`, analysis, reviews) are the audit trail; run
`./scripts/sdlc.sh sync` to reconcile workflow state.

```bash
./scripts/sdlc.sh status
./scripts/sdlc.sh advance
./scripts/sdlc.sh skip api-test --reason "no HTTP surface"
./scripts/sdlc.sh capture --summary "finished T02"
```

Set `SDLC_ENGINE=python` (or `auto`) to use the Python engine — see
[docs/engine-v2.md](../docs/engine-v2.md).

## Team registry

Team coordination uses **`spdd/memory/registry.jsonl`** (commit after
claim/release):

```bash
./scripts/sdlc.sh team
./scripts/sdlc.sh claim <WORK-ID>
./scripts/sdlc.sh release --reason "handoff"
```

## Archive completed work

When a canvas `## Final Status` is Complete or Cancelled, remove contract
artifacts from the working tree (git history retains them):

```bash
./scripts/sdlc.sh archive <WORK-ID>
./scripts/sdlc.sh archive --all
./scripts/sdlc.sh archive <WORK-ID> --dry-run
```

Removes: `spdd/canvas|analysis|reviews|sync` for the Work ID, matching
`.sdlc/sessions/*<WORK-ID>*` briefs (not `current-session.md`), and workflow
state. Leaves `requirements/milestones/<WORK-ID>.md` in place. Registry row
becomes `archived`.

## Session scripts

```bash
./scripts/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>
./scripts/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>"
```

Hot brief: `.sdlc/sessions/current-session.md`. Timestamped briefs rotate to
`.sdlc/sessions/archive/` via `--session-limit` on start (default 20).

## Optional Guide backend

When `agent-context/harness/guide-dice.md` is present, resolve backends with
`./scripts/resolve-context-backend.sh --target .` and augment retrieval with
`spdd_*` MCP tools. Guide is never required — see
[docs/guide-flow.md](../docs/guide-flow.md).
