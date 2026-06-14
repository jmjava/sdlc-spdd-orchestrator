# Testing Strategy

This project treats `/sdlc-spdd-*` command validation as a **confidence stack**, not
100% deterministic automation.

Cursor/Copilot/Claude Code chat runtime is nondeterministic and UI-driven. We verify
what can be proven automatically, then run a short manual smoke for the rest.

## Confidence Stack

| Level | Goal | Fully automatable? | How |
|------|------|---------------------|-----|
| 1. Deterministic CI | Prevent adapter/config drift | Yes | GitHub Actions + validator scripts |
| 2. Post-invocation effects | Prove command side-effects happened | Mostly | `verify-agent-command-effects.sh` |
| 3. Manual chat smoke | Validate real chat invocation path | No | Short guided run in Cursor/Copilot/Claude Code |

## Always-On CI Gates

In orchestrator repo:

- `validate-command-adapters` (`.github/workflows/validate-command-adapters.yml`)
- `test-adapter-install` (`.github/workflows/test-adapter-install.yml`)
- `validate-canvas` (`.github/workflows/validate-canvas.yml`)
- `validate-diagrams` (`.github/workflows/validate-diagrams.yml`)

### Adapter install regression harness

`./tests/test-adapter-install.sh` installs each assistant adapter (Cursor,
Copilot, Claude Code) into throwaway target directories and asserts:

- Single-assistant installs (`--cursor`, `--copilot`, `--claude`) produce only
  that assistant's files and no others.
- `--all` and `upgrade --all` install all three; Cursor and Copilot files stay
  byte-identical to their templates.
- `verify-project-install.sh` passes for every install combination.
- `validate-command-adapters.sh` still **fails** when a Cursor/Copilot guardrail
  is removed, a Required-Behavior step count diverges, or a command file is
  missing (negative tests).
- every assistant's always-on grounding file exists and covers the whole
  ecosystem; validation **fails** if Planning (`session-notes/`), SPDD
  (`spdd/canvas/`), or the Cursor grounding rule is dropped (negative tests).

Run it locally before changing any install/upgrade script or command template.

### Whole-ecosystem grounding norm (enforced)

Every supported assistant must ship an **always-on grounding file** that loads on
every interaction (not only when a `/sdlc-spdd-*` command runs):

- Cursor: `.cursor/rules/sdlc-spdd.mdc` (`alwaysApply: true`)
- GitHub Copilot: `.github/copilot-instructions.md`
- Claude Code: `CLAUDE.md`

`validate-command-adapters.sh` asserts each present grounding file contains the
shared operating-model anchors (the lifecycle line, `## Operating Model`,
`## Work Rules`) and the Planning + SPDD + SDLC artifacts (`ROADMAP.md`,
`milestone-*.md`, `session-notes/`, `spdd/canvas/`, `agent-context/memory/`).
This makes whole-ecosystem awareness the norm for all work across every assistant
— and runs in CI both here and inside installed target projects.

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
- [ ] One manual smoke run completed in Cursor, Copilot, or Claude Code
- [ ] `verify-agent-command-effects.sh` passes for `plan`, `architect`, `code`, `review`, `capture`
- [ ] Milestone/session-notes sync confirmed for the tested Work ID

## Known Blind Spots (Expected)

- CI cannot execute Cursor/Copilot/Claude Code chat UI itself.
- LLM wording is nondeterministic; we validate artifacts/invariants instead.
- Adapter parity checks enforce structure and guardrails, not semantic quality of every response.
