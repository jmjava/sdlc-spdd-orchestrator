#!/usr/bin/env bash
# Assert every Cursor slash-command adapter is installed.
set -euo pipefail
# shellcheck source=../lib.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/lib.sh"

ROOT="${1:?target root required}"
echo "== 05 cursor slash-command adapters =="

COMMANDS=(
  sdlc-spdd-init
  sdlc-spdd-plan
  sdlc-spdd-architect
  sdlc-spdd-analysis
  sdlc-spdd-code
  sdlc-spdd-api-test
  sdlc-spdd-review
  sdlc-spdd-sync
  sdlc-spdd-retro
  sdlc-spdd-prompt-update
  sdlc-spdd-commit-message
  sdlc-spdd-sunset
  sdlc-spdd-whereami
  sdlc-claim
  sdlc-next
  sdlc-advance
  sdlc-shelf
  sdlc-team
)

for cmd in "${COMMANDS[@]}"; do
  path="${ROOT}/.cursor/commands/${cmd}.md"
  if [[ -f "${path}" ]] && grep -q . "${path}"; then
    ok "/${cmd} adapter present"
  else
    bad "/${cmd} adapter missing"
  fi
done
