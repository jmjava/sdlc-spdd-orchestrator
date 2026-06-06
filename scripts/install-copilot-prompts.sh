#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: install-copilot-prompts.sh --target <path> [--force]

Install SDLC-SPDD GitHub Copilot instructions and prompt files into .github/.
EOF
}

TARGET=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
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
  exit 1
fi

TARGET="$(cd "${TARGET}" && pwd)"
INSTRUCTIONS_DEST="${TARGET}/.github/copilot-instructions.md"
PROMPTS_DEST="${TARGET}/.github/prompts"

installed=()
skipped=()

copy_if_missing() {
  local src="$1"
  local dest="$2"
  if [[ -f "${dest}" && "${FORCE}" -eq 0 ]]; then
    skipped+=("${dest}")
    return
  fi
  mkdir -p "$(dirname "${dest}")"
  cp "${src}" "${dest}"
  installed+=("${dest}")
}

copy_if_missing \
  "${REPO_ROOT}/templates/copilot/copilot-instructions.md" \
  "${INSTRUCTIONS_DEST}"

mkdir -p "${PROMPTS_DEST}"
for src in "${REPO_ROOT}"/templates/copilot/prompts/*.prompt.md; do
  base="$(basename "${src}")"
  copy_if_missing "${src}" "${PROMPTS_DEST}/${base}"
done

echo "Installed Copilot files (${#installed[@]}):"
printf '  %s\n' "${installed[@]:-none}"
echo "Skipped existing (${#skipped[@]}):"
printf '  %s\n' "${skipped[@]:-none}"
