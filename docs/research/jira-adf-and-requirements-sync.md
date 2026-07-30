# Research: Jira description format + requirements → Jira/REASONS sync

**Branch:** `feat/jira-requirements-jinja-sync`  
**Date:** 2026-07-30  
**Status:** Research complete — implementation not started on this commit  
**Scope note:** Guide spike stays separate.

## Verdict (what Jira actually expects)

| Jira product | REST API | `fields.description` type | Plain markdown / paste? |
|---|---|---|---|
| **Jira Cloud** | `/rest/api/3/issue` | **Atlassian Document Format (ADF) JSON object** | **No** — strings render badly or 400 |
| **Jira Server / Data Center** (typical) | `/rest/api/2/issue` | **Wiki markup string** | Markdown paste is still wrong; use wiki |
| Cloud API v2 | `/rest/api/2/issue` | Wiki markup string (legacy) | Prefer v3 + ADF on Cloud |

Official Cloud note (Create/Update issue):

> `description`, `environment`, and any `textarea` custom fields take **Atlassian Document Format**. Single-line `textfield` custom fields take a **string**.

Sources:

- [Jira Cloud REST v3 — Issues](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/)
- [ADF structure](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- ADF JSON Schema: <http://go.atlassian.com/adf-json-schema> →  
  `https://unpkg.com/@atlaskit/adf-schema@latest/dist/json-schema/v1/full.json`

---

## 1. Create issue — exact Cloud v3 payload

`POST {JIRA_BASE_URL}/rest/api/3/issue`

```http
Content-Type: application/json
Authorization: Basic {base64(email:api_token)}
Accept: application/json
```

```json
{
  "fields": {
    "project": { "key": "PROJ" },
    "summary": "Short title (string, max ~255)",
    "issuetype": { "name": "Story" },
    "labels": ["sdlc-spdd", "chore"],
    "components": [{ "name": "framework" }],
    "description": {
      "type": "doc",
      "version": 1,
      "content": [ /* ADF block nodes — see §3 */ ]
    }
  }
}
```

**Required field shapes that commonly bite integrations:**

| Field | Shape | Not |
|---|---|---|
| `project` | `{ "key": "PROJ" }` or `{ "id": "10000" }` | `"PROJ"` |
| `issuetype` | `{ "name": "Story" }` or `{ "id": "..." }` | `"Story"` alone |
| `summary` | string | ADF |
| `description` (v3) | ADF object | markdown string |
| `labels` | `["a","b"]` strings | objects |
| `components` | `[{ "name": "X" }, ...]` | `["X"]` |
| `priority` | `{ "name": "High" }` | `"High"` |

Create-screen fields vary by project/issue type. Discover with:

- `GET /rest/api/3/issue/createmeta?projectKeys=PROJ&expand=projects.issuetypes.fields` (deprecated but still used), or
- `GET /rest/api/3/issue/createmeta/{projectIdOrKey}/issuetypes/{issueTypeId}`

---

## 2. Update issue — exact Cloud v3 payload

`PUT {JIRA_BASE_URL}/rest/api/3/issue/{issueIdOrKey}`

```json
{
  "fields": {
    "summary": "Updated title",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [ /* full replacement ADF document */ ]
    }
  }
}
```

Notes:

- Updating `description` **replaces** the whole ADF document (not a patch of paragraphs).
- Same ADF rules as create.
- Our current engine (`IssueSyncService.push`) **creates only** and skips when a Key already exists — **update path is missing** and is required for “requirements are source of truth”.

---

## 3. ADF document contract (the format that matters)

### Root (required)

```json
{
  "type": "doc",
  "version": 1,
  "content": [ /* zero or more top-level block nodes */ ]
}
```

From schema `doc_node`:

- `type` enum: `"doc"`
- `version`: integer `1`
- `content`: array of top-level blocks

### Nodes we need for chore descriptions

| Node | Required fields | Purpose in our template |
|---|---|---|
| `heading` | `type`, `attrs.level` (1–6), optional `content` inlines | Section titles |
| `paragraph` | `type`, optional `content` inlines | Body prose |
| `bulletList` | `type`, `content` (≥1 `listItem`) | Acceptance criteria list |
| `listItem` | `type`, `content` (≥1 block; usually `paragraph`) | One AC line |
| `orderedList` | same pattern as bulletList | Numbered steps |
| `codeBlock` | `type`, optional `attrs.language`, `content` text nodes | Snippets |
| `rule` | `type` | Horizontal rule |
| `text` | `type`, `text` (**minLength 1** — empty text nodes are invalid) | Inline text |
| `hardBreak` | `type` | Soft line break inside a paragraph |

### Marks (inline formatting)

| Mark | Shape |
|---|---|
| bold | `{ "type": "strong" }` |
| italic | `{ "type": "em" }` |
| code | `{ "type": "code" }` |
| link | `{ "type": "link", "attrs": { "href": "https://..." } }` |

Example inline:

```json
{
  "type": "text",
  "text": "Work ID",
  "marks": [{ "type": "code" }]
}
```

### Optional richer AC: `taskList` / `taskItem`

Jira checklists can use ADF task nodes (schema requires `attrs.localId` + `state` `TODO`|`DONE`).  
For Given/When/Then we should **prefer `bulletList`** first (simpler, validates everywhere). Task lists can be a later enhancement.

### Golden fixture (validated)

This repo’s converter output for a chore-shaped body:

- Markdown source: [`engine/fixtures/jira/chore-given-when-then.md`](../../engine/fixtures/jira/chore-given-when-then.md)
- ADF JSON: [`engine/fixtures/jira/chore-given-when-then.adf.json`](../../engine/fixtures/jira/chore-given-when-then.adf.json)
- Wiki fallback: [`engine/fixtures/jira/chore-given-when-then.wiki.txt`](../../engine/fixtures/jira/chore-given-when-then.wiki.txt)

Validated against the official ADF JSON schema on 2026-07-30 (`jsonschema.validate` → pass).

Minimal Acceptance Criteria fragment (Given / When / Then):

```json
{
  "type": "heading",
  "attrs": { "level": 2 },
  "content": [{ "type": "text", "text": "Acceptance criteria" }]
}
```

```json
{
  "type": "bulletList",
  "content": [
    {
      "type": "listItem",
      "content": [
        {
          "type": "paragraph",
          "content": [
            { "type": "text", "text": "Given ", "marks": [{ "type": "strong" }] },
            { "type": "text", "text": "a chore requirement with Acceptance Criteria" }
          ]
        }
      ]
    },
    {
      "type": "listItem",
      "content": [
        {
          "type": "paragraph",
          "content": [
            { "type": "text", "text": "When ", "marks": [{ "type": "strong" }] },
            { "type": "text", "text": "the engine pushes or updates the linked Jira issue" }
          ]
        }
      ]
    },
    {
      "type": "listItem",
      "content": [
        {
          "type": "paragraph",
          "content": [
            { "type": "text", "text": "Then ", "marks": [{ "type": "strong" }] },
            { "type": "text", "text": "the description uses ADF headings and a Given/When/Then list" }
          ]
        }
      ]
    }
  ]
}
```

---

## 4. Server / DC wiki markup (API v2 fallback)

`POST/PUT /rest/api/2/issue` with `"description": "h2. Title\n\n* item\n"` (string).

Useful mappings:

| Markdown | Wiki |
|---|---|
| `## Title` | `h2. Title` |
| `**bold**` | `*bold*` |
| `*italic*` | `_italic_` |
| `` `code` `` | `{{code}}` |
| `- item` | `* item` |
| `1. item` | `# item` |
| `[label](url)` | `[label\|url]` |
| fenced code | `{code}...{code}` |

Our engine already implements `markdown_to_wiki()` for this path.

---

## 5. Why copy-paste from requirements looks horrible today

1. Jira Cloud’s editor is ADF-backed; pasted Markdown often becomes one flat paragraph.
2. Headings/lists/checkboxes are not inferred from `#` / `- [ ]` on paste the way GitHub does.
3. The API path must send ADF; the UI paste path is a different (lossy) pipeline.
4. Therefore: **never treat “paste the requirement file into Jira” as the integration** — render through the engine.

---

## 6. Source-of-truth model (target design)

```
requirements/**/*.md          ← ROOT source of truth (CHOREs included)
        │
        ├── Jinja templates (description + AC Given/When/Then)
        │         │
        │         ├──→ ADF (Cloud v3 create/update)   ⎫
        │         └──→ wiki (Server/DC v2 create/update) ⎬ only on explicit CLI
        │                                                   ⎭
        └── derived artifacts (also explicit CLI, not watchers)
                  ├── spdd/canvas/<WORK-ID>.md   (REASONS from requirement)
                  └── Jira issue fields           (create or update by Key)
```

### Execution model — explicit script only (no continuous sync)

**Hard constraint:** requirements are never pushed to Jira (or canvas) automatically on save, commit, PR, or agent turn.

| Surface | Allowed behavior |
|---|---|
| Engine / `sdlc.sh issues …` | **Only** place that may call Jira create/update (and only when the operator runs it, typically with `--apply`) |
| Slash command (Cursor/Copilot/Claude) | May **prepare** a paste-ready CLI invocation (dry-run preview + exact command line). **Must not** execute `push --apply`, open network calls to Jira, or write Keys back |
| CI / git hooks / file watchers | **Must not** sync requirements → Jira |
| Agents | Same as slash command: print the command; human (or explicit follow-up shell) runs it |

Example slash-command output (prepare only):

```text
Dry-run preview (no Jira API calls made by this command):
  ./scripts/sdlc.sh issues draft CHORE-010-example --system jira

To create or update in Jira, run explicitly:
  ./scripts/sdlc.sh issues push CHORE-010-example --system jira --apply
```

Default CLI posture stays fail-closed: `push` without `--apply` is dry-run only.

**Rules:**

1. Requirement markdown owns scope, acceptance criteria, and Jira draft fields (`## Jira`).
2. REASONS canvas is **derived from** the requirement when an explicit sync command is run (not a second inventing surface for AC).
3. Jira description is **rendered** from the requirement via Jinja → ADF/wiki — not hand-edited as source.
4. If Jira Key exists → explicit `push --apply` **UPDATEs** description/summary; if absent → **CREATEs** and writes Key back into the requirement.
5. No background, webhook, or “always sync” loop — operator-driven script execution only.

---

## 7. Gap vs current engine (as of main @ PR #46)

| Capability | Today | Needed |
|---|---|---|
| Markdown → ADF | Yes (`jira_format.markdown_to_adf`) | Keep; tighten G/W/T + Jinja |
| Markdown → wiki | Yes | Keep as fallback |
| Create issue | Yes (`issues push --apply`) | Keep |
| Update issue when Key exists | **No** (skips) | **Required** |
| Jinja templates for description/AC | **No** (hardcoded `build_jira_markdown`) | **Required** |
| Enforce Given/When/Then structure | Partial (subsection title only) | Parse + validate + render |
| CHORE-specific path under `requirements/` | Generic milestone parser | First-class CHORE template + sync |
| Requirements → REASONS canvas sync | Manual / separate | Explicit engine CLI op (not automatic) |
| Slash command prepares CLI only | N/A | New command: preview + print invocation; never `--apply` |
| Continuous / hook-based Jira sync | Absent (keep it that way) | **Do not add** |
| ADF schema validation in CI | No | Validate fixtures against official schema |

Existing code entry points:

- `engine/src/sdlc_engine/jira_format.py`
- `engine/src/sdlc_engine/issues.py`
- `engine/src/sdlc_engine/links.py` (`parse_milestone_requirement`, `## Jira` bullets/subsections)
- Chore template: `templates/requirements/requirement-chore-template.md`

---

## 8. Proposed Jinja surface (next implementation slice)

Suggested template files (not created yet):

```
engine/templates/jira/
  chore_description.md.j2      # markdown intermediate
  acceptance_gwt.md.j2         # Given/When/Then list fragment
```

Context built from the requirement:

```python
{
  "work_id": "CHORE-010-…",
  "summary": "...",
  "description": "...",
  "business_value": "...",
  "scope_in": [...],
  "scope_out": [...],
  "acceptance": [
    {"given": "...", "when": "...", "then": "..."},
  ],
  "requirement_path": "requirements/…",
  "labels": ["sdlc-spdd", "chore"],
  "issue_type": "Story",
}
```

Pipeline:

1. Parse requirement (front matter + `## Scope` + `## Acceptance Criteria` + `## Jira`).
2. Normalize AC into G/W/T triples (accept either triple bullets or one-line `Given … When … Then …`).
3. Render Jinja → markdown intermediate.
4. `markdown_to_adf` / `markdown_to_wiki`.
5. `POST` create or `PUT` update.
6. Write Key / URL / sync timestamp back to requirement; optionally refresh canvas R/Acceptance from the same context.

---

## 9. Recommended acceptance criteria authoring format (in requirements)

Prefer structured triples in the requirement (easy to parse, maps cleanly to ADF):

```markdown
## Acceptance Criteria

### AC-01
- Given a chore requirement with Acceptance Criteria
- When the engine updates the linked Jira issue
- Then the Jira description contains ADF headings and a Given/When/Then list

### AC-02
- Given an existing Jira Key on the requirement
- When acceptance criteria change in git
- Then `sdlc.sh issues push … --apply` updates the issue (does not create a duplicate)
```

One-line form also supported as a fallback:

```markdown
- Given X When Y Then Z
```

---

## 10. Auth / env (unchanged)

| Env | Purpose |
|---|---|
| `JIRA_BASE_URL` | e.g. `https://your-site.atlassian.net` |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | API token |
| `JIRA_PROJECT` | Project key |
| `JIRA_API_VERSION` | Force `2` or `3` |
| `JIRA_DESCRIPTION_FORMAT` | Force `adf` / `wiki` / `plain` |

Cloud default in engine today: v3 + ADF when host contains `atlassian.net`.

---

## 11. Next implementation Work ID (suggested)

`FEAT-013-jira-requirements-jinja-sync` (or CHORE if framed as chore-only first):

1. T01 — Freeze requirement CHORE schema + G/W/T parser tests  
2. T02 — Jinja templates + render pipeline  
3. T03 — Jira **update** path (`PUT /rest/api/3/issue/{key}`) on explicit `push --apply`  
4. T04 — Explicit requirements → REASONS canvas sync CLI (opt-in; never automatic)  
5. T05 — Slash command that **prints** draft/push invocation only (no network, no `--apply`)  
6. T06 — CI: validate ADF fixtures against official schema + docs

---

## 12. Quick reference — do / don’t

**Do**

- Send ADF JSON for Cloud v3 `description`
- Use `heading` + `bulletList` for AC
- Keep `text` nodes non-empty
- Treat requirements as root; regenerate Jira + canvas **via explicit CLI**
- Let slash commands prepare the exact `sdlc.sh issues …` line for the operator to run

**Don’t**

- POST markdown strings to `/rest/api/3/issue` `description`
- Rely on UI copy-paste from requirement files
- Hand-edit Jira as source of truth
- Invent acceptance criteria in the canvas that are not in the requirement
- Auto-sync on save/commit/PR/agent turn
- Let a slash command (or agent) execute `push --apply` / call Jira APIs itself
