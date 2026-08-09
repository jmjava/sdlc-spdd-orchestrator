# Contributing: harness skills

Target projects extend SDLC-SPDD behavior through **skills** — focused markdown
files under `harness/skills/` that agents load on demand via `#SkillName`.

**Shipped templates:** `templates/agent-context/harness/skills/*.md`  
**Resolver:** `scripts/resolve-agent-context.sh` (installed as `sdlc-spdd/scripts/resolve-agent-context.sh`)

There is no extension manifest in a storage v3 install. Phase-scoped static
context comes from `harness/phase-index.md`; on-demand skills come from
`harness/skills/`.

---

## How resolution works

```
resolve-agent-context.sh --phase <phase>
        │
        ├─ harness/phase-index.md → static files for the phase
        ├─ phase-matching skills under harness/skills/ (from skill frontmatter)
        │
        └─ #SkillName in prompt text → load harness/skills/<SkillName>.md
```

List discoverable skills:

```bash
./scripts/resolve-agent-context.sh --target . --list-skills
# or in a target project:
./sdlc-spdd/scripts/resolve-agent-context.sh --target . --list-skills
```

Verify resolution for a phase or prompt:

```bash
./scripts/resolve-agent-context.sh --target . --phase code --format paths
./scripts/resolve-agent-context.sh --target . --text "Implement auth #TDD #java-feature"
```

`!SkillName` excludes a skill even if also requested with `#`.

---

## Skill file format

Place one skill per file:

```
sdlc-spdd/harness/skills/my-team-style.md
```

Use YAML frontmatter for metadata the resolver reads:

```markdown
---
name: MyTeamStyle
phases: code, api-test
description: Team coding conventions for service layers
---

# My team style

…
```

- **name** — defaults to the filename stem; used for `#SkillName` lookup
- **phases** — comma-separated SDLC phases, or `*` for all phases
- **description** — contributor documentation (shown by `--list-skills`)

Shipped examples: `#TDD`, `#java-feature`, `#bugfix`, `#refactor`, `#pr-review`, `#security`.

---

## Adding a skill

1. Create a focused `.md` file under `harness/skills/`.

2. If the skill should load automatically for certain phases, set `phases:` in
   frontmatter. Otherwise agents request it explicitly with `#SkillName`.

3. Verify resolution (commands above).

4. Run tests in the orchestrator repo:

   ```bash
   ./tests/test-resolve-agent-context.sh
   ```

---

## How install / upgrade behaves

`init-project.sh` and `upgrade-project.sh` copy template skills with
**create-if-missing** semantics — they do **not** overwrite an existing skill
file in the target. To pick up framework updates to a shipped skill, copy the
template manually or delete the target file before upgrading.

See [framework-upgrade.md](framework-upgrade.md).

---

## See also

- [context-loading-and-scaling.md](context-loading-and-scaling.md) — progressive disclosure model
- [SDLC Agents and the framework](sdlc-agents-and-the-framework.md) — `#SkillName` mapping
- [TESTING.md](../TESTING.md) — command and resolver test stack
