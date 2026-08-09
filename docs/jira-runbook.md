# Jira Runbook

Create and sync Jira issues from SDLC-SPDD work. **You start in a requirement
markdown file** (`requirements/milestones/<WORK-ID>.md`); the engine builds a
structured description from `## Jira` subsections and **translates markdown → ADF**
on `issues push`. Jira Cloud REST v3 requires ADF — you do not author ADF by
hand to create an issue.

For rich formatting beyond markdown (panels, GWT blocks, complex tables), use the
optional **ADF Viewer** path (`adf/<KEY>.adf.json`) after the issue exists. For
the full tracker-to-branch workflow (GitHub Issues too), see
[Issue sync and branching](issue-sync-and-branching.md).

## Source of truth

| Artifact | Source of truth for |
|----------|---------------------|
| Requirement doc (`## Jira` markdown) | Summary, description outline, acceptance criteria, labels — **primary input to Jira** |
| Engine (`build_jira_markdown` → `markdown_to_adf`) | ADF payload sent on `issues push` |
| `adf/<JIRA-KEY>.adf.json` | Optional checked-in copy for **rich** descriptions edited in the viewer |
| Jira issue | Delivery status, ownership, sprint/board workflow |
| REASONS Canvas | Design contract, scope, operations, norms, safeguards |
| Lessons ledger | Implementation history (`session`, `decision`, `pitfall`, `pattern` records) |
| Review / sync artifacts | Fit vs canvas; reconciled drift |

Edit the requirement doc first. Jira receives **explicit pushes** — never
automatic sync. The `adf/` file is not read by `issues push`; it is only used
by `upload-adf` / `download-adf` and the viewer.

## The Jira process (overview)

```text
1. Create issue manually in Jira UI  →  copy key (PROJ-123)

requirements/milestones/<WORK-ID>.md
  ## Jira  (markdown: Summary, Description, Acceptance criteria)
         │
         ├─ ops console Jira tab / issues link ─→ record Key locally
         │     (requirement + canvas + registry)
         │
         ├─ issues draft ─────────────────────→ preview markdown + ADF
         │
         ├─ issues pull --apply ──────────────→ Jira → requirement doc
         │
         └─ issues push --apply ──────────────→ requirement md → Jira
                (update only when Key linked)     (markdown → ADF)

Optional — rich description refinement (after Key exists):

adf/<JIRA-KEY>.adf.json  + ADF Viewer  →  upload-adf / download-adf
```

### Standard path (manual Jira → link → sync)

1. **Scaffold the requirement** — `## Jira` with Summary, Description,
   Acceptance criteria. See
   [Jira-compatible requirements format](jira-compatible-requirements-format.md).
2. **Create the issue in Jira UI** — copy the key (`PROJ-123`). The engine does
   not create Jira issues from the ops console (too many org-specific flows).
3. **Link the key locally** — ops console **Jira** tab (*Preview link* → *Apply link*)
   or CLI `issues link <WORK-ID> PROJ-123 --apply`. Updates `## Jira Key`, frontmatter
   `jira_key`, canvas **Source Issue**, and registry note.
4. **Preview payload** — `issues draft` shows markdown composed from `## Jira` and
   the ADF JSON that would be sent on push.
5. **Sync with server** — *Pull* refreshes the requirement doc from Jira; *Push*
   updates the existing issue from local markdown (never creates).

### Optional path (rich ADF in the viewer)

Use when markdown is not enough (panels, status lozenges, GWT scenarios, tables
the markdown converter flattens):

1. After push, `issues download-adf <KEY> --apply` to materialize
   `adf/<KEY>.adf.json` from Jira (or seed from the draft ADF preview).
2. Edit in the [ADF Viewer](adf-viewer.md); commit the JSON file.
3. `issues upload-adf <KEY> --apply` pushes **only** the description body.

To refresh the requirement doc from Jira (description as markdown), use
`issues pull --apply` — not `download-adf`.

## One-time setup

```bash
export JIRA_BASE_URL="https://yourorg.atlassian.net"
export JIRA_EMAIL="you@yourorg.com"
export JIRA_API_TOKEN="…"
export JIRA_PROJECT="PROJ"

python3 -m pip install -e './engine[dev,viewer]'   # viewer optional
```

Optional overrides:

| Variable | Default | Purpose |
|----------|---------|---------|
| `JIRA_API_VERSION` | `3` on `*.atlassian.net` | REST API version |
| `JIRA_DESCRIPTION_FORMAT` | `adf` on v3 | Payload shape for push/upload |
| `JIRA_DESCRIPTION_FALLBACK` | `1` | Retry wiki/v2 ↔ ADF/v3 once on 400 |

For Jira Server/DC with wiki markup:

```bash
export JIRA_API_VERSION=2
export JIRA_DESCRIPTION_FORMAT=wiki
```

Validate requirement docs locally (no API):

```bash
./scripts/validate-requirements-format.sh --target .
```

## Create a new Jira issue

### 0. Draft in the requirement doc

Path:

```text
requirements/milestones/<WORK-ID>.md
# or
requirements/milestones/milestone-N/<WORK-ID>.md
```

Use YAML frontmatter (`jira_key`, …) and a `## Jira` section. Scaffolded by
`create-work-from-milestone.sh`. Leave `- Key: TBD` until push returns a real key.

The engine reads these subsections under `## Jira` (see
`links.py` / `build_jira_markdown`):

| Subsection | Maps to Jira description |
|------------|--------------------------|
| `- Summary:` (bullet) | Issue title (not body) |
| `### Description` | Description body |
| `### Acceptance criteria` | Acceptance criteria |
| `### Business value` | Business value (if present) |
| Scope from `## Scope` | Can feed scope-in/out when mirrored under Jira |

Example:

```markdown
## Jira

- Key: TBD
- Issue type: Story
- Summary: Order status API
- Labels: sdlc-spdd, feature

### Description

Customers need to check order status without contacting support.

### Acceptance criteria

- [ ] GET /orders/{id}/status returns current status
- [ ] Unknown order returns 404
```

After `./scripts/sdlc.sh claim <WORK-ID>`, registry events can carry
`jira:ABC-123` in the note when the key is set.

### 1. Triage (optional agent prompt)

```text
Triage this request before creating Jira. Identify type, proposed summary,
business value, acceptance criteria, risks, and Work ID prefix (FEAT, BUG, …):

<paste request>
```

### 2. Create in Jira UI and link locally

Create the issue in Jira (any workflow your team uses). Copy the key.

**Ops console** (`./scripts/sdlc.sh console` → **Jira** tab):

1. Enter Work ID and Jira key.
2. *Preview link* → *Apply link* (writes local files only).

**CLI:**

```bash
sdlc-engine issues link FEAT-001-order-status-api PROJ-123 --apply
sdlc-engine sync-links --repair
```

### 3. Preview and sync with server

```bash
# Preview markdown + ADF (no network write)
sdlc-engine issues draft FEAT-001-order-status-api --system jira
sdlc-engine issues draft FEAT-001-order-status-api --system jira --format adf

# Pull Jira fields into the requirement doc
sdlc-engine issues pull FEAT-001-order-status-api --system jira --apply

# Push local ## Jira markdown → Jira (update existing issue only)
sdlc-engine issues push FEAT-001-order-status-api --system jira --apply
```

Wrapper: `./scripts/sdlc.sh issues …` in installed projects.

### 3. Optional — refine description in ADF

Skip this step if the pushed markdown description is sufficient.

**Materialize a local ADF file** (after the issue exists):

```bash
sdlc-engine issues download-adf PROJ-123 --apply
# writes adf/PROJ-123.adf.json from Jira
```

**Edit in the viewer** (ops console ADF tab, or):

```bash
./scripts/sdlc.sh viewer --port 5050
# http://127.0.0.1:5050/
```

1. Open `adf/PROJ-123.adf.json`.
2. Edit in WYSIWYG or raw JSON; autosave → commit like source code.
3. *Prepare upload* → review dry-run → *Apply upload* pushes description to Jira.

CLI equivalent:

```bash
sdlc-engine issues upload-adf PROJ-123 \
  --file adf/PROJ-123.adf.json --apply
```

Keep project-specific ticket ADF in the **consuming repo**, not the orchestrator
framework repo (seed files like `ORCH-demo.adf.json` are examples only).

### 4. Create the Work ID and canvas

If work started from Jira, map keys explicitly:

```text
Jira: PROJ-123
Work ID: FEAT-123-order-status-api
```

The Work ID need not mirror the Jira key, but canvas **Metadata** must link both.

Then:

```text
/sdlc-spdd-plan Jira PROJ-123: <summary>. Link the canvas to the Jira URL and
use the requirement doc ## Jira acceptance criteria as Requirements input.
```

Gate first: `./scripts/sdlc.sh gate plan --work-id <WORK-ID>`.

### 5. Branch naming

```bash
git switch -c feature/PROJ-123-FEAT-123-order-status-api
```

See [Issue sync and branching §3](issue-sync-and-branching.md#3-branch-naming-convention).

## Create Jira children from a canvas

When one issue is too large for the board:

```text
For FEAT-123, read @spdd/canvas/FEAT-123-order-status-api.md. Draft Jira child
issues from Operations. Each child: summary, description outline in the parent's
requirement template style, acceptance criteria, parent PROJ-123, operation ID.
```

| Canvas operation | Jira issue type |
|------------------|-----------------|
| User-visible slice | Story or Task |
| Defect | Bug |
| Investigation | Spike |
| Test-only | Test or Task |
| Documentation | Task |

Add a requirement stub (or `## Jira` block) per child and push with `issues push`.
Use the optional ADF path only when a child needs rich formatting.

## Keep Jira in sync

Synchronize at lifecycle checkpoints. Prefer **structured pulls** over pasted
comments when fields changed on the tracker.

| SDLC-SPDD checkpoint | Jira update |
|----------------------|-------------|
| Canvas created | Comment or traceability in requirement Description; link canvas path |
| Architect ready | Transition; readiness decision in comment |
| Operation done | Comment with operation ID; ledger capture staged |
| Review complete | Comment with review outcome |
| Requirement changed | Update requirement doc `## Jira`, then `issues push --apply` |
| Blocked | Blocked status + missing decision |
| Retro / sync | Final validation; move toward Done |

**Refresh requirement doc from Jira** (summary, status, labels, description as markdown):

```bash
sdlc-engine issues pull FEAT-123-order-status-api --system jira --apply
```

**Refresh optional ADF file** (after someone edited description in Jira UI and
you maintain `adf/<KEY>.adf.json`):

```bash
sdlc-engine issues download-adf PROJ-123 --apply
```

**Push requirement changes** (markdown → ADF, full issue fields):

```bash
sdlc-engine issues push FEAT-123-order-status-api --system jira --apply
```

**Push viewer-only description changes** (ADF file → Jira description only):

```bash
sdlc-engine issues upload-adf PROJ-123 --apply
```

### Daily sync prompt

```text
For <WORK-ID>, read the canvas, review/sync artifacts if present, and run
`sdlc-engine context retrieve --work-id <WORK-ID> --kind session` for recent
progress. Draft a Jira comment for PROJ-123 with: current phase, completed
operations, validation, review result, blockers, next step.
```

### Status mapping

| SDLC-SPDD state | Typical Jira status |
|-----------------|---------------------|
| Request triaged | Backlog |
| Canvas created | To Do |
| Ready For Coding | In Progress |
| Operation implemented | In Progress |
| Review approved | In Review / Ready for QA |
| Review changes requested | In Progress |
| Blocked | Blocked |
| Retro / sync complete | Done |

Adapt names to your team's workflow.

## Requirement changes vs refactoring

### Behavior or requirement change

Update the requirement doc **`## Jira` markdown first**, push to Jira, then update
the canvas, then code. If you also maintain an ADF file, download or edit it
after the doc change — or rely on push alone for plain descriptions.

```text
Jira PROJ-123 changed acceptance criteria: <new rule>. Update
requirements/milestones/<WORK-ID>.md ## Jira, run issues push --apply, then
@sdlc/canvas/<WORK-ID>.md. Do not change source code yet.
```

After canvas review:

```text
/sdlc-spdd-code @spdd/canvas/<WORK-ID>.md operation <operation-id>
```

### Refactoring (no behavior change)

Refactor, review, sync canvas; Jira comment only:

```text
Refactor completed with no intended behavior change. Canvas synchronized after
review. Validation: <tests>.
```

## Jira sync checklist

Before coding:

- [ ] Requirement doc exists with `## Jira` Description and Acceptance criteria
- [ ] `gate analysis` / `gate plan` pass
- [ ] Jira key in requirement doc and canvas Metadata (or explicit decision not to use Jira)
- [ ] `issues push --apply` run at least once (description sent as ADF from markdown)
- [ ] Acceptance criteria match between requirement and canvas Requirements
- [ ] Branch name includes tracker key + Work ID
- [ ] (Optional) `adf/<KEY>.adf.json` committed and uploaded if using viewer workflow

During coding:

- [ ] Progress captured via `./scripts/sdlc.sh capture` (staged; accept at retro)
- [ ] Jira comments generated from canvas/ledger/review — not from chat memory alone
- [ ] Requirement changes: update `## Jira` markdown, `issues push --apply`, then canvas

Before done:

- [ ] Jira status matches review outcome
- [ ] Final comment includes validation and follow-ups
- [ ] Sync log records drift; retro lessons accepted to ledger

## Related

- [Ops console](ops-console.md) — **Jira** tab: link key + pull/push sync
- [Issue sync and branching](issue-sync-and-branching.md) — push/pull, branches, GitHub Issues, viewer sync panels
- [ADF Viewer](adf-viewer.md) — optional rich ADF editing after markdown push
- [Jira-compatible requirements format](jira-compatible-requirements-format.md) — `## Jira` schema
- [Research: Jira ADF + requirements sync](research/jira-adf-and-requirements-sync.md) — Cloud ADF payloads
