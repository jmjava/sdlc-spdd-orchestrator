# Contributing: command specs (FEAT-002)

Assistant commands for Cursor, Copilot, and Claude are generated from a single
canonical spec per command. This removes hand-maintained three-way drift.

**Shipped output:** `templates/cursor/`, `templates/copilot/prompts/`, `templates/claude/commands/`  
**Source of truth:** `spec/commands/*.spec.md`

---

## Edit workflow

1. Edit the spec for your command under `spec/commands/`.
2. Regenerate adapters:

   ```bash
   ./scripts/generate-command-adapters.sh
   ```

3. Verify:

   ```bash
   ./scripts/generate-command-adapters.sh --check
   ./scripts/validate-command-adapters.sh
   ./tests/test-command-specs.sh
   ./scripts/check-posture-boundary.sh
   ```

4. Commit **both** the spec and generated template files.

CI runs `generate-command-adapters.sh --check`, `validate-command-adapters.sh`, and
`tests/test-command-specs.sh` — stale adapters or missing semantic contracts fail the build.

### Generator overrides (tests / alternate trees)

```bash
./scripts/generate-command-adapters.sh --spec-dir /tmp/specs --template-root /tmp/tpl
# or: SDLC_SPEC_DIR=... SDLC_TEMPLATE_ROOT=...
```

Incomplete specs (missing `family`/`slug`, unknown family, missing title / Required
Behavior / Output) fail generation. New command files are created under
`--template-root` when absent (non-`--check` mode).

### Semantic contracts

`validate-command-adapters.sh` locks per-command anchors (Jira ask, readiness gates,
Outcome enum `improved` / `neutral` / `worse` / `unknown` on prompt-update and retro,
analysis index script, plan Needs Analysis, etc.). Keep those strings stable when
editing specs.

---

## Spec file layout

Each file is named `<family>-<slug>.spec.md`:

| Family | Example file | Generated command files |
|--------|--------------|-------------------------|
| `lifecycle` | `lifecycle-init.spec.md` | `sdlc-spdd-init` (all assistants) |
| `workflow` | `workflow-claim.spec.md` | `sdlc-claim` (all assistants) |

### Front matter (YAML)

```yaml
---
family: workflow
slug: claim
copilot_description: Short description for Copilot front matter
copilot_mode: agent
claude_description: Short description for Claude front matter
claude_argument_hint: <WORK-ID>   # workflow commands only
---
```

### Body blocks

Sections use block markers:

```markdown
---BLOCK:cursor:title---
/sdlc-claim
---END---

---BLOCK:shared:Required Behavior---
1. First step...
---END---
```

| Block prefix | When to use |
|--------------|-------------|
| `cursor:`, `copilot:`, `claude:` | Per-adapter title, preamble, or sections that differ |
| `shared:` | Identical `Required Behavior` or `Output` across all assistants |

Workflow commands typically share `Required Behavior` and `Output`. Lifecycle
commands like `init` may need per-adapter blocks when step wording differs.

---

## Bootstrap specs from templates

If templates were edited by hand (avoid — prefer spec edits), refresh specs:

```bash
./scripts/extract-command-specs.sh
./scripts/generate-command-adapters.sh --check
```

`--check` must pass before committing.

---

## Guardrails

- **No posture language** in generated adapters (`make it work/right/fast` stays in orchestrator planning docs only). Enforced by `check-posture-boundary.sh`.
- **No new commands** under FEAT-002 — change existing commands only unless a new Work ID adds them.
- Parity contract is encoded in `validate-command-adapters.sh` — read it when adding sections.

---

## See also

- [spec/commands/README.md](../spec/commands/README.md) — format reference
- [integration-branch.md](integration-branch.md) — manual test section F
- Canvas: [spdd/canvas/FEAT-002-command-spec-generation.md](../spdd/canvas/FEAT-002-command-spec-generation.md)
