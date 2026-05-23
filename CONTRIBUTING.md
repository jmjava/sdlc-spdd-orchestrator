# Contributing

Thanks for contributing to SDLC-SPDD Orchestrator.

## Principles

- Keep Markdown and shell scripts as the primary artifacts for MVP
- Preserve safe defaults: no overwrite without `--force`
- Keep no-code agent phases free of application code changes
- Implement one canvas operation per coding session
- Match existing conventions in the repository

## Development Setup

1. Clone the repository
2. Make changes in focused PRs
3. Run canvas validation when touching canvas files:

       ./scripts/validate-reasons-canvas.sh examples/spring-boot-order-api/spdd/canvas/FEAT-001-order-status-api.md

4. Test scripts with `--dry-run` when adding file-writing behavior

## Pull Requests

- Link related REASONS Canvas or work ID when applicable
- Fill in the PR template checklist
- Keep scope minimal and reviewable

## Attribution

When borrowing ideas from SDLC Agents or OpenSPDD, preserve attribution and avoid vendoring large upstream portions.
