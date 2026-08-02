# Catch-up guide

> **Historical (2026-07).** The integration merge to `main` already landed. For current
> product state see the root [README](../README.md), [ops-console.md](ops-console.md),
> and [guide-flow.md](guide-flow.md). SPIKE-001 is on `main` (T06 provisional go);
> do not treat “parked until T06” rows below as current policy.

Use this when reconciling **old** branch notes from mid-July offline sessions.

**Then-current path (superseded):** land work through **`cursor/merge-integration-to-main-0ab2`**.

```bash
git fetch origin cursor/merge-integration-to-main-0ab2
git checkout cursor/merge-integration-to-main-0ab2
```

Full gates, manual checklist, and merge procedure: [integration-branch.md](integration-branch.md)  
Tracking: [Issue #28](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/28) · supersedes draft [PR #27](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/27)

---

## What changed since the branch evaluation (2026-07-15)

The [2026-07-15 catch-up session note](../session-notes/2026-07-15-catch-up-branch-evaluation.md) recommended merging PR #25 next and starting FEAT-001 analysis. **That advice is superseded:**

| Then (evaluation note) | Now (integration tip) |
|------------------------|-------------------------|
| Merge PR #25 workflow commands | Absorbed into integration — merge via PR #27 |
| Start FEAT-001 T01 inventory | FEAT-001 T01–T04 **complete** on integration |
| FEAT-002 / FEAT-003 not started | **Complete** on integration |
| Catch-up branch as doc source | Catch-up docs merged into integration |

---

## Integration branch contents (summary)

| Area | Status |
|------|--------|
| Workflow commands (`/sdlc-claim`, etc.) | On integration |
| Catch-up docs | On integration |
| FEAT-001 `scripts/lib/` | Complete |
| FEAT-002 command spec generation | Complete |
| FEAT-003 extension manifest | Complete |
| Readability pass (milestone-1 #4) | Not started |
| SPIKE-001 / PR #24 | **Excluded** — parked until T06 go/no-go |

---

## Branch inventory (quick reference)

**Active — use integration:**

- `cursor/integration-981e` — all planned merges + maintainability refactors

**Superseded — delete after PR #27 merges:**

- `cursor/workflow-agent-commands-981e` (was PR #25)
- `cursor/catch-up-branch-evaluation-981e` (was PR #26)

**Parked — do not merge into integration:**

- `cursor/spike-guide-ingest-agent-context-17f4` (PR #24, SPIKE-001)

**Stale — safe to delete** (content already on `main`; see evaluation note for full table):

- `cursor/sdlc-pointer-guarded-run-1978`, `cursor/add-usage-runbook-ba69`, and other `merged=yes` remotes listed in the session note

For the full remote branch table and `gh` cleanup commands, see [session-notes/2026-07-15-catch-up-branch-evaluation.md](../session-notes/2026-07-15-catch-up-branch-evaluation.md).

---

## Open issues (at integration time)

| Issue | Action |
|-------|--------|
| [#23](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/23) | **Close when #27 merges** — workflow commands on integration |
| [#7](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/7) | **Close anytime** — parity already on `main` (not blocked on #27) |
| [#28](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/28) | **Close when #27 merges** — integration merged |
| [#22](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/22), [#18](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/18) | **Stay open** — not on integration |

Commands: [issues/INTEGRATION-MERGE-28.md](../issues/INTEGRATION-MERGE-28.md)

---

## After integration merges to `main`

1. Delete superseded remote branches (commands in [integration-branch.md](integration-branch.md)).
2. Add a new dated session note if branch inventory drifts again.
3. Continue milestone-1 with the **readability pass** or start deferred optimization work (FEAT-004+) per [milestone-1.md](../milestone-1.md).
