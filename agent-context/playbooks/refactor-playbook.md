# Refactor Playbook

1. Start or resume with `./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase architect`.
2. State behavior-preservation explicitly in the canvas.
3. Break refactor into incremental operations.
4. Before each resumed session, run `./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only`.
5. Run tests after each operation.
6. Review for scope creep into feature work.
7. Sync canvas if structure changed materially.
8. Persist memory with `./scripts/sdlc-spdd/capture-session-memory.sh --target . --work-id <WORK-ID> --phase <phase> --summary "<summary>" --validation "<tests>" --patterns "<pattern>" --next "<next command>"`.
