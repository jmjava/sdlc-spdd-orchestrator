# Engine system under test (REF-001)

**Work ID:** REF-001-engine-single-source  
**Construct:** C-COMPLY (named semantics; dual-engine confound)

This names the **system under test** for Milestone 2 evaluation. It is not a claim that every shell script is gone.

## SUT

**Python `WorkflowEngine.gate_check`** (`engine/src/sdlc_engine/workflow.py`), invoked as:

```bash
./scripts/sdlc.sh gate --phase code --work-id <WID>
# default SDLC_ENGINE=auto → Python when sdlc_engine is importable
sdlc-engine gate --phase code --work-id <WID>
```

FEAT-014 semantic minima and FEAT-016 review/`Files:` checks live here. Shell `validate-reasons-canvas.sh` is a CI helper, not a second evaluation condition.

## Defaults

| Variable | Default | Meaning |
|----------|---------|---------|
| `SDLC_ENGINE` | `auto` | Prefer Python for the `sdlc.sh` CLI when importable |
| `SDLC_ENGINE=python` | — | Require Python; fail if missing |
| `SDLC_ENGINE=shell` | — | Bash workflow CLI (`next`/`claim`/…). **Gates still call Python** when importable |
| `SDLC_GATE_ENGINE=shell` | unset | Force the bash substring fallback. **Not the SUT.** Used by `tests/test-sdlc-workflow.sh` |

`sdlc.sh capture`, `start`, and `accept` stay on the shell path under `auto`. Python equivalents are `local capture` and `context accept`.

## What is not the SUT

- `SDLC_GATE_ENGINE=shell` fallback (pre-FEAT-014 `ready for coding` grep; no `Files:` mapping)
- Adapter-text parity (`validate-command-adapters.sh`)
- Live-consumer matrix (Cursor-oriented; not C-PORT)

Until you freeze `SDLC_ENGINE=auto` or `python` in the slice log, do not treat a shell-fallback gate pass as C-COMPLY.
