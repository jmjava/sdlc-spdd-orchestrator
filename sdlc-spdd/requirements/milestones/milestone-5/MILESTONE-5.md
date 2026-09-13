# Milestone 5 — Make it fast (outline; not opened)

## Goal

Act on the measurement built in FEAT-004/005/015: optimize prompts and context loading with numbers, and finish the product surfaces that measurement needs. Per the ROADMAP posture this comes last and does not start until Milestone 3 P0 and P1 are complete.

**Stage:** make it fast.

## Candidate work (no Work IDs yet)

| Candidate | Why it waits |
|-----------|--------------|
| Act on metrics — prompt and context optimization driven by `sdlc-engine context metrics` (C-COMPLY, C-CONTEXT, C-REWORK, C-MEMORY) | Needs a stable single engine (REF-003) so the measured system is the shipped system |
| Context-budget telemetry and enforcement in `resolve-agent-context` | Needs REF-010 (resolve in Python) |
| Vue3 console parity and ADF viewer as a Vue tab; retire Flask-rendered pages | Needs REF-004 and REF-009 |
| Resume or close SPIKE-001 (Guide DICE hybrid) and SPIKE-002 (local models) with a go/no-go | Needs REF-007 (single Guide transport) and FEAT-017 IR baseline |
| Journal n ≥ 3 for TEST-002 (assistant behavior eval) | TEST-001 stop rule; independent of engineering work |

## Opening criteria

- Milestone 3 P0 and P1 checked off in `MILESTONE-3.md`.
- Milestone 4 P0 checked off (docs describe the system being measured).
- A SPIKE requirement that turns this outline into Work IDs with a REASONS canvas program plan.
