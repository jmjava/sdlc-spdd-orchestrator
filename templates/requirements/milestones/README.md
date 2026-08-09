# Milestone-Derived Requirements

This folder holds requirement stubs created from milestone checklist items.

## Layout

**Preferred (new projects):**

```text
requirements/milestones/
  README.md
  milestone-1/
    _milestone.yml
    MILESTONE-1.md
    FEAT-001-….md
  milestone-2/
    _milestone.yml
    MILESTONE-2.md
    CHORE-….md
```

**Legacy (still supported):**

- Root `milestone-N.md` at the project root
- Flat stubs: `requirements/milestones/<WORK-ID>.md`

Scripts prefer subdirectory definitions when both root and subdirectory exist
(with a warning). See [jira-compatible-requirements-format.md](../../../docs/jira-compatible-requirements-format.md#existing-root-milestones)
and [jira-compatible-requirements-format.md](../../../docs/jira-compatible-requirements-format.md).

## Purpose

When you run `create-work-from-milestone.sh`, each unchecked milestone item becomes:

- a Work ID
- a requirement file here (flat or under `milestone-N/`)
- a draft REASONS Canvas under `spdd/canvas/<WORK-ID>.md`
- a **Linked Work** row in the source milestone definition

Use these files in analysis/plan prompts:

    /sdlc-spdd-analysis @requirements/milestones/milestone-1/<WORK-ID>.md
    /sdlc-spdd-plan @requirements/milestones/milestone-1/<WORK-ID>.md @ROADMAP.md @requirements/milestones/milestone-1/MILESTONE-1.md

## Jira issue drafts

Each milestone requirement file stores Jira syntax:

- **Before create** — fill Summary, Description, acceptance criteria, labels, components
- **After create** — set `- Key: ABC-123` and commit
- **On claim** — `./scripts/sdlc.sh claim <WORK-ID>` (or `SDLC_ENGINE=python`) auto-reads the Key into the team registry
  `jira:` note token (disable with `SDLC_TEAM_AUTO_JIRA=0`)

Engine helpers (v2):

```bash
SDLC_ENGINE=python ./scripts/sdlc.sh issues draft <WORK-ID> --system jira
SDLC_ENGINE=python ./scripts/sdlc.sh issues draft <WORK-ID> --system jira --format adf  # Cloud payload preview
SDLC_ENGINE=python ./scripts/sdlc.sh issues push <WORK-ID> --system jira          # dry-run
SDLC_ENGINE=python ./scripts/sdlc.sh issues push <WORK-ID> --system jira --apply  # ADF on Jira Cloud
SDLC_ENGINE=python ./scripts/sdlc.sh sync-links --repair
```

Jira Cloud needs ADF for descriptions — the engine converts this markdown
automatically on push (see [jira-runbook.md](../../../docs/jira-runbook.md)).

See [jira-runbook.md](../../../docs/jira-runbook.md) and [engine/README.md](../../../engine/README.md).

## GitHub issue drafts

Optional `## GitHub` section for teams that track delivery in GitHub Issues:

```markdown
## GitHub

- Number: TBD
- Title: …
- Labels: feature
- URL:
```

After create, set `Number` / `URL`. Claim auto-links `github:#N` (disable with `SDLC_TEAM_AUTO_GITHUB=0`).

```bash
SDLC_ENGINE=python ./scripts/sdlc.sh issues push <WORK-ID> --system github --apply   # uses gh CLI
```

<!-- reconcile: retained subdirectory guidance from integration -->
- Optional YAML frontmatter (`jira_key`, epic, status, blocks/depends_on)
- `## Jira` section for copy-paste create flows
- **After create** — set `- Key: ABC-123` (and matching `jira_key`) and commit
- **On claim** — `./scripts/sdlc.sh claim <WORK-ID>` auto-reads the Key into the team registry

Validate:

    ./sdlc-spdd/scripts/validate-requirements-format.sh --target .

See [jira-runbook.md](../../../docs/jira-runbook.md).

## Relationship to other planning artifacts

| Artifact | Role |
|----------|------|
| `milestone-*.md` or `…/milestone-N/MILESTONE-N.md` | Goal, scope checklist, linked Work IDs |
| `requirements/milestones/` | Per-item requirement stubs + Jira draft syntax |
| `session-notes/` | Daily agent-session narrative |
| `ROADMAP.md` | Milestone progress and current focus |

Ad-hoc requirements (not from a milestone) live directly under `requirements/` instead.
Use the same frontmatter + `## Jira` section there when the work will be tracked in Jira.
