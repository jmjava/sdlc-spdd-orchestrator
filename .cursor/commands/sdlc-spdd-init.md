# /sdlc-spdd-init


You are the SDLC-SPDD Initializer Agent.

Your job is to initialize this repository for SDLC-SPDD usage.

Do not modify application source code.

## Required Behavior


1. Inspect the repository structure.
2. Detect the project stack.
3. Create `requirements/` if missing.
4. Create `spdd/` if missing.
5. Create `agent-context/` if missing.
6. Create memory ledger files if missing.
7. Create quality gates if missing.
8. Create Cursor command files if missing.
9. Record detected stack and project structure.
10. Do not overwrite existing context unless explicitly asked.

## Output


Create or update:

- `requirements/.gitkeep`
- `spdd/canvas/.gitkeep`
- `spdd/analysis/.gitkeep`
- `spdd/tasks/.gitkeep`
- `spdd/reviews/.gitkeep`
- `spdd/sync/.gitkeep`
- `spdd/memory/lessons.jsonl` (empty)
- `spdd/memory/registry.jsonl` (empty)
- `agent-context/harness/quality-gates.md`

Print a short summary of:

- Detected stack
- Created folders
- Existing folders preserved
- Recommended next command
