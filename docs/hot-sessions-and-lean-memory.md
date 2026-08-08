# Hot sessions and lean memory

**Shipped in `v2.0.0a6`.** This page explains where session briefs and durable
memory live after the agent-context cleanup — and what to stop committing.

## The split

| Kind | Lives in | Git? | Purpose |
| ---- | -------- | ---- | ------- |
| **Contracts** | `requirements/`, `spdd/canvas/`, `spdd/analysis|reviews|sync/` | Yes | Scope and governance |
| **Lean memory** | `spdd/memory/` | Yes (compact) | Lessons, progress entries, pointers, context-index |
| **Hot sessions** | `.sdlc/sessions/` | **No** (gitignored) | Resume briefs for the current machine |
| **Local graph** | `.sdlc/index.sqlite` | **No** | Regenerable query cache |
| **Resolve excerpts** | `.sdlc/resolved/` | **No** | Per-Work-ID slices (e.g. progress) |

`agent-context/` still holds **install-time** harness, playbooks, and extensions.
It is no longer the hot session bus or the place to pile feature mirrors.

## Hot sessions

```bash
./scripts/sdlc.sh start
# → .sdlc/sessions/<timestamp>-<phase>-<WORK-ID>.md
# → .sdlc/sessions/current-session.md   (symlink/copy of latest)
```

Open **`.sdlc/sessions/current-session.md`**, not `agent-context/sessions/…`.

The brief includes:

- Framework orientation
- **Resolved Context** table (from `resolve-agent-context.sh`)
- Resume Prompt (paste into chat)

Legacy `agent-context/sessions/` may remain after upgrades; new writes go hot.
Rotation/archive still applies under `.sdlc/sessions/` when configured.

Details: [agent-session-scripts.md](agent-session-scripts.md)

## Lean memory layout

```text
spdd/memory/
  README.md
  context-index.md          # area × kind index (dual-written to legacy path for Guide)
  pointers.jsonl            # append-only pointer ledger
  registry.jsonl            # lean claim ledger (alongside work-registry.tsv)
  lessons/
    decisions.md
    pitfalls.md
    patterns.md
  entries/
    progress.md             # shared progress ledger (## WORK-ID or ### ts - WID - phase)
    …                       # analysis / metric / … as needed
```

### Progress ledger formats

Both are valid and ingested by `db rebuild`:

```markdown
## FEAT-001-example

- Area: src/billing
- Phase: code
- T01 complete — greet helper
```

```markdown
### 2026-08-08T12:00:00Z - FEAT-001-example - code

- Code areas: src/billing
- T01 complete — greet helper
```

### Work-scoped progress

`resolve-agent-context.sh` does **not** inject the whole shared `progress.md`.
It extracts the active Work ID’s section into:

```text
.sdlc/resolved/progress-<WORK-ID>.md
```

and adds that path to Resolved Context. Other Work IDs do not bleed into the
session brief.

## Feature mirrors

New workflow paths **do not** require `agent-context/features/<WORK-ID>/…`
mirrors. Verifiers accept lean-first artifacts:

| Check | Prefer | Legacy fallback |
| ----- | ------ | --------------- |
| Requirement | `requirements/milestones/<WID>.md` | `features/<WID>/requirement.md` |
| Review | `spdd/reviews/<WID>-review.md` | `features/<WID>/review.md` |
| Sync | `spdd/sync/<WID>-sync.md` | `features/<WID>/sync-log.md` |
| Retro | `spdd/memory/entries/retro.md` (section) or lean lessons | `features/<WID>/retro.md` |

Upgrade can move old mirrors aside; see `sdlc-engine agent-context upgrade`.

## Pointer ledger

Each persist appends a JSON line to `spdd/memory/pointers.jsonl` (id, kind,
work_id, intent, paths, links, ts). Reconstruct / list via the engine pointer
APIs and SQLite `pointer` rows after rebuild.

Spike note: [SPIKE-087](agent-context-cleanup/spikes/SPIKE-087-git-pointer-protocol.md)

## Day-to-day commands

```bash
./scripts/sdlc.sh start
./scripts/sdlc.sh capture --work-id FEAT-001-example --phase code \
  --summary "…" --validation "…"

./scripts/resolve-agent-context.sh --target . --phase code --work-id FEAT-001-example

./scripts/sdlc.sh db rebuild
./scripts/sdlc.sh db lookup --work-id FEAT-001-example --markdown
```

## Related

- [What's new in v2.0.0a6](whats-new-v2.0.0a6.md)
- [Triple-path context](triple-path-context.md)
- [Context loading and scaling](context-loading-and-scaling.md)
- Stay-set inventory: [agent-context-cleanup/STAY-SET.md](agent-context-cleanup/STAY-SET.md)
