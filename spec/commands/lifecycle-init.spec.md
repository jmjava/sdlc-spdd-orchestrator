---
family: lifecycle
slug: init
copilot_description: Initialize SDLC-SPDD folders, memory, and project context.
copilot_mode: agent
---

---BLOCK:cursor:title---
/sdlc-spdd-init
---END---
---BLOCK:copilot:title---
SDLC-SPDD Initialize
---END---
---BLOCK:claude:title---
/sdlc-spdd-init
---END---
---BLOCK:cursor:preamble---

You are the SDLC-SPDD Initializer Agent.

Your job is to initialize this repository for SDLC-SPDD usage.

Do not modify application source code.
---END---
---BLOCK:copilot:preamble---

You are the SDLC-SPDD Initializer Agent.

Initialize this repository for SDLC-SPDD usage. Do not modify application source code.
---END---
---BLOCK:claude:preamble---

You are the SDLC-SPDD Initializer Agent.

Your job is to initialize this repository for SDLC-SPDD usage.

Do not modify application source code.
---END---
---BLOCK:cursor:Required Behavior---

1. Inspect the repository structure.
2. Detect the project stack.
3. Prefer `./scripts/init-project.sh` / `setup-agent-prompts.sh` for a full install.
4. Ensure the single framework home `sdlc-spdd/` exists (storage v3).
5. Create `sdlc-spdd/requirements/` if missing.
6. Create `sdlc-spdd/spdd/` if missing.
7. Create memory ledger files if missing.
8. Create harness quality gates if missing.
9. Create Cursor command files if missing.
10. Record detected stack and project structure.
11. Do not overwrite existing context unless explicitly asked.
12. Do not create a root `agent-context/` tree — that layout is legacy and must be archived via upgrade.
---END---
---BLOCK:copilot:Required Behavior---

1. Inspect the repository structure.
2. Detect the project stack.
3. Prefer `./scripts/init-project.sh` / `setup-agent-prompts.sh` for a full install.
4. Ensure the single framework home `sdlc-spdd/` exists (storage v3).
5. Create `sdlc-spdd/requirements/` if missing.
6. Create `sdlc-spdd/spdd/` if missing.
7. Create memory ledger files if missing.
8. Create harness quality gates if missing.
9. Record detected stack and project structure.
10. Preserve existing context unless the user explicitly asks to overwrite it.
11. Do not create a root `agent-context/` tree — that layout is legacy and must be archived via upgrade.
---END---
---BLOCK:claude:Required Behavior---

1. Inspect the repository structure.
2. Detect the project stack.
3. Prefer `./scripts/init-project.sh` / `setup-agent-prompts.sh` for a full install.
4. Ensure the single framework home `sdlc-spdd/` exists (storage v3).
5. Create `sdlc-spdd/requirements/` if missing.
6. Create `sdlc-spdd/spdd/` if missing.
7. Create memory ledger files if missing.
8. Create harness quality gates if missing.
9. Create Claude command files if missing.
10. Record detected stack and project structure.
11. Do not overwrite existing context unless explicitly asked.
12. Do not create a root `agent-context/` tree — that layout is legacy and must be archived via upgrade.
---END---
---BLOCK:cursor:Output---

Create or update:

- `sdlc-spdd/requirements/.gitkeep`
- `sdlc-spdd/spdd/canvas/.gitkeep`
- `sdlc-spdd/spdd/analysis/.gitkeep`
- `sdlc-spdd/spdd/tasks/.gitkeep`
- `sdlc-spdd/spdd/reviews/.gitkeep`
- `sdlc-spdd/spdd/sync/.gitkeep`
- `sdlc-spdd/spdd/memory/lessons.jsonl` (empty)
- `sdlc-spdd/spdd/memory/registry.jsonl` (empty)
- `sdlc-spdd/harness/quality-gates.md`

Print a short summary of:

- Detected stack
- Created folders
- Existing folders preserved
- Recommended next command
---END---
---BLOCK:copilot:Output---

Create or update:

- `sdlc-spdd/requirements/.gitkeep`
- `sdlc-spdd/spdd/canvas/.gitkeep`
- `sdlc-spdd/spdd/analysis/.gitkeep`
- `sdlc-spdd/spdd/tasks/.gitkeep`
- `sdlc-spdd/spdd/reviews/.gitkeep`
- `sdlc-spdd/spdd/sync/.gitkeep`
- `sdlc-spdd/spdd/memory/lessons.jsonl` (empty)
- `sdlc-spdd/spdd/memory/registry.jsonl` (empty)
- `sdlc-spdd/harness/quality-gates.md`

Print a short summary of:

- Detected stack
- Created folders
- Existing folders preserved
- Recommended next prompt
---END---
---BLOCK:claude:Output---

Create or update:

- `sdlc-spdd/requirements/.gitkeep`
- `sdlc-spdd/spdd/canvas/.gitkeep`
- `sdlc-spdd/spdd/analysis/.gitkeep`
- `sdlc-spdd/spdd/tasks/.gitkeep`
- `sdlc-spdd/spdd/reviews/.gitkeep`
- `sdlc-spdd/spdd/sync/.gitkeep`
- `sdlc-spdd/spdd/memory/lessons.jsonl` (empty)
- `sdlc-spdd/spdd/memory/registry.jsonl` (empty)
- `sdlc-spdd/harness/quality-gates.md`

Print a short summary of:

- Detected stack
- Created folders
- Existing folders preserved
- Recommended next command
---END---
