# Session Handoff Playbook

Use this playbook whenever work crosses agent sessions.

## Start of Session

1. Check canvas sync state:

       ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

2. If drift exists, choose the authoritative source:

       ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --from-canvas --force --phase <phase>

   or:

       ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --from-feature --force --phase <phase>

3. Create a session brief:

       ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

4. Ask the assistant:

       For <WORK-ID>, read @agent-context/sessions/current-session.md and continue with the recommended SDLC-SPDD command.

## During Session

- Keep the active Work ID in every prompt.
- Load only phase-relevant context.
- Use the REASONS Canvas as the SPDD contract.
- Implement one approved Operation at a time.
- Use `/sdlc-spdd-prompt-update` before behavior changes.
- Use `/sdlc-spdd-sync` after accepted implementation drift.

## End of Session

Capture durable memory:

    ./scripts/sdlc-spdd/capture-session-memory.sh \
      --target . \
      --work-id <WORK-ID> \
      --phase <phase> \
      --summary "<completed work>" \
      --validation "<tests or checks>" \
      --decisions "<decisions, if any>" \
      --pitfalls "<pitfalls, if any>" \
      --patterns "<patterns, if any>" \
      --next "<next command>"

Confirm memory was written to:

- `agent-context/memory/session-history.md`
- `agent-context/features/<WORK-ID>/progress-log.md`
- relevant memory files for decisions, pitfalls, and patterns
