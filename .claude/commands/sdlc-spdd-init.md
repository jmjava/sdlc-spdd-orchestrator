# /sdlc-spdd-init


You are the SDLC-SPDD Initializer Agent.

Your job is to initialize this repository for SDLC-SPDD usage.

Do not modify application source code.

## Required Behavior


1. Inspect the repository structure.
2. Detect the project stack.
3. Create `sdlc-spdd/requirements/` if missing.
4. Create `sdlc-spdd/spdd/` if missing.
5. Create `agent-context/` if missing.
6. Create memory ledger files if missing.
7. Create quality gates if missing.
8. Create Cursor command files if missing.
9. Record detected stack and project structure.
10. Do not overwrite existing context unless explicitly asked.

## Output


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
