# Cursor slash-command live checklist

Three layers:

1. **Adapters present** — `scenarios/05-cursor-commands.sh` (CI-safe)
2. **Effect simulation** — `scenarios/06-slash-effects-sim.sh` (CI-safe; harness writes files)
3. **Real Cursor agents** — `./run-cursor-agent-matrix.sh` (local only; needs `CURSOR_API_KEY`)

Prefer (3) when you need proof the agent created canvas/analysis/review/etc.

Use this checklist for **manual Cursor IDE chat** (`/` picker) against a kept consumer:

```bash
LIVE_CONSUMER_KEEP=1 ./tests/live-consumer/run-matrix.sh
# then open /tmp/sdlc-spdd-live in Cursor
```

Work ID: `FEAT-001-hello-live`

| # | Slash command | After it runs, assert |
|---|---------------|------------------------|
| 1 | `/sdlc-spdd-init` | `verify-agent-command-effects.sh --step init` |
| 2 | `/sdlc-spdd-plan @requirements/milestones/FEAT-001-hello-live.md` | `--step plan` |
| 3 | `/sdlc-spdd-architect` | `--step architect` |
| 4 | `/sdlc-spdd-analysis` | `spdd/analysis/FEAT-001-hello-live-analysis.md` exists |
| 5 | `/sdlc-spdd-code` | `--step code --operation T01` |
| 6 | `/sdlc-spdd-api-test` | note skip or test artifact |
| 7 | `/sdlc-spdd-review` | `--step review` |
| 8 | `/sdlc-spdd-sync` | `--step sync` |
| 9 | `/sdlc-spdd-retro` | `--step retro` |
| 10 | `/sdlc-spdd-prompt-update` | `--step prompt-update` |
| 11 | `/sdlc-spdd-commit-message` | prints a message; does **not** commit |
| 12 | `/sdlc-spdd-sunset` | engine snapshot of PR/commits/Jira; stages ledger record |
| 13 | `/sdlc-spdd-whereami` | matches `./scripts/sdlc-spdd/sdlc.sh next` |
| 14 | `/sdlc-claim FEAT-001-hello-live` | pointer + registry updated |
| 15 | `/sdlc-next` | actionable "Do now" |
| 16 | `/sdlc-advance` | phase moves |
| 17 | `/sdlc-shelf` | pointer cleared |
| 18 | `/sdlc-team` | shows claims |

Effect verifier from the consumer root:

```bash
./scripts/sdlc-spdd/verify-agent-command-effects.sh \
  --target . --work-id FEAT-001-hello-live --step plan
```
