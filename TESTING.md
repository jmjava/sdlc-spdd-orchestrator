# Testing Strategy

This project treats `/sdlc-spdd-*` command validation as a **confidence stack**, not
100% deterministic automation.

Cursor/Copilot chat runtime is nondeterministic and UI-driven. We verify what can be
proven automatically, then run a short manual smoke for the rest.

## Confidence Stack

| Level | Goal | Fully automatable? | How |
|------|------|---------------------|-----|
| 1. Deterministic CI | Prevent adapter/config drift | Yes | GitHub Actions + validator scripts |
| 2. Post-invocation effects | Prove command side-effects happened | Mostly | `verify-agent-command-effects.sh` |
| 3. Manual chat smoke | Validate real chat invocation path | No | Short guided run in Cursor/Copilot |

## Always-On CI Gates

In orchestrator repo:

- `validate-command-adapters` (`.github/workflows/validate-command-adapters.yml`)
- `validate-canvas` (`.github/workflows/validate-canvas.yml`)
- `validate-diagrams` (`.github/workflows/validate-diagrams.yml`)

In installed target projects (when both Cursor + Copilot adapters are installed):

- `.github/workflows/validate-sdlc-spdd-adapters.yml`

## Local Smoke Protocol (5-10 minutes)

Use one canonical Work ID and one operation.

1. In chat, run:

       /sdlc-spdd-plan @requirements/<topic>.md @ROADMAP.md @milestone-1.md
       /sdlc-spdd-architect @spdd/canvas/<WORK-ID>.md
       /sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation T01
       /sdlc-spdd-review @spdd/canvas/<WORK-ID>.md

2. In terminal, verify effects:

       ./scripts/sdlc-spdd/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step plan
       ./scripts/sdlc-spdd/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step architect
       ./scripts/sdlc-spdd/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step code --operation T01
       ./scripts/sdlc-spdd/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step review

3. Capture memory and planning sync:

       ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase code --summary "<summary>" --validation "<tests>" --milestone milestone-1.md --roadmap-note "<progress>" --next "<next command>"
       ./scripts/sdlc-spdd/verify-agent-command-effects.sh --target . --work-id <WORK-ID> --step capture --milestone milestone-1.md --require-roadmap

## Release Confidence Contract

Before release or major merge, require:

- [ ] CI gates green (adapters + canvas + diagrams)
- [ ] One manual smoke run completed in either Cursor or Copilot
- [ ] `verify-agent-command-effects.sh` passes for `plan`, `architect`, `code`, `review`, `capture`
- [ ] Milestone/session-notes sync confirmed for the tested Work ID

## Known Blind Spots (Expected)

- CI cannot execute Cursor/Copilot chat UI itself.
- LLM wording is nondeterministic; we validate artifacts/invariants instead.
- Adapter parity checks enforce structure and guardrails, not semantic quality of every response.
