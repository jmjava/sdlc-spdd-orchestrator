# Engine system under test (REF-001)

**Work ID:** REF-001-engine-single-source  
**Construct:** C-COMPLY (named semantics; dual-engine confound)

This names the **system under test** for Milestone 2 evaluation. It is not a claim that every shell script is gone.

## SUT

**Python `WorkflowEngine.gate_check`** (`engine/src/sdlc_engine/workflow.py`), invoked as:

```bash
./scripts/sdlc.sh gate --phase code --work-id <WID>
# the dispatcher requires sdlc_engine; there is no other gate implementation
sdlc-engine gate --phase code --work-id <WID>
```

FEAT-014 semantic minima and FEAT-016 review/`Files:` checks live here. Shell `validate-reasons-canvas.sh` is a CI helper, not a second evaluation condition.

## Defaults

REF-003 removed the second implementation, so there is no engine to select. The
variables survive only as rejected or inert inputs.

| Variable | Default | Meaning |
|----------|---------|---------|
| unset | — | `sdlc.sh` runs the Python engine; missing Python 3.12 or `sdlc_engine` fails with a setup hint |
| `SDLC_ENGINE=python` | — | Accepted as a no-op; it already names the only engine |
| `SDLC_ENGINE=shell` | — | **Rejected** (non-zero, "no longer supported"); it cannot select a bash workflow CLI |
| `SDLC_GATE_ENGINE=shell` | unset | **Rejected** (non-zero); the bash substring fallback is gone, so it is not an evaluation condition |

`sdlc.sh capture`, `start`, and `accept` are retained shell utilities that call
the Python engine; they no longer host lifecycle semantics. Python equivalents
are `local capture` and `context accept`.

Before REF-003 the default was `SDLC_ENGINE=auto` (Python when importable) and
`SDLC_GATE_ENGINE=shell` forced a pre-FEAT-014 `ready for coding` grep with no
`Files:` mapping. Slice logs recorded before REF-003 must still name the frozen
engine; a shell-fallback gate pass was never C-COMPLY.

## What is not the SUT

- Adapter-text parity (`validate-command-adapters.sh`)
- Live-consumer matrix (Cursor-oriented; not C-PORT)
