#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: install-claude-commands.sh --target <path> [--force]

Install SDLC-SPDD Claude Code command templates into .claude/commands/ and the
project memory file CLAUDE.md into the target project root.
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
COMMANDS_DEST="${TARGET}/.claude/commands"
MEMORY_DEST="${TARGET}/CLAUDE.md"

installed=()
updated=()
skipped=()

CLAUDE_BEGIN="<!-- BEGIN SDLC-SPDD MANAGED CLAUDE GROUNDING -->"
CLAUDE_END="<!-- END SDLC-SPDD MANAGED CLAUDE GROUNDING -->"

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

upsert_claude_memory() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "${dest}")"
  if [[ ! -f "${dest}" || "${FORCE}" -eq 1 ]]; then
    cp "${src}" "${dest}"
    installed+=("${dest}")
    return
  fi

  local tmp
  tmp="$(mktemp)"
  awk -v begin="${CLAUDE_BEGIN}" -v end="${CLAUDE_END}" -v src="${src}" '
    BEGIN {
      while ((getline line < src) > 0) {
        block = block line ORS
      }
      close(src)
    }
    $0 == begin {
      printf "%s", block
      in_block = 1
      replaced = 1
      next
    }
    $0 == end {
      in_block = 0
      next
    }
    !in_block { print }
    END {
      if (!replaced) {
        if (NR > 0) {
          print ""
        }
        printf "%s", block
      }
    }
  ' "${dest}" > "${tmp}"

  if cmp -s "${tmp}" "${dest}"; then
    rm -f "${tmp}"
    skipped+=("${dest}")
    return
  fi
  mv "${tmp}" "${dest}"
  updated+=("${dest}")
}

upsert_claude_memory \
  "${REPO_ROOT}/templates/claude/CLAUDE.md" \
  "${MEMORY_DEST}"

mkdir -p "${COMMANDS_DEST}"
for src in "${REPO_ROOT}"/templates/claude/commands/*.md; do
  base="$(basename "${src}")"
  copy_if_missing "${src}" "${COMMANDS_DEST}/${base}"
done

echo "Installed Claude Code files (${#installed[@]}):"
printf '  %s\n' "${installed[@]:-none}"
echo "Updated Claude Code files (${#updated[@]}):"
printf '  %s\n' "${updated[@]:-none}"
echo "Skipped existing (${#skipped[@]}):"
printf '  %s\n' "${skipped[@]:-none}"
