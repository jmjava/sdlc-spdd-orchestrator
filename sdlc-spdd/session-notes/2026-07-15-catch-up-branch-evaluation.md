# Catch-up: unmerged branches and what to do next

> **Superseded:** See [TESTING.md](../TESTING.md#integration-merge-gate) and `./tests/test-integration-merge.sh`.
> integration PR [#27](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/27).
> Do not merge PR #25/#26 separately — workflow commands and FEAT-001–003 are on
> `cursor/integration-981e`. Keep this note for the historical remote-branch table.

**Date:** 2026-07-15  
**Author:** Cloud agent session (branch evaluation)  
**Purpose:** Offline reference for reconciling remote branches, open PRs, and roadmap priorities.  
**Base ref:** `origin/main` as of 2026-07-15.

---

## Executive summary

Only **two branches** carry real unmerged work. The other **11** remote branches are stale (already merged via squash, or superseded). Recommended order:

1. Merge **PR #25** (workflow agent commands) — closes #23
2. Close **#7** (instruction-file parity — already on `main`)
3. Start **FEAT-001 T01** (shared `scripts/lib/` duplication inventory)
4. Keep **SPIKE-001 / PR #24** parked until canvas op **T06 go/no-go**
5. Delete stale remote branches (commands below)

---

## Delivery posture reminder

From [ROADMAP.md](../ROADMAP.md) and [milestone-1.md](../milestone-1.md):

| Stage | Status | Focus |
|-------|--------|-------|
| Make it work | mostly done | MVP adapters, capture, CI |
| **Make it right** | **active** | Refactors: `scripts/lib/`, command spec, extension manifest |
| Make it fast | horizon | Prompt optimization + ledger (FEAT-004/005, SPIKE-001/002) |

Default new framework work to **make it right** unless it is explicitly prompt/context optimization.

---

## Remote branch inventory

`merged=yes` means every commit on the branch is an ancestor of `main` (content landed, often via squash merge with a different SHA).

| Branch | Merged into main? | Ahead | Behind | Last commit | Verdict |
|--------|-------------------|-------|--------|-------------|---------|
| `cursor/workflow-agent-commands-981e` | no | 1 | 0 | 2026-07-15 | **Merge** — PR #25 |
| `cursor/spike-guide-ingest-agent-context-17f4` | no | 14 | 3 | 2026-07-11 | **Park** — PR #24, T06 pending |
| `cursor/sdlc-pointer-guarded-run-1978` | no | 1 | 15 | 2026-06-27 | **Delete** — landed as #20 |
| `cursor/add-usage-runbook-ba69` | no | 6 | 78 | 2026-06-06 | **Delete** — superseded |
| `chore/docgen-video-generation` | yes | 0 | 23 | 2026-06-20 | Delete remote |
| `cursor/add-claude-supported-framework-dbc7` | yes | 0 | 42 | 2026-06-14 | Delete remote |
| `cursor/context-loading-and-indexing` | yes | 0 | 40 | 2026-06-17 | Delete remote |
| `cursor/fowler-followup-fixes` | yes | 0 | 36 | 2026-06-17 | Delete remote |
| `cursor/fowler-spdd-alignment` | yes | 0 | 38 | 2026-06-17 | Delete remote |
| `cursor/framework-quality-and-prompt-metrics` | yes | 0 | 25 | 2026-06-19 | Delete remote |
| `cursor/sdlc-agents-progressive-disclosure` | yes | 0 | 33 | 2026-06-17 | Delete remote |
| `cursor/sdlc-agents-skill-loader` | yes | 0 | 29 | 2026-06-18 | Delete remote |
| `cursor/sdlc-workflow-state-1978` | yes | 0 | 7 | 2026-06-27 | Delete remote |
| `gh-pages` | — | — | — | deploy | **Leave** — GitHub Pages |

---

## Open pull requests

### PR #25 — Workflow agent commands (merge next)

- **Branch:** `cursor/workflow-agent-commands-981e`
- **URL:** https://github.com/jmjava/sdlc-spdd-orchestrator/pull/25
- **State:** Draft, mergeable, CI green
- **Closes:** #23
- **Stage:** make it right (chat wrappers for existing `sdlc.sh` CLI)
- **Scope:** +515 / −12 lines, 23 files — `/sdlc-claim`, `/sdlc-shelf`, `/sdlc-advance`, `/sdlc-next`, `/sdlc-team` across Cursor/Copilot/Claude

**Offline actions:**

```bash
git fetch origin
git checkout cursor/workflow-agent-commands-981e
# Review, then mark PR ready and merge on GitHub
```

### PR #24 — SPIKE-001 Guide/DICE context backend (do not merge yet)

- **Branch:** `cursor/spike-guide-ingest-agent-context-17f4`
- **URL:** https://github.com/jmjava/sdlc-spdd-orchestrator/pull/24
- **State:** Draft — explicit policy: no merge until **T06 go/no-go**
- **Stage:** make it fast (optimization spike, parked behind FEAT-004/005 per roadmap)
- **Scope:** +3,587 / −257 lines, 94 files, 14 commits
- **Paired:** https://github.com/jmjava/guide/pull/2 (`cursor/spike-spdd-dice-projection-17f4`)
- **Canvas:** `spdd/canvas/SPIKE-001-guide-rag-context-backend.md` — ops T01–T05, T07–T08 complete; **T06 remaining**

**Operator docs on spike branch:** `docs/guide-flow.md`, `docs/dice-projection-runbook.md`

**Offline actions (evaluation only):**

```bash
git fetch origin
git checkout cursor/spike-guide-ingest-agent-context-17f4
./scripts/guide/verify-spike-guide-setup.sh   # when Guide is running locally
# Complete T06 go/no-go in canvas before considering merge
```

---

## Open issues (no dedicated branch)

| Issue | Title | Recommendation |
|-------|-------|----------------|
| [#23](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/23) | Workflow agent commands | Close when PR #25 merges |
| [#7](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/7) | Instruction-file parity CI | **Close as done** — `validate-command-adapters.sh` + workflow paths already on `main` |
| [#22](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/22) | Demo video updates | Manual/chore — regen MP4s for workflow CLI |
| [#18](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/18) | Language-specific playbooks | Broader docs/examples — no branch yet |

---

## Milestone 1 — make it right backlog (no branch yet)

From [milestone-1.md](../milestone-1.md), execution order:

| Work ID | Canvas | Status | Next step |
|---------|--------|--------|-----------|
| **FEAT-001** | `spdd/canvas/FEAT-001-shared-script-library.md` | Draft — Needs Analysis | **T01:** inventory duplicated bash in `scripts/`, write `spdd/analysis/FEAT-001-shared-script-library-analysis.md` |
| FEAT-002 | command spec → generated adapters | Draft | After FEAT-001 |
| FEAT-003 | extension/hook manifest | Draft | After FEAT-002 |
| FEAT-004 | prompt-optimization ledger | Ready — **deferred** | make it fast; after refactors |
| FEAT-005 | canvas readiness indicators | Draft | make it fast; last |

**Suggested branch for next work:**

```bash
git checkout main && git pull
git checkout -b cursor/feat-001-script-lib-analysis-981e
# Claim work:
./scripts/sdlc.sh claim FEAT-001-shared-script-library
```

---

## Recommended priority (offline checklist)

- [ ] **Merge PR #25** — workflow commands, closes #23
- [ ] **Close #7** — instruction parity already shipped
- [ ] **Delete stale remotes** (see commands below)
- [ ] **Start FEAT-001 T01** — analysis artifact for `scripts/lib/` refactor
- [ ] **SPIKE-001 T06** — only if actively pursuing retrieval optimization now
- [ ] **#22** — regen demo videos when convenient
- [ ] **#18** — language playbooks when docs capacity allows

---

## Stale branch cleanup (copy-paste)

Safe to delete — content already on `main` or superseded:

```bash
git push origin --delete \
  chore/docgen-video-generation \
  cursor/add-claude-supported-framework-dbc7 \
  cursor/add-usage-runbook-ba69 \
  cursor/context-loading-and-indexing \
  cursor/fowler-followup-fixes \
  cursor/fowler-spdd-alignment \
  cursor/framework-quality-and-prompt-metrics \
  cursor/sdlc-agents-progressive-disclosure \
  cursor/sdlc-agents-skill-loader \
  cursor/sdlc-pointer-guarded-run-1978 \
  cursor/sdlc-workflow-state-1978
```

**Do not delete** until merged or explicitly abandoned:

- `cursor/workflow-agent-commands-981e` (merge first)
- `cursor/spike-guide-ingest-agent-context-17f4` (active spike)
- `gh-pages` (deployment)

---

## What not to do

- **Do not rebase `cursor/add-usage-runbook-ba69`** — 78 commits behind `main`, content long superseded by later PRs.
- **Do not merge PR #24 before SPIKE-001 T06** — contradicts canvas safeguards and README spike policy.
- **Do not start FEAT-004/005 yet** — roadmap defers make-it-fast work until make-it-right refactors land.

---

## Refresh this doc

Re-run branch stats after pulling `main`:

```bash
git fetch origin main
for b in $(git branch -r | grep -v HEAD | sed 's|origin/||'); do
  ahead=$(git rev-list --count origin/main..origin/$b 2>/dev/null || echo "?")
  behind=$(git rev-list --count origin/$b..origin/main 2>/dev/null || echo "?")
  merged=$(git merge-base --is-ancestor origin/$b origin/main 2>/dev/null && echo yes || echo no)
  echo "$b | merged=$merged | ahead=$ahead behind=$behind"
done
gh pr list --state open
gh issue list --state open
```

---

## Related artifacts

- Roadmap: [ROADMAP.md](../ROADMAP.md)
- Active milestone: [milestone-1.md](../milestone-1.md)
- Issue spec (workflow commands): [issues/ENHANCEMENT-agent-commands-for-workflow.md](../issues/ENHANCEMENT-agent-commands-for-workflow.md)
- SPIKE canvas: [spdd/canvas/SPIKE-001-guide-rag-context-backend.md](../spdd/canvas/SPIKE-001-guide-rag-context-backend.md)
- FEAT-001 canvas: [spdd/canvas/FEAT-001-shared-script-library.md](../spdd/canvas/FEAT-001-shared-script-library.md)
