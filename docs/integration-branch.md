# Integration branch: `cursor/integration-981e`

> **Historical.** This branch was the mid-2026 make-it-right landing vehicle and is
> already on `main`. Prefer root [README](../README.md) and [TESTING.md](../TESTING.md)
> for current gates. Kept as a record of the checklist that was used.

Collect planned merges off `main`, run automated gates and a manual checklist, then land everything in one merge to `main`.

| | |
|--|--|
| **PR** | Landing via `cursor/merge-integration-to-main-0ab2` (supersedes draft [#27](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/27)) |
| **Tracking issue** | [#28 — Merge integration branch to main](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/28) |
| **Status** | FEAT-001–003 + archive (#29) + expanded regression gates |
| **Created** | 2026-07-15 |
| **Base** | `origin/main` @ `3b519cb` |

---

## Quick start

```bash
git fetch origin cursor/integration-981e
git checkout cursor/integration-981e

# Automated gates (expect all green)
./scripts/validate-command-adapters.sh
./scripts/generate-command-adapters.sh --check
./scripts/verify-script-lib-duplicates.sh
./tests/test-adapter-install.sh
./tests/test-scripts-lib.sh
./tests/test-index-spdd-analysis.sh
./tests/test-resolve-agent-context.sh
./tests/test-extension-manifest.sh
./tests/test-sdlc-workflow.sh
./tests/test-sdlc-pointer.sh
./tests/test-archive-work.sh
./tests/test-command-spec-generation.sh
./tests/test-integration-merge.sh
./scripts/check-posture-boundary.sh
```

Then work through [Manual test checklist](#manual-test-checklist) below.

---

## What is on this branch

### Merged from feature branches

| Source branch | Original PR | Contents |
|---------------|-------------|----------|
| `cursor/workflow-agent-commands-981e` | [#25](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/25) | `/sdlc-claim`, `/sdlc-shelf`, `/sdlc-advance`, `/sdlc-next`, `/sdlc-team` |
| `cursor/catch-up-branch-evaluation-981e` | [#26](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/26) | `docs/catch-up.md`, branch-evaluation session note |

Do **not** merge #25 or #26 separately — [#27](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/27) supersedes both. Those draft PRs were **closed** (not merged) on 2026-07-15.

### Built directly on integration (maintainability refactors)

| Work ID | Scope | Key paths |
|---------|-------|-----------|
| [FEAT-001](../spdd/canvas/FEAT-001-shared-script-library.md) | Shared `scripts/lib/`, consumer migration, duplicate check | `scripts/lib/`, `scripts/verify-script-lib-duplicates.sh` |
| [FEAT-002](../spdd/canvas/FEAT-002-command-spec-generation.md) | Canonical command specs → generated adapters | `spec/commands/`, `scripts/generate-command-adapters.sh` |
| [FEAT-003](../spdd/canvas/FEAT-003-extension-hook-manifest.md) | Extension manifest + resolver fallback | `templates/agent-context/extensions/manifest.md` (ships to targets), `resolve-agent-context.sh` |

Contributor guides: [Command specs](contributing-command-specs.md) · [Extensions manifest](contributing-extensions.md)

### Explicitly excluded (parked)

| Branch | PR | Reason |
|--------|-----|--------|
| `cursor/spike-guide-ingest-agent-context-17f4` | [#24](https://github.com/jmjava/sdlc-spdd-orchestrator/pull/24) | SPIKE-001 — wait for canvas **T06 go/no-go** (deferred optimization work) |

### Not on integration (stays open)

- [#22](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/22) — demo video regen (manual chore)
- [#18](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/18) — language playbooks

---

## Manual test checklist

Use a **throwaway target** so you do not disturb a real project.

Preferred install path (`setup-agent-prompts.sh` wraps `init-project.sh` and supports `--all`).
Create the target directory first — `init-project.sh` requires it to exist:

```bash
export TARGET=/tmp/sdlc-integration-test
rm -rf "${TARGET}"
mkdir -p "${TARGET}"
./scripts/setup-agent-prompts.sh --target "${TARGET}" --all
```

Equivalent direct init (no `--all` on `init-project.sh` — list assistants explicitly):

```bash
mkdir -p "${TARGET}"
./scripts/init-project.sh --target "${TARGET}" --cursor --copilot --claude
```

### A. Install and adapter parity

- [ ] Install completes without error
- [ ] Workflow commands exist in target: `.cursor/commands/sdlc-claim.md`, `.github/prompts/sdlc-claim.prompt.md`, `.claude/commands/sdlc-claim.md`
- [ ] Grounding files list workflow commands (`/sdlc-claim`, `/sdlc-team`, etc.)
- [ ] `./scripts/validate-command-adapters.sh --target "${TARGET}"` passes

### B. Workflow CLI (shell)

From `${TARGET}`:

```bash
cd "${TARGET}"

# Blank init has no Work IDs yet — create a stub canvas so list-work/claim are realistic:
mkdir -p spdd/canvas
printf '%s\n' '# DEMO-001-integration-smoke' '' '## Final Status' '' '- Status: In Progress' \
  > spdd/canvas/DEMO-001-integration-smoke.md

./scripts/sdlc-spdd/sdlc.sh list-work
./scripts/sdlc-spdd/sdlc.sh claim DEMO-001-integration-smoke
./scripts/sdlc-spdd/sdlc.sh next
./scripts/sdlc-spdd/sdlc.sh team
./scripts/sdlc-spdd/sdlc.sh shelf --reason "integration test"
./scripts/sdlc-spdd/sdlc.sh list-work
```

- [ ] `list-work` shows `DEMO-001-integration-smoke`
- [ ] `claim` sets `.sdlc/pointer` and appends a team-registry claim event
- [ ] `next` shows phase and recommended command
- [ ] `team` shows registry row
- [ ] `shelf` clears pointer and marks shelved

### C. Workflow commands (assistant — optional)

In Cursor / Copilot / Claude on the target project:

- [ ] `/sdlc-claim DEMO-001-integration-smoke` appears in command palette
- [ ] `/sdlc-next` returns orientation
- [ ] `/sdlc-team` shows registry
- [ ] `/sdlc-shelf` parks active work
- [ ] `/sdlc-advance` either advances or correctly refuses when gates are unmet (a minimal DEMO stub often refuses — that is expected)

### D. Upgrade path

From the **orchestrator repo** (`upgrade-project.sh` supports `--all`; it does **not** take `--force`):

```bash
./scripts/upgrade-project.sh --target "${TARGET}" --all
./scripts/validate-command-adapters.sh --target "${TARGET}"
```

- [ ] Upgrade installs missing workflow commands and extension manifest (create-if-missing)
- [ ] Parity validation still passes

### E. Shared script library (FEAT-001)

In the **orchestrator repo** (integration tip):

```bash
./scripts/verify-script-lib-duplicates.sh
./tests/test-scripts-lib.sh
```

In the **target** after install:

- [ ] `${TARGET}/scripts/sdlc-spdd/lib/common.sh` exists
- [ ] `${TARGET}/scripts/sdlc-spdd/resolve-agent-context.sh` runs without "missing shared library" errors

### F. Command specs (FEAT-002)

In the orchestrator repo:

```bash
./scripts/generate-command-adapters.sh --check   # adapters match specs
./scripts/validate-command-adapters.sh           # parity across assistants
```

- [ ] Editing a spec under `spec/commands/` and regenerating updates all three adapters (spot-check one command if desired)

See [contributing-command-specs.md](contributing-command-specs.md).

### G. Extension manifest (FEAT-003)

From the **orchestrator repo** (or `cd "${TARGET}"` and use `scripts/sdlc-spdd/`):

```bash
./scripts/resolve-agent-context.sh --target "${TARGET}" --phase code --format paths
```

- [ ] `${TARGET}/agent-context/extensions/manifest.md` exists
- [ ] `example-manifest-extension.md` appears in the resolved paths
- [ ] Renaming that `manifest.md` to `manifest.md.bak` still resolves extensions (convention fallback)

In the orchestrator repo:

```bash
./tests/test-extension-manifest.sh
```

See [contributing-extensions.md](contributing-extensions.md).

### H. Orchestrator regression spot-check

- [ ] `./scripts/sdlc.sh next` works in orchestrator repo root
- [ ] `./scripts/check-posture-boundary.sh` passes (no posture language in shipped templates)

---

## Merge to `main` (after sign-off)

When sections A–H pass:

```bash
git checkout main
git pull origin main
git merge cursor/integration-981e
# re-run Quick start gates on main
git push origin main
```

Then follow [issues/INTEGRATION-MERGE-28.md](../issues/INTEGRATION-MERGE-28.md) for issue/PR cleanup.

Delete superseded remotes after merge:

```bash
git push origin --delete cursor/workflow-agent-commands-981e
git push origin --delete cursor/catch-up-branch-evaluation-981e
```

---

## Next work on integration (optional before merge)

Per [milestone-1.md](../milestone-1.md), the remaining maintainability item is:

- **Readability pass** — consistent structure, naming, and examples across code and docs

FEAT-001–003 are complete on this branch. You can merge to `main` without the readability pass, or land it on integration first.

---

## Refresh integration from `main`

If `main` moves while you test:

```bash
git fetch origin main
git checkout cursor/integration-981e
git merge origin/main
# resolve conflicts, re-run Quick start gates
git push origin cursor/integration-981e
```

---

## Related docs

| Doc | Use when |
|-----|----------|
| [catch-up.md](catch-up.md) | Branch inventory and offline reconciliation |
| [contributing-command-specs.md](contributing-command-specs.md) | Editing assistant commands via specs |
| [contributing-extensions.md](contributing-extensions.md) | Adding phase extensions and manifest rows |
| [INTEGRATION-MERGE-28.md](../issues/INTEGRATION-MERGE-28.md) | Post-merge issue/PR close list |
