# Analysis Phase Scope Validation

Prevent scope creep in `/sdlc-spdd-analysis` by locking scope **before** generating
analysis sections.

Related: [Jira-compatible requirements format](jira-compatible-requirements-format.md),
[Context loading and scaling](context-loading-and-scaling.md),
[Roadmap, milestones, and session notes](roadmap-milestones-and-session-notes.md).

## Why scope lock-in matters

Without an upfront lock, analysis often absorbs neighboring layers (entities,
repositories, API handlers, integration points) that belong to other Work IDs.
That forces iterative “trim the analysis” cycles before architect/code can start.

Scope lock makes the analysis artifact a contract: architect and code phases
inherit the same boundaries.

## Checkpoint order

1. Read the requirement (and optional YAML frontmatter / `## Jira` / Related Work).
2. Write **Scope Lock** (In / NOT / Reference-only / Deferred targets).
3. Generate analysis **only** for locked-scope items.
4. Validate each section against the lock; move or delete out-of-scope material.
5. Accept analysis → proceed to `/sdlc-spdd-plan`.

## Scope Lock section format

```markdown
## Scope Lock

### In Scope for This Work
- Primary deliverable (schema, feature, integration, etc.)
- Direct dependencies only

### NOT in Scope (Deferred)
- Related work that belongs to separate Work IDs (name them)
- Integration points that belong to later phases

### Reference Materials (Context Only, Not Deliverables)
- Existing patterns and infrastructure that inform scope
- External systems (context reference only)
```

## Validation checklist (per analysis section)

For Domain Keywords, Code Areas, Existing/New Concepts, Strategic Direction,
and Acceptance-related risks:

- [ ] Does this address a locked **In Scope** item?
- [ ] If reference material, does it inform locked scope (not become a deliverable)?
- [ ] Should this move to **NOT in Scope (Deferred)** with a target Work ID?
- [ ] Remove if neither locked nor useful context

## Common scope-creep patterns

| Pattern | Symptom | Fix |
|---------|---------|-----|
| Layer bleed | Schema CHORE analysis includes JPA entities / repositories | Defer to API Work IDs |
| Integration early | Analysis designs callbacks or external sync for a DDL-only chore | Defer to later phase |
| Reference bloat | Long lists of pre-existing handlers “for context” | Keep only what informs locked deliverables |
| AC inflation | Acceptance criteria for deferred Work IDs | Move AC to deferred Work ID requirement |

## Analyst checklist

- [ ] Requirement IN/NOT scope read (or inferred and stated explicitly)
- [ ] Deferred Work IDs named where known
- [ ] Jira key copied into Metadata as read-only context (do not invent or rewrite keys)
- [ ] Scope Lock is the first major section after Metadata
- [ ] New Concepts / Strategic Direction contain no deferred deliverables
- [ ] Ready for `/sdlc-spdd-plan` without another scope-trim pass

## Stakeholder notes

- Scope lock is a **workflow gate** (analysis incomplete without the section), not a
  hard CI fail in this release.
- Deferred work stays **inside the analysis artifact** under NOT in Scope; promote
  to backlog/requirement stubs when ready.
- Plan phase benefits from the same boundaries via the analysis artifact; do not
  re-expand scope in the REASONS Canvas without updating the requirement first.
