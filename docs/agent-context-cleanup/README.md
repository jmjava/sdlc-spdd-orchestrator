# Agent-context cleanup program

Index: [GitHub #92](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/92)  
End-state: [GitHub #93](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/93)  
**Shipped:** `v2.0.0a6` / [#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109)

> **Operators:** start with the user guides, not this folder —  
> [What's new in v2.0.0a6](../whats-new-v2.0.0a6.md) ·
> [Hot sessions & lean memory](../hot-sessions-and-lean-memory.md) ·
> [Triple-path context](../triple-path-context.md) ·
> [Quiet mode](../quiet-mode.md).  
> This directory is the program / spike archive.

## End-state (locked)

Three **concurrent** projections of the **same** information:

1. **Lean git / cleaner agent-context** — contracts + pointers; not the session bus  
2. **SQLite** — same graph in **relational** form (tables / FKs)  
3. **Guide (Neo4j DICE)** — same graph as `__Entity__` nodes + typed edges  

Thin-in-git means lean **encoding**, not fewer features ([#82](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/82)).

### Stays in git ([#81](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/81))

| Artifact | Path |
|----------|------|
| Requirements → Jira | `requirements/milestones/<WORK-ID>.md`, `requirements/` |
| REASONS (SPDD progress) | `spdd/canvas/<WORK-ID>.md` (+ `spdd/analysis|reviews|sync` as governance) |

### Leaves git commit surface (`agent-context/` only — [#80](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/80))

Session briefs, feature mirrors, ephemeral locks, and other runtime noise under `agent-context/`.

## Branch process

| Branch | Role |
|--------|------|
| `cursor/agent-context-cleanup-integration-decf` | Integration line — all task work merges here |
| `cursor/agent-context-cleanup-<task>-decf` | Short-lived task branches off integration |
| `main` | Receives **one** final PR from integration — open as draft [#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109) |

Rules:

1. Keep the working tree clean: commit or discard; no long-lived dirty tabs.  
2. Task branches merge into **integration** (agent-managed). No human approval required for those merges.  
3. **Only** the final PR `integration → main` needs human approval — and **only when the program is 100% complete with tests** (full capability coverage + upgrade + quiet mode + mirror removal).  
4. Do not open intermediate PRs to `main`. Integration-only PRs are fine.  
5. Prefer small, focused commits per spike/feature slice.

## Work order

1. Constraints: stay-set (#81), parity (#82), end-state (#93) — this folder  
2. Encodings: pointers (#87), lessons (#83), registry (#84), sessions (#85)  
3. Stores: SQLite v2 (#88), Guide contract (#89)  
4. Orchestration: fan-out + assemble (#90)  
5. Migration: mirror removal (#86), upgrade/re-init (#80)  
6. UX: quiet / product-test mode (#91)

## Spike status

| Spike | Doc | Status |
|-------|-----|--------|
| #87 Git pointer protocol | `spikes/SPIKE-087-git-pointer-protocol.md` | implemented + unit tested |
| #83 Lessons lean-git | `spikes/SPIKE-083-lessons-lean-git.md` | lean persist via ContextStore |
| #84 Registry | `spikes/SPIKE-084-registry.md` | lean `registry.jsonl` + TSV + SQLite claims |
| #85 Sessions | `spikes/SPIKE-085-sessions.md` | **hot path `.sdlc/sessions/`** + SQLite upsert |
| #86 Feature mirrors | `spikes/SPIKE-086-feature-mirrors.md` | no new mirror writes; archive via upgrade |
| #88 SQLite graph | `spikes/SPIKE-088-sqlite-v2.md` | schema v4 + coverage tests |
| #89 Guide contract | `spikes/SPIKE-089-guide-contract.md` | orchestrator dual-write shipped; Guide dual-read on `jmjava/guide` **branch**, not merged |
| #90 Orchestration | `spikes/SPIKE-090-orchestration.md` | ContextStore fan-out + `context backends` + console Persistence tab |
| #91 Quiet mode | `spikes/SPIKE-091-quiet-mode.md` | `SDLC_QUIET` / `--quiet` / harness file |
| #80 Upgrade/re-init | (issue) | `sdlc-engine agent-context upgrade` → `.sdlc/legacy-export/` |

### Gate status (post-merge)

- [x] Full capability model (schema v4) + `capability_coverage().complete`  
- [x] Hot sessions (#85), upgrade (#80), mirror stop (#86), quiet (#91) with tests  
- [x] Persistence options (#90): `.sdlc/persistence-config.json`, `CONTEXT_BACKENDS`, ops console **Persistence** tab  
- [x] Fable hard-review passes cleared (criticals + Important + Nice-to-have): retrieve backend gating, capture-format DB ingest, work-scoped progress excerpts (`.sdlc/resolved/progress-<WORK-ID>.md`), …  
- [x] Orchestrator dual-write of lean + legacy context-index (#89) — Guide tag `sdlc-spdd-projection-v1` keeps working via the legacy path  
- [x] Integration merged to `main`: [#109](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/109) (release tag `v2.0.0a6`)  
- [ ] Guide dual-read (#89) merged in `jmjava/guide` — implemented on branch `cursor/spdd-dual-context-index-decf`, **not yet** on `jmjava/guide` `main` or the tag  

Hard rule: never PR/push/merge to `embabel/guide` — all Guide dogfood work goes through the `jmjava/guide` fork.

See `spikes/` and the GitHub issues above.
