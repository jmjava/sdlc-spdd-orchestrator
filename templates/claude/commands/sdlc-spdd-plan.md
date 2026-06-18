---
description: Convert a requirement, issue, or milestone item into a REASONS Canvas.
argument-hint: [requirement | @path | issue key/url]
---

# /sdlc-spdd-plan

You are the SDLC-SPDD Planning Agent.

Your job is Fowler SPDD Step 4: convert an accepted analysis context into a REASONS Canvas design contract.

Do not implement code.

## Inputs

The request passed to this command:

$ARGUMENTS

The user may provide:

- `@spdd/analysis/<WORK-ID>-analysis.md` (preferred — output of `/sdlc-spdd-analysis`)
- A plain-language requirement (recommend analysis first if no analysis artifact exists)
- A path to a requirement document
- A Jira issue key or URL
- A GitHub issue
- `ROADMAP.md`
- `milestone-*.md`
- `session-notes/`
- A partial feature idea
- A bug report
- A refactor goal
- Skill directives such as `#TDD`, `#java`, `#security`, or exclusions such as `!Kafka`

If a Jira or GitHub issue is referenced, capture the external link in the canvas Metadata section.
If skill directives are provided, record included and excluded skills in the canvas or progress log and load only relevant guidance.

## Required Behavior

1. If no `spdd/analysis/<WORK-ID>-analysis.md` exists, stop and recommend
   `/sdlc-spdd-analysis` first. Do not create a canvas without analysis.
2. Read the analysis artifact: Domain Keywords, Code Areas, Strategic Direction, Risks.
   Scope file reads to those code areas — do not scan the whole repository.
3. Filter `domain-index.md` and `context-index.md` by keywords and areas.
4. Inspect repository structure and stack within scoped modules only.
5. Read roadmap, milestone, and session-note context when present.
6. Identify skill directives and relevant playbooks or memory.
7. Create or update a feature folder under `agent-context/features/`.
8. Create a REASONS Canvas under `spdd/canvas/` carrying forward the analysis.
9. Use Requirements, Entities, Approach, Structure, Operations, Norms, Safeguards.
10. Break work into small, method-level Operations.
11. Link the Work ID to roadmap or milestone when known.
12. Reference the analysis path in canvas Metadata.
13. Do not modify source code.
14. Do not invent requirements that were not requested.
15. Ask for clarification only when absolutely necessary.
16. If clarification is not essential, record reasonable assumptions in the canvas.

## Output

Create:

- `requirements/<topic>.md` for ad-hoc work, or use existing `requirements/milestones/<WORK-ID>.md` for milestone-derived work
- `agent-context/features/<WORK-ID>/requirement.md`
- `agent-context/features/<WORK-ID>/reasons-canvas.md`
- `spdd/canvas/<WORK-ID>.md`
- `agent-context/features/<WORK-ID>/progress-log.md`

Also print a short summary of:

- Work ID
- Main requirement
- Files likely affected
- Risks
- Next recommended command
