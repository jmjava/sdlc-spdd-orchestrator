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
- `test-sdlc-pointer` (`.github/workflows/test-sdlc-pointer.yml`)
- `test-sdlc-workflow` (`.github/workflows/test-sdlc-workflow.yml`)
- `test-session-memory` (`.github/workflows/test-session-memory.yml`)
- `test-index-spdd-analysis` (`.github/workflows/test-index-spdd-analysis.yml`)
- `test-resolve-agent-context` (`.github/workflows/test-resolve-agent-context.yml`)
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

### SDLC pointer harness

`./tests/test-sdlc-pointer.sh` exercises `agent-context/sdlc-pointer.sh`:

- CLI round-trip (`set`/`get`/`reset`)
- Guarded run (`run_against_pointer`) refusal on mismatch
- `SDLC_POINTER_OVERRIDE` bootstrap
- Integration with `start-agent-session.sh` pointer auto-set
- Install path copies the script to target projects

### SDLC workflow + team registry harness

`./tests/test-sdlc-workflow.sh` exercises `agent-context/sdlc-workflow.sh` and team registry:

- Phase/gate tracking, `next`/`advance`/`skip`/`shelf`/`resume`/`sync`
- `sdlc.sh` wrapper delegation
- Guarded `capture` (pointer must match)
- Team `claim`/`release`, stale TTL, branch/PR/Jira notes in `work-registry.tsv`
- Jira Key auto-link from `requirements/milestones/<WORK-ID>.md` on claim

### Session memory index + rotation harness

`./tests/test-session-memory-index.sh` runs `capture-session-memory.sh` and
`start-agent-session.sh` against throwaway targets and asserts the relevance-based
retrieval model:

- Per-session entry files are written under `agent-context/memory/sessions/`, and
  recorded areas appear in the entry.
- `agent-context/memory/code-areas.md` is the canonical category list: capture parses
  session documents (summary, `session-notes/`, `current-session.md`, the full latest
  timestamped session brief, canvas, progress log) for path/package tokens, matches
  known categories, and appends new ones. Covered sources include daily session notes
  and the latest timestamped session brief.
- `session-index.md` is created with an `Areas` column and is ordered newest-first.
- `context-index.md` is a reverse index (area → sessions, decisions, pitfalls, patterns, analysis); two unrelated
  Work IDs that touch the same area are both discoverable under that area, and
  `--areas` values are de-duplicated. Decisions/pitfalls/patterns without resolved
  areas are written to memory files but not indexed.
- `agent-context/memory/phase-index.md` maps SDLC phase → static playbooks and harness files.
- `session-history.md` rotates: with `--history-limit`, the recent window is
  bounded and older entries move to `agent-context/memory/archive/`;
  `--no-history-rotate` keeps it append-only with no archive.
- `--dry-run` writes nothing.
- The `start-agent-session.sh` brief opens with a Framework Orientation section
  (framework bootstrap) and does not parse canvas file lists.

Code areas are parsed from session documents at capture (summary, `session-notes/`,
`current-session.md`, the full latest timestamped session brief, canvas, progress
log, capture flags): known categories are matched, path/package tokens create new
categories. Optional `--areas` overrides or supplements parsing. The script never
narrows to `current-session.md`-only parsing.

### Index SPDD analysis harness

`./tests/test-index-spdd-analysis.sh` runs `index-spdd-analysis.sh` against
throwaway targets and asserts:

- `domain-index.md` rows for Domain Keywords and Code Areas from the analysis artifact
- `context-index.md` rows with Kind `analysis`
- new code areas appended to `code-areas.md`
- `--dry-run` writes nothing; missing analysis file exits non-zero

Run locally after changing `index-spdd-analysis.sh` or `domain-index.md`.

### Resolve agent context harness

`./tests/test-resolve-agent-context.sh` runs `resolve-agent-context.sh` against
throwaway targets and asserts:

- `--phase code` resolves `_all-agents/`, `coding-agent/`, and playbooks from `phase-index.md`
- `#SkillName` resolves `extensions/skills/` and `*-playbook.md` files
- `!SkillName` excludes a skill even when also requested with `#`
- `--work-id` / `--areas` filter `context-index.md` by code area; anchor-only rows do not load whole memory logs
- `--list-skills` discovers skills and playbook-derived names
- `--format json` returns paths, areas, and index rows
- `start-agent-session.sh` resume prompt skips artifacts already listed in Resolved Context

Run locally after changing `resolve-agent-context.sh`, extension templates, or
`start-agent-session.sh` Resolved Context integration.

### Whole-ecosystem grounding norm (enforced)

Every supported assistant must ship an **always-on grounding file** that loads on
every interaction (not only when a `/sdlc-spdd-*` command runs):

- Cursor: `.cursor/rules/sdlc-spdd.mdc` (`alwaysApply: true`)
- GitHub Copilot: `.github/copilot-instructions.md`
- Claude Code: `CLAUDE.md`

`validate-command-adapters.sh` asserts each present grounding file contains the
shared operating-model anchors (the lifecycle line, `## Operating Model`,
`## Work Rules`) and the Planning + SPDD + SDLC artifacts (`ROADMAP.md`,
`milestone-*.md`, `session-notes/`, `spdd/analysis/`, `spdd/canvas/`,
`agent-context/sessions/`, `agent-context/memory/`, `/sdlc-spdd-analysis`).
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
