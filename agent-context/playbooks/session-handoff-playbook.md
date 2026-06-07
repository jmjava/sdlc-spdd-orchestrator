# Session Handoff Playbook

Use this playbook whenever work crosses agent sessions.

## Start of Session

1. Check canvas sync state (does not create a session brief):

       ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --check-only

2. If drift exists, reconcile and create a session brief in one step. **Default:** canonical `spdd/canvas/<WORK-ID>.md` is authoritative:

       ./scripts/sdlc-spdd/resync-agent-session.sh --target . --work-id <WORK-ID> --from-canvas --force --phase <phase>

   Use `--from-feature` only when the feature workspace canvas was intentionally edited.

3. If no drift, create a session brief:

       ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase>

4. Paste the **Resume Prompt** from `agent-context/sessions/current-session.md`.

   Optional explicit milestone:

       ./scripts/sdlc-spdd/start-agent-session.sh --target . --work-id <WORK-ID> --phase <phase> --milestone milestone-1.md

   See `docs/sdlc-spdd/session-prompt-standard.md` for the full prompt contract.

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
      --milestone milestone-1.md \
      --roadmap-note "<roadmap-level progress, if applicable>" \
      --next "<next command>"

`--milestone` is optional when the Work ID is already listed in a `milestone-*.md` file (auto-detected).

Confirm memory was written to:

- `agent-context/memory/session-history.md`
- `agent-context/features/<WORK-ID>/progress-log.md`
- relevant memory files for decisions, pitfalls, and patterns
