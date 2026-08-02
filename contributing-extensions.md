# Contributing: extension manifest (FEAT-003)

Target projects extend SDLC-SPDD behavior through phase extensions and skills
without modifying framework command packs. The **manifest** documents those
extension points explicitly.

**Shipped template:** `templates/agent-context/extensions/manifest.md`  
**Resolver:** `scripts/resolve-agent-context.sh` (installed as `scripts/sdlc-spdd/resolve-agent-context.sh`)

---

## How resolution works

```
resolve-agent-context.sh --phase <phase>
        │
        ├─ manifest.md present and parseable?
        │     yes → load folders from Phase extensions table
        │     no  → convention fallback (_all-agents + phase-agent folder)
        │
        └─ collect *.md from matched folders (+ skills via #SkillName)
```

Convention fallback preserves backward compatibility for projects without a manifest.

---

## Manifest format

`agent-context/extensions/manifest.md` uses markdown tables:

### Phase extensions

| Folder | Phases | Description |
|--------|--------|-------------|
| `_all-agents` | * | Loaded for every phase |
| `coding-agent` | code, api-test | Implementation extensions |

- **Folder** — subdirectory under `agent-context/extensions/` (backticks optional)
- **Phases** — `*` for all phases, or comma-separated SDLC phase names (`init`, `analysis`, `plan`, …)
- **Description** — contributor documentation only (not read by resolver)

### Skills and hooks

The Skills table documents known skill files; discovery still works via
`extensions/skills/` and `#SkillName` in prompts.

The Hooks table is **declarative only** in this MVP — no automatic execution.

---

## Adding an extension

1. Create a focused `.md` file under the right folder:

   ```
   agent-context/extensions/coding-agent/my-team-style.md
   ```

2. If you add a **new folder** or change phase mapping, update `manifest.md`.

3. Verify resolution:

   ```bash
   ./scripts/resolve-agent-context.sh --target . --phase code --format paths
   # or in a target project:
   ./scripts/sdlc-spdd/resolve-agent-context.sh --target . --phase code --format paths
   ```

4. Run tests in the orchestrator repo:

   ```bash
   ./tests/test-extension-manifest.sh
   ./tests/test-resolve-agent-context.sh
   ```

---

## Example shipped with the framework

`templates/agent-context/extensions/_all-agents/example-manifest-extension.md` demonstrates a minimal `_all-agents` rule. `init-project.sh` copies it to new targets; remove or replace in real projects.

---

## How install / upgrade behaves

`init-project.sh` and `upgrade-project.sh` copy:

- `manifest.md`
- `README.md`
- `example-manifest-extension.md`
- `skills/*.md`

Upgrade uses create-if-missing for these files — it does **not** overwrite an
existing `manifest.md`, example extension, or skill file in the target. To pick
up framework updates to those files, copy them manually or delete the target
file before upgrading.

See [framework-upgrade.md](framework-upgrade.md).

---

## See also

- [templates/agent-context/extensions/README.md](../templates/agent-context/extensions/README.md) — layout overview
- [context-loading-and-scaling.md](context-loading-and-scaling.md) — progressive disclosure model
- [integration-branch.md](integration-branch.md) — manual test section G
- Canvas: [spdd/canvas/FEAT-003-extension-hook-manifest.md](../spdd/canvas/FEAT-003-extension-hook-manifest.md)
