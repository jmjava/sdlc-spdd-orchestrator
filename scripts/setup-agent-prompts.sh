#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: setup-agent-prompts.sh --target <path> [--cursor] [--copilot] [--claude] [--all] [--force] [--dry-run]

Set up the integrated SDLC Agents + SPDD prompt system in a target project.

This creates SDLC-SPDD folders, durable memory, session storage, playbooks,
quality harness files, and assistant prompt adapters.

Options:
  --target <path>   Target project path (required)
  --cursor          Install Cursor command prompts
  --copilot         Install GitHub Copilot instructions and prompt files
  --claude          Install Claude Code commands and CLAUDE.md
  --all             Install all supported assistant prompt adapters
  --force           Overwrite existing generated files
  --dry-run         Show actions without writing files
  --help            Print this help message

If no assistant flag is provided, Cursor and Copilot are installed for backward
compatibility. Use --all to include Claude Code.
EOF
}

TARGET=""
INSTALL_CURSOR=0
INSTALL_COPILOT=0
INSTALL_CLAUDE=0
FORCE=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --cursor)
      INSTALL_CURSOR=1
      shift
      ;;
    --copilot)
      INSTALL_COPILOT=1
      shift
      ;;
    --claude)
      INSTALL_CLAUDE=1
      shift
      ;;
    --all)
      INSTALL_CURSOR=1
      INSTALL_COPILOT=1
      INSTALL_CLAUDE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${TARGET}" ]]; then
  echo "Error: --target is required" >&2
  usage >&2
  exit 1
fi

if [[ "${INSTALL_CURSOR}" -eq 0 && "${INSTALL_COPILOT}" -eq 0 && "${INSTALL_CLAUDE}" -eq 0 ]]; then
  INSTALL_CURSOR=1
  INSTALL_COPILOT=1
fi

init_args=(--target "${TARGET}")
if [[ "${INSTALL_CURSOR}" -eq 1 ]]; then
  init_args+=(--cursor)
fi
if [[ "${INSTALL_COPILOT}" -eq 1 ]]; then
  init_args+=(--copilot)
fi
if [[ "${INSTALL_CLAUDE}" -eq 1 ]]; then
  init_args+=(--claude)
fi
if [[ "${FORCE}" -eq 1 ]]; then
  init_args+=(--force)
fi
if [[ "${DRY_RUN}" -eq 1 ]]; then
  init_args+=(--dry-run)
fi

"${SCRIPT_DIR}/init-project.sh" "${init_args[@]}"

echo
echo "Integrated SDLC-SPDD prompt setup complete."
echo "Next steps:"
echo "  1. Open the target project in Cursor, GitHub Copilot, or Claude Code."
echo "  2. Start or resume context:"
echo "     ${TARGET}/scripts/sdlc-spdd/start-agent-session.sh --target ${TARGET} --phase init"
echo "  3. Invoke:"
echo "     /sdlc-spdd-init"
echo
echo "For projects initialized by an older version, use:"
echo "  ${SCRIPT_DIR}/upgrade-project.sh --target ${TARGET} --all"
