# Bugfix Playbook

1. Run `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase plan` or create a new Work ID if one does not exist.
2. Capture reproduction steps in `requirements/` or an issue.
3. Plan with `/sdlc-spdd-plan` using the bugfix template.
4. Architect review with focus on regression risk.
5. Before each resumed session, run `./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only`.
6. Implement fix in one or more small coding operations.
7. Add regression test before closing.
8. Review, retro, and sync.
9. Persist bug-specific learning with `./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --pitfalls "<pitfall>" --next "<next command>"`.
