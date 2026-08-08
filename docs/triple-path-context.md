# Triple-path context store

**Shipped in `v2.0.0a6`.** Same Work ID facts can live in three backends at once:

| Path | Store | Role | Failure mode |
| ---- | ----- | ---- | ------------ |
| 1 | **Git stay-set + pointers** | Reviewable source of truth | Required — persist fails if this fails |
| 2 | **SQLite** (`.sdlc/index.sqlite`) | Local relational graph / FTS | Soft-fail → `partial` |
| 3 | **Guide** (Neo4j SPDD projection) | Typed-edge retrieve | Soft-fail → `partial` |

Implementation: `engine/src/sdlc_engine/context_store.py` + `persistence.py`.

## Mental model

```text
                 persist_lesson / persist_entry / capture
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             lean git files    SQLite upsert    Guide project
             + pointers.jsonl  (if enabled)     (if enabled)
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                    retrieve(work_id=…, area=…)
                    assembles only *enabled* backends
```

- **`ok`** on a persist result means the git leg succeeded.
- **`partial`** means git succeeded but a secondary backend errored (not skipped).
- **Skipped** backends (disabled in config) are not errors.

## Configure backends

Priority: env `CONTEXT_BACKENDS` → `.sdlc/persistence-config.json` → defaults (all three).

Canonical names:

- `git-pointers` — always included (cannot be turned off)
- `sqlite`
- `guide-dice`

```bash
# Inspect
sdlc-engine context backends
./scripts/resolve-context-backend.sh --target .

# Set (writes .sdlc/persistence-config.json)
sdlc-engine context backends --set git-pointers,sqlite --notes "no Guide on laptop"

# Env override for one shell
export CONTEXT_BACKENDS=git-pointers,sqlite
```

Ops console: **Persistence** tab → refresh / save
([ops-console.md](ops-console.md)).

Aliases accepted: `git`/`files` → `git-pointers`, `db` → `sqlite`, `guide`/`dice` → `guide-dice`.
Unknown names are rejected on save (CLI exit 2 / HTTP 400).

### Guide URL

- Configured URL is optional; leave blank to use `GUIDE_BASE_URL` or `http://localhost:$GUIDE_PORT`.
- Saving persistence options does **not** bake the effective default URL into the config file.

### Explicit opt-out

If config/env omits `guide-dice`, `resolve-context-backend.sh` will **not** re-add it
just because `agent-context/harness/guide-dice.md` exists. Marker + live probe only
apply on the defaults path.

## Persist

```bash
# Lesson (decision | pitfall | pattern)
sdlc-engine context persist-lesson \
  --kind pitfall \
  --work-id FEAT-001-example \
  --area src/billing \
  --body "Never open PRs against embabel/guide" \
  --no-guide          # optional: skip Guide even if enabled

# Non-lesson entry (progress, analysis, metric, …)
sdlc-engine context persist-entry \
  --kind progress \
  --work-id FEAT-001-example \
  --body "T01 complete — greet helper"
```

Lean files written (examples):

- `spdd/memory/lessons/pitfalls.md` (append section)
- `spdd/memory/entries/progress.md` (append `## <WORK-ID>` block)
- `spdd/memory/context-index.md` (+ legacy dual-write to `agent-context/memory/context-index.md`)
- `spdd/memory/pointers.jsonl`

Capture via `sdlc.sh capture` / `capture-session-memory.sh` feeds the same stay-set.

## Retrieve

```bash
sdlc-engine context retrieve --work-id FEAT-001-example
sdlc-engine context retrieve --work-id FEAT-001-example --area src/billing
```

JSON includes `backends`, `git_pointers`, `sqlite_lessons`, `sqlite_graph`, `guide`
(or `skipped` markers when gated off). Retrieve honors the same backend gates as persist.

## Capability coverage

```bash
sdlc-engine context coverage
./scripts/sdlc.sh db rebuild   # refresh graph from stay-set + canvases
```

Schema v4 models requirements, canvases, lessons, context entries, edges, and
claims. See [local-sqlite-index.md](local-sqlite-index.md).

## When to use which backend

| Situation | Suggested set |
| --------- | ------------- |
| Laptop offline / CI unit tests | `git-pointers` or `git-pointers,sqlite` |
| Normal dogfood | `git-pointers,sqlite` |
| Full stack with Guide up | `git-pointers,sqlite,guide-dice` |

## Related

- [What's new in v2.0.0a6](whats-new-v2.0.0a6.md)
- [Quiet mode](quiet-mode.md)
- [Guide flow](guide-flow.md) (optional path 3 only)
- Spike notes: [SPIKE-090](agent-context-cleanup/spikes/SPIKE-090-orchestration.md)
