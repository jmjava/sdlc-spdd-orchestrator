# Engine system under test (REF-001, REF-003)

**Work ID:** REF-001-engine-single-source (Milestone 2), closed out by REF-003-one-engine (Milestone 3)  
**Construct:** C-COMPLY (named semantics; dual-engine confound)

This names the **system under test** for evaluation. Since REF-003 there is
exactly one engine: the Python `sdlc-engine` package. The bash workflow twin
(`sdlc-workflow.sh` / `sdlc-team-registry.sh` / `sdlc-pointer.sh`) and the
`SDLC_ENGINE` / `SDLC_GATE_ENGINE` switches were removed.

## SUT

**Python `WorkflowEngine.gate_check`** (`engine/src/sdlc_engine/workflow.py`), invoked as:

```bash
./scripts/sdlc.sh gate --phase code --work-id <WID>   # thin dispatcher → python -m sdlc_engine
sdlc-engine gate --phase code --work-id <WID>
```

FEAT-014 semantic minima and FEAT-016 review/`Files:` checks live here. Shell
`validate-reasons-canvas.sh` is a CI helper, not a second evaluation condition.

## One engine

| Surface | Implementation |
|---------|----------------|
| `sdlc.sh <verb>` | `exec python -m sdlc_engine --root <root> <verb>`; no shell verbs remain |
| `capture`, `start`, `complete`, `accept`, `session *` | Python top-level verbs (`sdlc_engine.commands.context`) |
| Gates | Python only; there is no substring fallback |
| `SDLC_ENGINE`, `SDLC_GATE_ENGINE` | Removed. Setting either makes `sdlc.sh` exit 2 with a removal notice |

## What is not the SUT

- Adapter-text parity (`validate-command-adapters.sh`)
- Live-consumer matrix (Cursor-oriented; not C-PORT)
- Install/upgrade packaging shell (`init-project.sh`, `upgrade-project.sh`): copies files, holds no workflow logic

A gate pass is C-COMPLY evidence only when produced by the Python engine; since
REF-003 that is the only way a gate can pass.
