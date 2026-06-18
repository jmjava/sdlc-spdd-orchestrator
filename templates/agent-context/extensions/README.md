# Agent Extensions

Project-local rules and skills that extend SDLC-SPDD behavior **without modifying**
framework command packs or grounding files.

Inspired by [SDLC Agents extensions](https://github.com/dsilahcilar/sdlc-agents).
Follow **progressive disclosure**: agents should load extension files only when the
active phase or a `#SkillName` directive calls for them — not on every request.

## Layout

    agent-context/extensions/
    ├── _all-agents/     Rules applied to every phase (security policy, team norms)
    ├── skills/          Custom skills referenced via #SkillName in prompts
    └── README.md        This file

## How to use

1. Add a `.md` file under `_all-agents/` for rules that apply to all phases.
2. Add skill files under `skills/` (for example `skills/TDD.md`, `skills/java.md`).
3. Reference skills in prompts: `/sdlc-spdd-code @spdd/canvas/WORK-ID.md operation T01 #TDD`
4. Exclude irrelevant skills: `#java !Kafka`
5. Record selected skills in the canvas Metadata or feature progress log when relevant.

## Progressive disclosure rules

- Do **not** expect agents to read every file in this folder automatically.
- Name the skill or extension in the prompt when you need it.
- Keep each extension focused — one concern per file.
- Prefer linking from `agent-context/playbooks/` for framework-owned workflows;
  use `extensions/` for project-specific overrides.

See `docs/sdlc-spdd/sdlc-agents-and-the-framework.md` after install.
