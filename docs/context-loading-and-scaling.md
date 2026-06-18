# Context Loading and Scaling

How agent context is loaded across Cursor, GitHub Copilot, and Claude Code, what
is loaded automatically versus on demand, and how the model behaves as a project
grows.

> Short answer: **not everything is loaded.** Only one small, fixed-size grounding
> file per assistant is injected automatically on every request. All
> `agent-context/`, `spdd/`, and planning artifacts are loaded selectively.

## Two tiers of context

### Tier 1 — Always-on grounding (auto-injected every request)

Each assistant auto-loads exactly one grounding file. These files are
framework-owned and installed by `setup-agent-prompts.sh`.

| Assistant | File | Load mechanism |
|-----------|------|----------------|
| Cursor | `.cursor/rules/sdlc-spdd.mdc` | Front-matter `alwaysApply: true` injects it into every Chat/Agent request |
| GitHub Copilot | `.github/copilot-instructions.md` | Copilot auto-loads it for every Copilot Chat request in the repo |
| Claude Code | `CLAUDE.md` (repo root) | Auto-loaded at session start |

Properties:

- **Fixed size** (~2.5–2.9 KB each). The cost does not grow with the project.
- They **do not inline** memory, canvas, or planning content. They carry the
  operating model, a list of directories to consult, and the instruction to
  *load only the artifacts relevant to the current Work ID, phase, and operation*.
- They are kept in parity across assistants and CI-validated by
  `scripts/validate-command-adapters.sh`.

### Tier 2 — On-demand artifacts (never auto-loaded)

Everything below is pulled into context **only when needed**:

- `requirements/`, `requirements/milestones/`
- `spdd/canvas/`, `spdd/tasks/`, `spdd/reviews/`, `spdd/sync/`
- `ROADMAP.md`, `milestone-*.md`, `session-notes/`
- `agent-context/sessions/`, `agent-context/memory/`,
  `agent-context/features/`, `agent-context/harness/`, `agent-context/playbooks/`

An artifact enters context only through one of three paths:

1. **You `@`-mention it** in a prompt (for example `@spdd/canvas/FEAT-001.md`).
2. **A session brief or command names it** — `agent-context/sessions/current-session.md`
   and the resume prompt written by `start-agent-session.sh` point at specific files.
3. **The agent chooses to read it** based on the Tier 1 instruction.

## What about the other `.github/*.md` files?

Only `.github/copilot-instructions.md` is agent context (and only for Copilot).
The remaining `.github/` files are **GitHub UI templates**, not agent context, and
are never loaded into any assistant:

- `.github/ISSUE_TEMPLATE/*.yml` — used by GitHub when opening an issue.
- `.github/pull_request_template.md` — used by GitHub when opening a pull request.
- `.github/workflows/*.yml` — CI definitions run by GitHub Actions.

They have **zero effect** on agent context size or scaling.

## How it scales

The always-on tier is constant, so it scales cleanly. All scaling pressure is in
the on-demand tier, and it is a **soft** limit: progressive disclosure is an
instruction, not an enforced mechanism. Pressure points as a project grows:

| Artifact | Growth | Risk | Mitigation |
|----------|--------|------|------------|
| `agent-context/memory/session-history.md` | Bounded recent window (rotates) | Low — `capture-session-memory.sh` keeps the most recent `--history-limit` entries inline and moves older ones to `agent-context/memory/archive/` | Retrieve via the indexes below, not by reading this file |
| `agent-context/sessions/` | One brief per session (unbounded count) | Low if agents read only `current-session.md` | Treat `current-session.md` as the single entry point |
| `agent-context/features/`, `spdd/canvas/`, `spdd/reviews/`, `spdd/sync/` | One set per Work ID | Low when scoped to one Work ID; listings grow | Scope reads to the active Work ID subtree |
| `session-notes/` | One file per day (unbounded count) | Low — only recent notes matter | Read only the current and recent dates |

## Bootstrapping the framework each session

So the agent knows how to operate *within the framework* from the start of every
session — not just what work to do — two things load up front:

- The **always-on grounding file** (Tier 1) carries the operating model and the
  context-loading rules on every request.
- The **session brief** (`agent-context/sessions/current-session.md`, written by
  `start-agent-session.sh`) opens with a **Framework Orientation** section that
  points new agents at how the framework works (operating model, three-part path,
  session and context-loading rules) before any work begins.

## Practical loading rules

To keep context small and relevant regardless of project size:

1. **Start at `agent-context/sessions/current-session.md`.** Read its Framework
   Orientation, then follow its pointers instead of scanning directories.
2. **Scope to one Work ID.** A Work ID's own history is its
   `agent-context/features/<WORK-ID>/progress-log.md` and `spdd/canvas/<WORK-ID>.md`.
   Read those, not the global history.
3. **Retrieve by relevance, not recency** (see indexes below). Sessions for
   unrelated work are interleaved in time, so never read history top-to-bottom.
4. **`@`-mention deliberately.** Naming specific files is cheaper and more precise
   than asking the agent to discover them.

## Retrieval indexes (relevance, not recency)

The REASONS Canvas is **prose**. The agent determines which **code areas** a piece
of work matches (a Java package, or a directory for everything else) by reading
that prose against the codebase — this is not derived by parsing the canvas. Two
indexes turn those areas into fast, relevant retrieval:

| Index | Keyed by | Use it to |
|-------|----------|-----------|
| `agent-context/memory/code-area-index.md` | Code area → work/sessions | Find all prior work in an area you are about to touch, across any Work ID or date |
| `agent-context/memory/session-index.md` | Session (newest first), with Work ID + Areas columns | Filter by Work ID or Area to find related sessions; full detail in `agent-context/memory/sessions/<entry>` |

The agent records the areas it matched at capture time:

    ./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> \
      --phase code --summary "<summary>" --areas "src/billing, com.acme.billing"

Recency only orders matches *within* an area or Work ID; it is never the primary
key.

## Per-phase context budget

A practical default for which artifacts each phase should load:

| Phase | Load |
|-------|------|
| init | repo structure, stack detection output |
| plan | the requirement, `ROADMAP.md`, active `milestone-*.md` |
| architect | the Work ID canvas, `agent-context/memory/architecture-decisions.md`, `agent-context/harness/` |
| code | the Work ID canvas, that feature's `progress-log.md`, `agent-context/memory/known-pitfalls.md` |
| review | the Work ID canvas, the diff, `agent-context/harness/quality-gates.md` |
| retro / sync | the Work ID canvas, that feature's progress log, the relevant memory file being updated |

## Related

- [Architecture](architecture.md) — five delivery concerns and progressive loading.
- [Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md) — planning-narrative artifacts.
- [Maintaining your project](maintaining-your-project.md) — memory hygiene and session maintenance.
