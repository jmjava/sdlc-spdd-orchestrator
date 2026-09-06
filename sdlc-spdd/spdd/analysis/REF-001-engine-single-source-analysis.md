# Analysis: REF-001 — Single source of truth for gate semantics

## Metadata

- Work ID: REF-001-engine-single-source
- Date: 2026-09-06
- Depends on: SPIKE-004; CHORE-003 merged (`7b8a139` / PR #237)
- Constructs: C-COMPLY (named SUT; dual-engine confound)

## Scope Lock

### In Scope

- Name Python `WorkflowEngine.gate_check` as the Milestone 2 system under test
- Default `SDLC_ENGINE=auto` so operators with the engine get Python
- When Python is importable, workflow `gate` delegates to it even if `SDLC_ENGINE=shell`
- `SDLC_GATE_ENGINE=shell` remains an explicit fallback (workflow harness / no-engine installs)
- ROADMAP + TESTING state the SUT

### NOT in Scope

- Deleting shell scripts (install/upgrade stay shell)
- New workflow phases
- Making the bash fallback implement FEAT-014/016 minima itself (that would duplicate semantics)
- Embabel upstream

## Recommendation

One gate implementation: Python. Shell CLI may still run `next`/`claim` when `SDLC_ENGINE=shell`, but it must not apply the pre-FEAT-014 substring gate while Python is sitting next to it.
