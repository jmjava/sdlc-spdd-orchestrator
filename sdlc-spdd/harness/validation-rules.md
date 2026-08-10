# Validation Rules

REASONS Canvas files must include these sections:

- Metadata
- R - Requirements
- E - Entities
- A - Approach
- S - Structure
- O - Operations
- N - Norms
- S - Safeguards
- Review Checklist
- Sync Notes
- Final Status

Validate locally:

    ./scripts/validate-reasons-canvas.sh spdd/canvas/

Validate one file:

    ./scripts/validate-reasons-canvas.sh spdd/canvas/FEAT-001-example.md

## Optional readiness (FEAT-005)

Canvases may declare readiness as YAML frontmatter `readiness:` **or** Metadata
`- Readiness:`. Canonical values (aliases accepted):

| Canonical | Display |
|-----------|---------|
| `needs-analysis` | Needs Analysis |
| `needs-clarification` | Needs Clarification |
| `needs-redesign` | Needs Redesign |
| `ready-for-coding` | Ready For Coding |
| `blocked` | Blocked |

Missing readiness is OK. Unknown values warn only (do not fail section validation).
`/sdlc-spdd-code` should proceed only when readiness is Ready For Coding.

Operations should:

- Be small enough for one coding session
- Name affected files explicitly
- Include validation steps
