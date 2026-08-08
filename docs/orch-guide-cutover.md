# Cutover: `jmjava/guide` → `jmjava/orch-guide`

Goal: stop depending on Cursor rules to avoid Embabel PRs. Put orchestrator Guide
work in a **standalone** repo that is **not** a GitHub fork of `embabel/guide`.

```text
embabel/guide          ← upstream product (read-only for us)
       ▲ fetch only
jmjava/guide           ← temporary fork; later hard-reset to embabel/guide
       │ one-time / manual copy
       ▼
jmjava/orch-guide      ← durable home for SPDD + git-incremental + dogfood env
```

## Why

- GitHub forks invite “contribute upstream” UX and accidental PRs.
- Rules/hooks are soft. A non-fork repo makes the wrong merge path structurally hard.
- After cutover, `jmjava/guide` can track Embabel cleanly again.

## Phase 1 — Create empty repo (human)

**Done (2026-08-08):** `jmjava/orch-guide` exists, empty, `isFork=false`.

## Phase 2 — Copy current fork tip (agent or human)

**Blocked on push credentials:** Cloud Agent `cursor[bot]` got HTTP 403 writing
to `jmjava/orch-guide`. Human must push once (or grant the environment write
access to that repo), then continue Phase 3.

From a clean `jmjava/guide` checkout on `main` (includes pin tip + SPDD):

```bash
./scripts/guide/push-orch-guide-bootstrap.sh
# or manually:
git remote add orch https://github.com/jmjava/orch-guide.git
git push orch main
git push orch --tags
# especially: sdlc-spdd-projection-v1, sdlc-spdd-projection-v2
```

Verify:

```bash
gh repo view jmjava/orch-guide --json url,defaultBranchRef
git ls-remote https://github.com/jmjava/orch-guide.git HEAD
```

## Phase 3 — Retarget orchestrator

Defaults today: `GUIDE_GIT_URL=https://github.com/jmjava/guide.git`.

After bootstrap:

| Setting | New value |
|---------|-----------|
| `GUIDE_GIT_URL` / console Git URL | `https://github.com/jmjava/orch-guide.git` |
| `GUIDE_GIT_REF` | `sdlc-spdd-projection-v2` (or `main`) |
| Dual-repo Cloud Agent env | swap Guide repo → `orch-guide` |
| Docs (`guide-flow`, dice runbook, etc.) | point at `jmjava/orch-guide` |

Inbound Embabel sync (optional, manual): fetch `embabel/guide` into **orch-guide**
when you want product updates — never open a PR back to Embabel.

## Phase 4 — Hard-reset `jmjava/guide` to Embabel (human, after Phase 3)

Only after dogfood uses `orch-guide`:

```bash
cd /path/to/jmjava/guide
git fetch upstream main
git checkout main
git reset --hard upstream/main
git push --force origin main   # destroys fork-only history on jmjava/guide
```

**Do not** force-push until orch-guide has the tags and tip you need.

Optional: delete SPDD-only branches on `jmjava/guide` or leave them orphaned.

## Manual sync later (orch-guide ↔ embabel)

```bash
cd orch-guide
git remote add embabel https://github.com/embabel/guide.git   # fetch only
git remote set-url --push embabel DISABLED
git fetch embabel main
git merge embabel/main   # or rebase policy of the day
# resolve; cut new pin tag if projection contract moved
```

## Non-goals

- No PR from orch-guide (or jmjava/guide) to `embabel/guide`
- No reliance on Cursor rules as the primary control (repo topology is the control)
