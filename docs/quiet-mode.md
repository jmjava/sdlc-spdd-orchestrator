# Quiet / product-test mode

**Shipped in `v2.0.0a6`** ([#91](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/91)).

Quiet mode is for **product work and field testing** inside a repo that also
dogfoods SDLC-SPDD. It keeps context retrieve, sessions, and gates available —
but stops recommending the next `/sdlc-spdd-*` T## dogfood command.

## When to turn it on

- You are implementing the *product*, not exercising the framework itself
- Demos where T## gravity confuses the audience
- CI / agents that should load resolved context and continue the task

Leave it **off** when you are deliberately dogfooding the SDLC-SPDD lifecycle
(plan → architect → code → review) on this orchestrator.

## How to enable

Any one of:

| Mechanism | Example |
| --------- | ------- |
| Environment | `export SDLC_QUIET=1` (also `true` / `yes` / `on`, case-insensitive) |
| Harness marker | create `agent-context/harness/quiet-mode.md` (any content) |
| Session flag | `./scripts/start-agent-session.sh … --quiet` |
| CLI inspect | `sdlc-engine agent-context quiet-status` |

```bash
# Shell workflow
SDLC_QUIET=1 ./scripts/sdlc.sh next
SDLC_QUIET=on ./scripts/sdlc.sh status --json   # includes "quiet": true

# Python engine
SDLC_QUIET=1 sdlc-engine next
sdlc-engine agent-context quiet-status
sdlc-engine agent-context quiet-status --quiet   # force flag
```

## What changes

| Surface | Quiet off | Quiet on |
| ------- | --------- | -------- |
| `sdlc.sh next` / `sdlc-engine next` | Phase + recommended `/sdlc-spdd-*` | Short quiet blurb — continue the product task |
| `status` JSON | no/`quiet:false` | `quiet: true`, recommended_command = quiet blurb |
| Session Resume Prompt | May steer toward next T## | No T## dogfood gravity |
| Context retrieve / SQLite / Guide | Available | Still available |

Default quiet blurb (keep shell + Python in sync):

> Quiet mode: load resolved context and continue the product task. Skip
> recommended `/sdlc-spdd-*` T## dogfood commands unless explicitly requested.

## What does **not** change

- Work ID pointer, phase state, and gates still work
- `claim` / `start` / `capture` / `db` still work
- You can still run `/sdlc-spdd-*` manually if you want

## Related

- [What's new in v2.0.0a6](whats-new-v2.0.0a6.md)
- Spike note: [SPIKE-091](agent-context-cleanup/spikes/SPIKE-091-quiet-mode.md)
- Code: `engine/src/sdlc_engine/quiet.py`, `agent-context/sdlc-workflow.sh`
