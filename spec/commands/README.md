# Command specs (FEAT-002)

Canonical source for SDLC-SPDD assistant command adapters. Edit specs here,
then regenerate templates:

```bash
./scripts/generate-command-adapters.sh
./scripts/validate-command-adapters.sh
```

CI runs `./scripts/generate-command-adapters.sh --check` so checked-in adapters
cannot drift from specs.

## Layout

Each `*.spec.md` file contains:

- YAML front matter (`family`, `slug`, per-adapter descriptions)
- Block sections (`---BLOCK:cursor:title---` … `---END---`)
- Shared `Required Behavior` / `Output` sections when all adapters match
- Per-adapter sections (`cursor:`, `copilot:`, `claude:`) when they differ

## Bootstrap from existing templates

To refresh specs from current adapter files (e.g. after a one-off hand edit):

```bash
./scripts/extract-command-specs.sh
./scripts/generate-command-adapters.sh --check
```

The generator must pass `--check` before committing spec or template changes.

**Contributor guide:** [docs/contributing-command-specs.md](../../docs/contributing-command-specs.md)
