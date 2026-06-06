# PR Review Playbook

1. Run `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase review`.
2. Read the linked REASONS Canvas and `agent-context/sessions/current-session.md`.
3. Compare PR diff to Requirements, Operations, Norms, and Safeguards.
4. Check tests and dependency changes.
5. Use review result values: Approved, Approved With Notes, Changes Requested, Blocked.
6. Recommend `/sdlc-spdd-prompt-update` when the intended behavior changed.
7. Recommend `/sdlc-spdd-sync` if accepted implementation drifted from the canvas.
8. Persist review memory with `./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase review --summary "<review summary>" --validation "<checks>" --next "<next command>"`.
