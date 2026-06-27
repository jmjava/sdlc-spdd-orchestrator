#!/usr/bin/env bash
# Short entry point for SDLC pointer + workflow helpers.
# Installed to scripts/sdlc-spdd/sdlc.sh in target projects; lives at scripts/sdlc.sh in the orchestrator repo.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "${SCRIPT_DIR}/../agent-context/sdlc-workflow.sh" ]]; then
  ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
elif [[ -f "${SCRIPT_DIR}/../../agent-context/sdlc-workflow.sh" ]]; then
  ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
else
  ROOT="$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

WORKFLOW="${ROOT}/agent-context/sdlc-workflow.sh"
if [[ ! -x "${WORKFLOW}" ]]; then
  echo "sdlc: workflow not installed (${WORKFLOW})" >&2
  echo "Run setup-agent-prompts.sh or upgrade-project.sh from the orchestrator repo." >&2
  exit 1
fi

export SDLC_ROOT="${ROOT}"
cmd="${1:-next}"
if [[ $# -gt 0 ]]; then
  shift
fi
exec "${WORKFLOW}" "${cmd}" "$@"
