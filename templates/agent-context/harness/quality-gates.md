# Quality Gates

Every feature should pass these gates before being considered complete:

- [ ] Requirement documented
- [ ] REASONS Canvas exists
- [ ] Architect review completed (advisory)
- [ ] Operations are task-sized (advisory)
- [ ] Code changes map to approved operations
- [ ] Tests added or updated (advisory)
- [ ] Review completed
- [ ] Safeguards checked
- [ ] Retro completed
- [ ] Canvas synced with implementation (advisory)

Human reminders (not `GATE_LABELS`): canvas readiness is Ready For Coding before `/sdlc-spdd-code`; flag review if coding proceeded without Ready For Coding; update the prompt-optimization ledger when prompts/canvas changed (FEAT-004).

Instruction vs constraint: Norms instruct; `/sdlc-spdd-code` exit is constrained by named Validation (or documented test/lint/typecheck), a twice-same-error stop, and `git diff --name-only` within the T## `Files:` plus tests.
