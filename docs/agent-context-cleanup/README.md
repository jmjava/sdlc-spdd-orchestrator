# Agent-context cleanup program

Index: [GitHub #92](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/92)  
End-state: [GitHub #93](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/93)

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
| `main` | Receives **one** final PR from integration when the program is done |

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
| #83 Lessons lean-git | `spikes/SPIKE-083-lessons-lean-git.md` | lean persist via ContextStore (partial; full lesson migration TBD) |
| #84 Registry | `spikes/SPIKE-084-registry.md` | claim rows + edges (partial) |
| #85 Sessions | `spikes/SPIKE-085-sessions.md` | ingested + `context_sessions` (hot-path write switch TBD) |
| #86 Feature mirrors | `spikes/SPIKE-086-feature-mirrors.md` | ingested as mirror kinds; removal/archive TBD |
| #88 SQLite graph | `spikes/SPIKE-088-sqlite-v2.md` | **schema v4** full capability model + coverage tests |
| #89 Guide contract | `spikes/SPIKE-089-guide-contract.md` | dual-write legacy index; Guide dual-read still TBD |
| #90 Orchestration | `spikes/SPIKE-090-orchestration.md` | ContextStore lesson + context_entry fan-out tests |
| #91 Quiet mode | `spikes/SPIKE-091-quiet-mode.md` | proposal accepted — **not implemented** |
| #80 Upgrade/re-init | (issue) | **not implemented** |

### Remaining before `integration → main`

1. Hot session writes to `.sdlc/sessions/` only (#85)  
2. Mirror removal / archive + tool path resolution (#86)  
3. Upgrade/re-init for legacy `agent-context/` (#80)  
4. Guide dual-index read in loader (#89)  
5. Quiet / product-test mode (#91)  
6. `capability_coverage().complete` green on real repo rebuild + proof tests for each remaining slice  

See `spikes/` and the GitHub issues above.
