#!/usr/bin/env bash
# Assert install layout for a Cursor-only consumer.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
HOME="$(live_home "${ROOT}")"
echo "== 01 install layout =="

[[ -x "${HOME}/scripts/sdlc.sh" ]] && ok "sdlc.sh installed" || bad "sdlc.sh missing"
[[ ! -e "${HOME}/scripts/sdlc-pointer.sh" ]] && ok "retired pointer script absent" || bad "pointer script should be absent"
[[ ! -e "${HOME}/scripts/sdlc-workflow.sh" ]] && ok "retired workflow script absent" || bad "workflow script should be absent"
[[ ! -e "${HOME}/scripts/sdlc-team-registry.sh" ]] && ok "retired registry script absent" || bad "registry script should be absent"
[[ -f "${HOME}/spdd/memory/registry.jsonl" ]] && ok "registry.jsonl" || bad "registry.jsonl"
[[ -f "${ROOT}/.cursor/rules/sdlc-spdd.mdc" ]] && ok "cursor rule" || bad "cursor rule"
[[ -d "${ROOT}/.cursor/commands" ]] && ok "cursor commands dir" || bad "cursor commands dir"

# Cursor-only: Copilot/Claude adapters must not appear.
if [[ -d "${ROOT}/.github/prompts" ]]; then
  bad "unexpected Copilot prompts on --cursor install"
else
  ok "no Copilot prompts (cursor-only)"
fi
if [[ -d "${ROOT}/.claude/commands" ]]; then
  bad "unexpected Claude commands on --cursor install"
else
  ok "no Claude commands (cursor-only)"
fi

# Seed work visible.
if live_sdlc "${ROOT}" list-work | grep -Fq "${WORK_ID}"; then
  ok "list-work sees ${WORK_ID}"
else
  bad "list-work missing ${WORK_ID}"
fi
