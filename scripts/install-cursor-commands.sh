#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: install-cursor-commands.sh --target <path> [--force]

Install SDLC-SPDD Cursor command templates into .cursor/commands/.
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
DEST="${TARGET}/.cursor/commands"
mkdir -p "${DEST}"

installed=()
skipped=()

for src in "${REPO_ROOT}"/templates/cursor/*.md; do
  base="$(basename "${src}")"
  out="${DEST}/${base}"
  if [[ -f "${out}" && "${FORCE}" -eq 0 ]]; then
    skipped+=("${out}")
    continue
  fi
  cp "${src}" "${out}"
  installed+=("${out}")
done

echo "Installed Cursor commands (${#installed[@]}):"
printf '  %s\n' "${installed[@]:-none}"
echo "Skipped (${#skipped[@]}):"
printf '  %s\n' "${skipped[@]:-none}"
