# Live consumer matrix

Idempotent **seed → install → exercise → flush** harness for a realistic
Cursor-only consumer project.

## Why

- Dogfooding the orchestrator repo misses installed paths (`sdlc-spdd/scripts/`).
- A long-lived sibling repo drifts and stops being a clean test.
- This harness wipes a fake git repo every run.

## Quick start

```bash
# From orchestrator repo root — shell + effect simulation (CI-safe)
./tests/test-live-consumer-matrix.sh

# Keep /tmp/sdlc-spdd-live for manual IDE slash checks
LIVE_CONSUMER_KEEP=1 ./tests/live-consumer/run-matrix.sh

# REAL Cursor agents (local only, needs CURSOR_API_KEY):
export CURSOR_API_KEY=cursor_...
./tests/live-consumer/run-cursor-agent-matrix.sh
# see cursor-agent/README.md
```

## Layout

| Path | Role |
|------|------|
| `seed/` | Mini app + milestone + canvas fixture |
| `seed-and-install.sh` | Flush, seed, `git init`, `--cursor` install |
| `scenarios/*.sh` | One scenario family each |
| `scenarios/08-full-populate.sh` | Golden capture: validation, decisions, pitfalls, patterns, milestone, roadmap, next, metrics |
| `run-matrix.sh` | Orchestrates all scenarios |
| `CURSOR-SLASH-LIVE.md` | Manual Cursor chat checklist |

After a kept run, inspect:

```bash
LIVE_CONSUMER_KEEP=1 ./tests/live-consumer/run-matrix.sh
less /tmp/sdlc-spdd-live/.sdlc/sessions/current-session.md
less /tmp/sdlc-spdd-live/ROADMAP.md
less /tmp/sdlc-spdd-live/requirements/milestones/milestone-1/MILESTONE-1.md
```

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `LIVE_CONSUMER_ROOT` | (mktemp) | Fixed consumer path |
| `LIVE_CONSUMER_KEEP` | `0` | When `1`, use/keep `/tmp/sdlc-spdd-live` |
| `LIVE_WORK_ID` | `FEAT-001-hello-live` | Primary Work ID |
| `SDLC_USER` | `live-matrix` | Registry owner name |
