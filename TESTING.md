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
- `test-session-memory` (`.github/workflows/test-session-memory.yml`)
- `validate-canvas` (`.github/workflows/validate-canvas.yml`)
- `validate-diagrams` (`.github/workflows/validate-diagrams.yml`)

### Adapter install regression harness

`./tests/test-adapter-install.sh` installs each assistant adapter (Cursor,
Copilot, Claude Code) into throwaway target directories and asserts:

- Single-assistant installs (`--cursor`, `--copilot`, `--claude`) produce only
  that assistant's files and no others.
- No-flag setup/upgrade keeps the legacy Cursor + Copilot default; Claude Code
  is installed only with `--claude` or `--all`.
- `--all` and `upgrade --all` install all three; Cursor and Copilot files stay
  byte-identical to their templates.
- Upgrade preserves project-owned files such as an existing root `CLAUDE.md`
  and target-local adapter workflow customizations; only the managed
  SDLC-SPDD grounding block inside `CLAUDE.md` is added or refreshed.
- Repeated upgrades do not duplicate the managed `CLAUDE.md` grounding block,
  and `--dry-run` paths do not mutate target files.
- Installed target adapter workflows watch command files, always-on grounding
  files, and the target-local validator script.
- `verify-project-install.sh` passes for every install combination.
- `validate-command-adapters.sh` still **fails** when an adapter guardrail
  is removed, a Required-Behavior step count diverges, or a command file is
  missing (negative tests).
- every assistant's always-on grounding file exists and covers the whole
  ecosystem; validation **fails** if Planning (`session-notes/`), SPDD
  (`spdd/canvas/`), SDLC session context (`agent-context/sessions/`), or an
  assistant grounding file is dropped (negative tests).

Run it locally before changing any install/upgrade script or command template.
The CI workflow also runs `bash -n` over shell scripts before executing the
regression harness.

### Session memory index + rotation harness

`./tests/test-session-memory-index.sh` runs `capture-session-memory.sh` and
`start-agent-session.sh` against throwaway targets and asserts the relevance-based
retrieval model:

- Per-session entry files are written under `agent-context/memory/sessions/`, and
  the recorded `--areas` appear in the entry.
- `session-index.md` is created with an `Areas` column and is ordered newest-first.
- `code-area-index.md` is a reverse index (area → work/sessions); two unrelated
  Work IDs that touch the same area are both discoverable under that area, and
  `--areas` values are de-duplicated.
- `session-history.md` rotates: with `--history-limit`, the recent window is
  bounded and older entries move to `agent-context/memory/archive/`;
  `--no-history-rotate` keeps it append-only with no archive.
- `--dry-run` writes nothing.
- The `start-agent-session.sh` brief opens with a Framework Orientation section
  (framework bootstrap) and does not parse canvas file lists.

Code areas are supplied by the agent (which maps the prose REASONS Canvas to the
code) via `--areas`; the script records them but does not parse the canvas.

### Whole-ecosystem grounding norm (enforced)

Every supported assistant must ship an **always-on grounding file** that loads on
every interaction (not only when a `/sdlc-spdd-*` command runs):

- Cursor: `.cursor/rules/sdlc-spdd.mdc` (`alwaysApply: true`)
- GitHub Copilot: `.github/copilot-instructions.md`
- Claude Code: `CLAUDE.md`

`validate-command-adapters.sh` asserts each present grounding file contains the
shared operating-model anchors (the lifecycle line, `## Operating Model`,
`## Work Rules`) and the Planning + SPDD + SDLC artifacts (`ROADMAP.md`,
`milestone-*.md`, `session-notes/`, `spdd/canvas/`,
`agent-context/sessions/`, `agent-context/memory/`).
This makes whole-ecosystem awareness the norm for all work across every assistant
— and runs in CI both here and inside installed target projects when the target
adapter workflow is installed.

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

- [ ] CI gates green (adapter parity + adapter install/upgrade + canvas + diagrams)
- [ ] One manual smoke run completed in Cursor, Copilot, or Claude Code
- [ ] `verify-agent-command-effects.sh` passes for `plan`, `architect`, `code`, `review`, `capture`
- [ ] Milestone/session-notes sync confirmed for the tested Work ID

## Known Blind Spots (Expected)

- CI cannot execute Cursor/Copilot/Claude Code chat UI itself.
- LLM wording is nondeterministic; we validate artifacts/invariants instead.
- Adapter parity checks enforce structure and guardrails, not semantic quality of every response.
