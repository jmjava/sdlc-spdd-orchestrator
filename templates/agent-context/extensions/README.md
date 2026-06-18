# Agent Extensions

Project-local rules and skills that extend SDLC-SPDD behavior **without modifying**
framework command packs or grounding files.

Inspired by [SDLC Agents extensions](https://github.com/dsilahcilar/sdlc-agents).
Follow **progressive disclosure**: agents load extension files only when the
active phase or a `#SkillName` directive calls for them — not on every request.

Resolve what to load with:

    ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase <phase>
    ./scripts/sdlc-spdd/resolve-agent-context.sh --text "Implement #TDD #java !Kafka"

## Layout

    agent-context/extensions/
    ├── _all-agents/        Rules for every phase (security policy, team norms)
    ├── initializer-agent/  /sdlc-spdd-init
    ├── planning-agent/     analysis, plan, prompt-update
    ├── architect-agent/    /sdlc-spdd-architect
    ├── coding-agent/       code, api-test
    ├── codereview-agent/   /sdlc-spdd-review
    ├── retro-agent/        /sdlc-spdd-retro
    ├── curator-agent/      /sdlc-spdd-sync
    ├── skills/             Custom skills referenced via #SkillName
    └── README.md           This file

## How to use

1. Drop a `.md` file into `_all-agents/` or the phase agent folder above.
2. Add skill files under `skills/` (for example `skills/TDD.md`, `skills/java.md`).
3. Reference skills in prompts: `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01 #TDD`
4. Exclude irrelevant skills: `#java !Kafka`
5. Run `resolve-agent-context.sh` or read the **Resolved Context** section in
   `agent-context/sessions/current-session.md` after `start-agent-session.sh`.

## Progressive disclosure rules

- Do **not** expect agents to read every file in this folder automatically.
- `start-agent-session.sh` resolves phase extensions into the session brief.
- Name skills in the prompt when you need them beyond the phase defaults.
- Keep each extension focused — one concern per file.

See `docs/sdlc-spdd/sdlc-agents-and-the-framework.md` after install.
