# Real Cursor agent slash matrix (local only)

Drives a **real Cursor agent** (SDK local runtime) against a seeded consumer so
canvas / analysis / review / sync / retro are created by the agent — not by the
test harness.

## What this is / isn't

| | |
|--|--|
| **Is** | Same Cursor agent harness + models, `cwd` = seeded consumer, each `.cursor/commands/<slash>.md` executed, then `verify-agent-command-effects.sh` |
| **Isn't** | Clicking `/` in the Cursor IDE chat UI |
| **Isn't** | CI-safe (needs `CURSOR_API_KEY`, network, paid inference, slow) |

## Setup

1. Create an API key: [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations)  
   (This is a **Cursor user/API key**, not a GitHub PAT. `BROAD_REPO_TOKEN` is separate.)

2. Store it locally (any one):

```bash
# A) shell export
export CURSOR_API_KEY=cursor_...

# B) same place-pattern as BROAD_REPO_TOKEN file
mkdir -p ~/.config/courseforge && chmod 700 ~/.config/courseforge
printf '%s' 'cursor_...' > ~/.config/courseforge/cursor-api-key
chmod 600 ~/.config/courseforge/cursor-api-key

# C) gitignored orchestrator .env (next to OPENAI_API_KEY etc.)
echo 'CURSOR_API_KEY=cursor_...' >> .env
```

For **GitHub Actions**, add the same key as repo secret `CURSOR_API_KEY`
(Settings → Secrets and variables → Actions). Workflow
`test-live-consumer.yml` runs the SDK job only when that secret is present.

Optional: also add `CURSOR_API_KEY` under **Cursor Dashboard → Cloud Agents → Secrets**
beside `BROAD_REPO_TOKEN` if cloud agents need it. That does **not** replace the
GitHub Actions secret or local file/export.

3. From the orchestrator repo:

```bash
./tests/live-consumer/run-cursor-agent-matrix.sh

# subset while iterating:
./tests/live-consumer/run-cursor-agent-matrix.sh --only init,claim,plan
```

Optional:

```bash
export LIVE_CURSOR_MODEL=composer-2.5
export LIVE_CONSUMER_ROOT=/tmp/sdlc-spdd-live
export LIVE_WORK_ID=FEAT-001-hello-live
```

## After a run

Inspect agent-created artifacts under `/tmp/sdlc-spdd-live`:

- `spdd/canvas/FEAT-001-hello-live.md`
- `spdd/analysis/`, `spdd/reviews/`, `spdd/sync/`
- `.sdlc/sessions/current-session.md`, `spdd/memory/lessons.jsonl`

## Full persistence test (SDK + SQLite)

```bash
./tests/live-consumer/run-cursor-persistence-test.sh
```

Covers: agent-created artifacts → full capture → `.sdlc/index.sqlite` rebuild/query/export
→ delete+regenerate → `Agent.resume` → pointer/`sdlc.sh next` still durable
→ `start-agent-session` embeds **Local SQLite Index** into the brief → agent reads it.
