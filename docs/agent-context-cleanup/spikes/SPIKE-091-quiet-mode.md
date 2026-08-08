# SPIKE-091: Quiet / product-test mode

GitHub: [#91](https://github.com/jmjava/sdlc-spdd-orchestrator/issues/91)  
Status: **implemented**

## Decision

Enable when any of:

- `SDLC_QUIET=1`  
- `agent-context/harness/quiet-mode.md` exists  
- `--quiet` on `start-agent-session.sh`

Effects:

- Do not inject next T## / dogfood gravity into briefs  
- `sdlc_workflow_recommended_command` returns quiet blurb  
- Still allow on-demand retrieve of lessons/graph via ContextStore  

CLI: `sdlc-engine agent-context quiet-status`
