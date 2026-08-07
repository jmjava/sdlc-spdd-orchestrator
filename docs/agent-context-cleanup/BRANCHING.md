# Branching and merge rules

## Integration branch

```text
origin/main
    └── cursor/agent-context-cleanup-integration-decf   ← ongoing integration
            ├── cursor/agent-context-cleanup-stay-set-decf
            ├── cursor/agent-context-cleanup-pointers-decf
            └── …
```

## Task loop (agent-managed)

```bash
git fetch origin
git checkout cursor/agent-context-cleanup-integration-decf
git pull origin cursor/agent-context-cleanup-integration-decf

git checkout -b cursor/agent-context-cleanup-<short-task>-decf
# … implement …
git -c commit.gpgsign=false commit …
git push -u origin cursor/agent-context-cleanup-<short-task>-decf

git checkout cursor/agent-context-cleanup-integration-decf
git merge --no-ff cursor/agent-context-cleanup-<short-task>-decf
git push origin cursor/agent-context-cleanup-integration-decf
```

Optional: open a PR **into integration** for visibility; merge does not require human approval.  
Do **not** target `main` until the program is complete.

## Final merge (human approval)

One PR only:

- **Base:** `main`  
- **Head:** `cursor/agent-context-cleanup-integration-decf`  
- **Title:** Agent-context cleanup — lean git + SQLite + Guide parity  

## Git hygiene

- No committing `agent-context/sessions/**` or lockfiles as part of this program’s product commits.  
- If a task dirty’s the tree with generated session files, delete or gitignore — do not leave the Git tab dirty.  
- Sign commits with `commit.gpgsign=false` in this environment when signing keys are unavailable.
