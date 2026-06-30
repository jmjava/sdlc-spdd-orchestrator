# Enhancement: Add Agent Commands for Workflow State Management

**Status:** Proposed  
**Date:** 2026-06-30  
**Author:** John Menke  
**Related:** Workflow CLI upgrade (PR #20, #21)

## Summary

The workflow CLI (`sdlc.sh`) provides commands for managing work state (`claim`, `shelf`, `advance`, `next`), but these are currently shell-only. They should be wired up as agent commands (Cursor, Copilot, Claude Code) so users can manage their Work ID and phase from within the editor/chat without switching to terminal.

## Current State

✅ **Implemented:**
- Shell scripts exist and work: `agent-context/sdlc-pointer.sh`, `agent-context/sdlc-workflow.sh`, `agent-context/sdlc-team-registry.sh`
- CLI works: `./scripts/sdlc.sh claim|shelf|advance|next`
- Team registry is committed for visibility

❌ **Missing:**
- No agent commands (`.cursor/commands/`, `.github/prompts/`, `.claude/commands/`)
- Users must switch to terminal to manage work state
- No parity checks for agent command availability

## Desired State

Users should be able to invoke (in any supported editor/chat):

```
/sdlc-claim <WORK-ID>          — Claim a work item and set pointer
/sdlc-shelf [reason]           — Shelf active work (pause temporarily)
/sdlc-advance [--to PHASE]     — Advance to next phase gate
/sdlc-next                     — Show next action for current work (alias for /sdlc-spdd-whereami)
/sdlc-team                     — See team work registry
```

## Implementation Notes

### Architecture

1. **Command Templates** — Create `.cursor/commands/sdlc-*.md`, `.github/prompts/sdlc-*.prompt.md`, `.claude/commands/sdlc-*.md`
2. **Shell Integration** — Commands delegate to existing functions in `agent-context/sdlc-*.sh`
3. **Parity** — Update `validate-command-adapters.sh` to include checks for new commands
4. **Install** — Add to `scripts/upgrade-project.sh` so new projects get them automatically

### Commands Detail

#### /sdlc-claim <WORK-ID>
- **Input:** Work ID (e.g., `FEAT-001-shared-script-library`)
- **Action:** 
  - Set `.sdlc/pointer` to WORK-ID
  - Update team registry (status: active, owner: current user)
  - Auto-detect branch name and Jira key if available
- **Output:** Confirmation + recommended next command (`/sdlc-spdd-analysis` or `/sdlc-spdd-whereami`)

#### /sdlc-shelf [reason]
- **Input:** Optional reason (e.g., "waiting for upstream PR")
- **Action:**
  - Clear `.sdlc/pointer`
  - Update team registry (status: shelved, reason: captured)
- **Output:** Confirmation + list of available work items

#### /sdlc-advance [--to PHASE]
- **Input:** Optional target phase
- **Action:**
  - Move from current phase to next (or specified phase)
  - Update workflow state file
  - Update team registry
- **Output:** Confirmation + recommended next command for new phase

#### /sdlc-next
- **Input:** None
- **Action:** Same as `/sdlc-spdd-whereami` (already exists, but alias useful)
- **Output:** Current work, phase, and recommended next command

#### /sdlc-team
- **Input:** None
- **Action:** Display team registry with status indicators
- **Output:** Table showing who's on what, phase, stale claims

### Grounding Integration

Add to always-on grounding files (`.cursor/rules/sdlc-spdd.mdc`, `.github/copilot-instructions.md`, `CLAUDE.md`):

```markdown
## Workflow Commands

Manage your Work ID and lifecycle phase:
- /sdlc-claim <WORK-ID>        Claim a work item (sets pointer)
- /sdlc-shelf [reason]         Shelf current work (pause temporarily)
- /sdlc-advance [--to PHASE]   Advance to next phase gate
- /sdlc-next                   Show next action for current work
- /sdlc-team                   See team work registry

Workflow state is tracked in `.sdlc/` (local, private) and `agent-context/work-registry.tsv` (shared).
```

## Benefits

1. **Reduced Context Switching** — Users stay in editor/chat to manage work
2. **Discoverability** — Commands appear in command palette
3. **Consistency** — Same workflow across all supported adapters
4. **Documentation** — Agent prompts document expected usage
5. **Observability** — Team can see work state from registry without asking

## Testing

- [ ] New commands available in Cursor, Copilot, Claude Code
- [ ] Commands respect existing pointer/registry state
- [ ] Team registry updates correctly when commands run
- [ ] Parity validation passes in CI (`validate-command-adapters.sh`)
- [ ] Upgrade script (`upgrade-project.sh`) installs new commands without regression
- [ ] Dry-run shows new commands without breaking existing setup

## Migration Path

1. Create command templates + shell integration
2. Add to `upgrade-project.sh`
3. Validate in CI
4. Document in `docs/workflow.md`
5. Ship in next release (Milestone 1+ ready)

## Related Issues

- PR #20: SDLC pointer manager
- PR #21: Workflow CLI + team registry

## Next Steps

- [ ] Clarify which phase gates require which conditions
- [ ] Decide on command naming convention (/ prefix consistent?)
- [ ] Prototype one command (e.g., `/sdlc-claim`) end-to-end
- [ ] Review for edge cases (concurrent claims, offline state, etc.)
