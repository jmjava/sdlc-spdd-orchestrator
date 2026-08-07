# Agent probes: FEAT-013-guide-git-incremental-upstream

Freeform verification log (canvas section V). Does not advance Operations.

## 2026-08-07T21:23Z — V01 Dual-env map

**Probe intent:** Can the agent name both checkouts, branches, active Work ID, and
next T##? Pass = orientation table matches reality.

| Item | Observed |
|------|----------|
| Orchestrator path | `/agent/repos/sdlc-spdd-orchestrator` |
| Orchestrator branch / tip | `cursor/embabel-context-graph-research-65ca` @ `8cc65ca` |
| Guide path | `/agent/repos/guide` |
| Guide branch / tip | `cursor/spike-003-absorption-tip-refresh-decf` @ `f870b73` |
| Guide pin tag | `sdlc-spdd-projection-v1` → `a6e3246` |
| Upstream tip (fetched) | `embabel/guide` `main` @ `67f5e9d` |
| Active Work ID | `FEAT-013-guide-git-incremental-upstream` |
| Phase / next op | code / **T02** |
| Verify command surfaced | yes (`./scripts/sdlc.sh next` Optional block) |

**Result:** Pass

**Repos touched:** both (read-only `git` / `ls` / `sdlc.sh next`). No product code changes.

## 2026-08-07T21:24Z — V02 Allowlist vs fork tip

**Probe intent:** Do Layer B allowlist paths exist on Guide tip, and can SPDD
paths be excluded from an upstreamable diff? Pass = allowlist present; SPDD not
required for Layer B.

| Check | Result |
|-------|--------|
| Allowlist paths on tip | 12/12 present |
| Layer B in `upstream/main...HEAD` | yes (git-incremental, maintenance, DataManager, GuideProperties, SecurityConfig, tests, …) |
| SPDD paths in same tip diff | yes (`com/embabel/guide/spdd/**`, docs, fixture) — **excludable** for FEAT-013 |
| Core Layer B imports `guide.spdd`? | no |

**Result:** Pass

**Repo touched:** `guide` (read-only). Orchestrator: canvas/probe log only.
