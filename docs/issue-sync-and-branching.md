# Issue Sync and Branching — Tracker-to-Branch Runbook

How a Work ID travels from a requirement doc to a Jira issue or GitHub Issue,
into a branch name, through commits and PRs, and back — for **both** trackers.
Commands only; no theory.

Contents:

1. [Source of truth: the requirement doc](#1-source-of-truth-the-requirement-doc)
2. [Creating and syncing issues](#2-creating-and-syncing-issues)
3. [Branch naming convention](#3-branch-naming-convention)
4. [Commit and PR linkage](#4-commit-and-pr-linkage)
5. [The ADF Viewer editor](#5-the-adf-viewer-editor)
6. [Quick reference](#6-quick-reference)

---

## 1. Source of truth: the requirement doc

Every unit of work has a Work ID (`FEAT-001-order-status-api`, `BUG-003-null-discount`)
and one requirement doc: `requirements/milestones/<WORK-ID>.md` (or
`requirements/milestones/milestone-N/<WORK-ID>.md` in the subdirectory layout).
That file — not the tracker — is where the external issue link is recorded.

Two places carry the link, and they must agree:

- **YAML frontmatter** — machine-readable keys (`jira_key`, `jira_type`, `jira_status`).
- **`## Jira` / `## GitHub` sections** — bullet fields the engine reads and writes
  (`links.py parse_milestone_requirement`; Jira keys must match `^[A-Z][A-Z0-9]+-\d+$`,
  anything else — `TBD`, `TODO`, `N/A` — is treated as "not created yet").

Real-shaped example (`requirements/milestones/FEAT-001-order-status-api.md`):

```markdown
---
work_id: "FEAT-001-order-status-api"
jira_key: "PROJ-123"
jira_type: "Story"
jira_status: "In Progress"
---

# Requirement: FEAT-001-order-status-api

## Summary

Expose a read-only order status endpoint for the storefront.

## Jira

- Key: PROJ-123
- Summary: Order status API
- Issue type: Story
- Labels: sdlc-spdd, feature
- Components: api

### Description

Customers need to check order status without contacting support.

### Acceptance criteria

- [ ] GET /orders/{id}/status returns current status
- [ ] Unknown order returns 404

## GitHub

- Number: 42
- Title: Order status API
- Labels: feature
- URL: https://github.com/acme/storefront/issues/42
```

Before the issue exists, leave `Key: TBD` / `Number: TBD`. For **Jira**, create the
issue manually in the Jira UI, then link the key locally (ops console **Jira** tab or
`issues link … --apply`). For **GitHub**, `issues push --apply` can create the issue
and writes the number back into the doc.

## 2. Creating and syncing issues

All three subcommands run through the engine CLI (`sdlc-engine issues …`, or the
project wrapper `./scripts/sdlc.sh issues …`). Everything is **dry-run by default**;
nothing touches the tracker or your files without `--apply`.

### Credentials and config

Jira (REST API, no extra CLI needed):

```bash
export JIRA_BASE_URL="https://yourorg.atlassian.net"   # or JIRA_URL
export JIRA_EMAIL="you@yourorg.com"                    # basic auth (Cloud)
export JIRA_API_TOKEN="…"                              # API token or PAT
export JIRA_PROJECT="PROJ"                             # required for issue create
# Optional overrides:
#   JIRA_API_VERSION=2|3         (default: 3 on *.atlassian.net)
#   JIRA_AUTH_MODE=basic|bearer  (bearer for Server/DC PATs)
#   JIRA_DESCRIPTION_FORMAT=adf|wiki|plain (default: raw ADF on API v3)
```

GitHub (via the `gh` CLI — install it and authenticate once):

```bash
gh auth login
# Optional: override the repo (default comes from `git remote get-url origin`):
export SDLC_GITHUB_REPO="acme/storefront"   # or GH_REPO
```

### `issues draft` — preview, writes nothing

```bash
sdlc-engine issues draft FEAT-001-order-status-api --system jira
sdlc-engine issues draft FEAT-001-order-status-api --system github
```

Reads the requirement doc (`## Jira` / `## GitHub` sections) and prints the
title, labels, and body that *would* be sent. For Jira, the engine composes a
markdown description from `## Jira` subsections (`build_jira_markdown`), then
converts it to ADF for Cloud v3. Use `--format adf|md|wiki` to preview the exact
payload. No file or network writes. **`issues push` does not read `adf/*.json`
files** — those are only for `upload-adf` / `download-adf`.

### `issues link` — record a manually created Jira key (local only)

```bash
sdlc-engine issues link FEAT-001-order-status-api PROJ-123 --apply
sdlc-engine sync-links --repair
```

Updates `## Jira Key`, frontmatter `jira_key`, canvas **Source Issue**, and registry
note. Does **not** call Jira create APIs. Preferred path for Jira; see
[Jira runbook](jira-runbook.md).

### `issues push` — update tracker from requirement doc

```bash
# Dry-run first (prints the payload and the action):
sdlc-engine issues push FEAT-001-order-status-api --system jira
# Then for real:
sdlc-engine issues push FEAT-001-order-status-api --system jira --apply
sdlc-engine issues push FEAT-001-order-status-api --system github --apply
```

What it does per system:

- **Jira** — PUTs to update when `Key:` holds a real key (markdown → ADF). Can POST
  to create via CLI when `Key:` is still `TBD`, but the ops console and recommended
  flow use manual Jira create + `issues link` first. Repairs local links on apply.
- **GitHub** — runs `gh issue create --title … --body …` in the project root.
  The issue number and URL from gh's output are **written back** into the
  `## GitHub` section (`- Number: 42`, `- URL: …`). If `Number:` is already
  set, push is a no-op (it never creates duplicates).

After an apply, commit the requirement doc — the written-back key/number is the
durable link.

### `issues pull` — refresh the doc from the tracker

```bash
sdlc-engine issues pull FEAT-001-order-status-api --system jira            # report only
sdlc-engine issues pull FEAT-001-order-status-api --system jira --apply    # write fields back
sdlc-engine issues pull FEAT-001-order-status-api --system github --apply
```

Reads the issue identified by the doc's `Key:` / `Number:` and reports summary,
status, labels, and (Jira) the description rendered as markdown. With `--apply`
it updates the doc's bullets (Summary/Title, Labels, URL, Description) and
repairs local links. It errors clearly when no key/number is recorded yet.

## 3. Branch naming convention

One branch per Work ID, named:

```text
<type>/<TRACKER-KEY>-<WORK-ID>
```

- `<type>` — `feature`, `fix`, `chore`, `spike`, … (mirrors the Work ID prefix).
- `<TRACKER-KEY>` — Jira key (`PROJ-123`) or GitHub number (`gh-42`).
- `<WORK-ID>` — always present, so every branch links back to its SPDD
  artifacts (`spdd/canvas/<WORK-ID>.md`, `spdd/analysis/…`, requirement doc).

Exact commands:

```bash
# Jira-tracked feature:
git switch -c feature/PROJ-123-FEAT-001-order-status-api

# GitHub-tracked bug fix:
git switch -c fix/gh-42-BUG-003-null-discount
```

Why the tracker key goes in the name:

- **Jira** — any branch (and PR) whose name contains `PROJ-123` shows up
  automatically in the issue's **Development panel** (requires the
  GitHub-for-Jira / DVCS connector).
- **GitHub** — branches created for an issue appear under **Development /
  linked branches** on the issue; PRs from a branch containing the issue
  reference plus a `Fixes #42` line close the issue on merge.

The Work ID goes in the name so that agents and scripts can resolve the active
canvas and phase artifacts from the branch alone — the tracker key alone is not
enough for SPDD tooling.

## 4. Commit and PR linkage

Prefix commit subjects with the tracker key and Work ID:

```bash
git commit -m "PROJ-123 FEAT-001: add order status endpoint"
git commit -m "gh-42 BUG-003: guard null discount in cart total"
```

- **Jira** — a commit message containing `PROJ-123` links the commit to the
  issue. Jira **smart commits** go further:
  `PROJ-123 #comment handled empty cart #time 1h #transition In Review`.
- **GitHub** — use closing keywords in the PR description or a commit:
  `Fixes #42` / `Closes #42` (or `Fixes acme/storefront#42` cross-repo). The
  issue closes when the PR merges.

PR titles follow the same shape: `PROJ-123 FEAT-001: order status API`.

`/sdlc-spdd-commit-message` drafts this for you: it collects the change set via
the engine (`./scripts/sdlc.sh commit-message`), resolves the active Work ID
from the session pointer when you omit it, and produces a paste-ready subject +
body with the Work ID included (e.g. `FEAT-001: …` or a `Work-ID:` trailer).
It never runs `git commit` — you review, then commit with the branch/prefix
conventions above.

## 5. The ADF Viewer editor (optional)

**Primary Jira path:** create the issue in Jira UI → link key locally (ops console
**Jira** tab or `issues link`) → edit `requirements/milestones/<WORK-ID>.md`
(`## Jira` markdown) → `issues pull` / `issues push --apply` (update only in console).

The ADF Viewer (`http://127.0.0.1:5050`, started from the ops console or
`python3 -m sdlc_engine.viewer --root . --port 5050`) is for **optional**
rich-description work after an issue exists: WYSIWYG + raw-ADF editing of
`adf/<KEY>.adf.json`. Its sync boxes talk to both trackers. Everything is
prepare-first (dry-run); apply is always an explicit second click.

**Jira sync** (issue key field, e.g. `PROJ-123`):

- *Prepare/Apply upload* — local ADF file → Jira issue description (raw ADF on
  Cloud v3, optional wiki shim). CLI equivalent:
  `sdlc-engine issues upload-adf --issue-key PROJ-123 --file adf/PROJ-123.adf.json --apply`
- *Prepare/Apply download* — Jira description → local ADF file, with a diff
  report first. CLI: `sdlc-engine issues download-adf PROJ-123 --apply`

**GitHub Issue sync** ("GitHub Issue #" field — accepts `123`, `#123`, or
`owner/repo#123`; repo defaults from `git remote get-url origin`, overridable
in the optional repository field or `SDLC_GITHUB_REPO`):

- *Prepare/Apply pull* — fetches the issue body with `gh issue view`, converts
  markdown → ADF, and (on apply) overwrites the open document so you can edit
  it in the WYSIWYG.
- *Prepare/Apply push* — converts the open document ADF → markdown and (on
  apply) writes it back with `gh issue edit --body`.

> **Round-trip caveat:** GitHub stores issue bodies as markdown, not ADF.
> ADF → markdown → ADF is lossy for exotic formatting — panels, statuses,
> colored text, and complex tables may flatten to plain markdown equivalents.
> The viewer shows this note next to the GitHub controls. For Jira the
> round-trip is lossless (raw ADF both ways).

## 6. Quick reference

```bash
# 0. One-time setup
gh auth login                       # GitHub
export JIRA_BASE_URL=… JIRA_EMAIL=… JIRA_API_TOKEN=… JIRA_PROJECT=…   # Jira

# 1. Create Jira issue in UI; link key locally
sdlc-engine issues link FEAT-001-order-status-api PROJ-123 --apply
#    (or ops console → Jira tab → Apply link)

# 2. Optional: draft/push/pull to sync requirement ↔ Jira
sdlc-engine issues draft FEAT-001-order-status-api --system jira
sdlc-engine issues push  FEAT-001-order-status-api --system jira --apply   # update only when Key set

# 2. Branch with tracker key + Work ID
git switch -c feature/PROJ-123-FEAT-001-order-status-api

# 3. Work; commit with linked prefixes (draft via /sdlc-spdd-commit-message)
git commit -m "PROJ-123 FEAT-001: add order status endpoint"

# 4. PR with the same prefix; `Fixes #42` for GitHub-tracked work

# 5. Keep doc and tracker aligned
sdlc-engine issues pull FEAT-001-order-status-api --system jira --apply
```
