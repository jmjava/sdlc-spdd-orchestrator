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

Instruction vs constraint: Norms and named Validation instruct. `/sdlc-spdd-code` exit is constrained by the leftover #6 verify receipt (command, exit, pass/fail) recorded when `sdlc.sh capture`/`complete` executes `--verify-command`. A claimed exit is not a receipt. `gate_check` stays enter-phase. `tests_updated` stays advisory. The code command still refuses completion when validation did not run, a failure is not tied to its Norm or Safeguard, the same failure repeats, or `git diff --name-only` leaves the operation `Files:` and explicitly allowed tests. Extra paths are incomplete work, not a warning. Those checks stay in the command. They do not enter `gate_check`.
