## Summary

<!-- What changed and why -->

## REASONS Canvas

- Work ID:
- Canvas path: `spdd/canvas/<WORK-ID>.md`

## Checklist

- [ ] Canvas updated or synced
- [ ] One operation per coding session respected
- [ ] Tests added or updated
- [ ] Review completed
- [ ] Safeguards respected
- [ ] CI gates pass (`validate-command-adapters`, `test-adapter-install`, `validate-canvas`, `validate-diagrams`)
- [ ] If command/prompt adapter files changed, ran adapter parity validation

## Manual Smoke (Required for high-risk changes)

Check this section when your PR changes command templates, prompt files, session scripts, install/upgrade logic, or docs that define invocation flow.

- [ ] Manual chat smoke executed in Cursor, Copilot, **or** Claude Code (`plan -> architect -> code -> review`)
- [ ] `verify-agent-command-effects.sh` passed for `plan`, `architect`, `code`, `review`, and `capture`
- [ ] Milestone/session-notes sync verified for tested Work ID (and roadmap when expected)

## Test Plan

<!-- How was this validated? -->
