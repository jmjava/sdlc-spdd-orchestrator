#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: summarize-session-notes.sh [--target <path>] (--all|--file <path>) [--dry-run]

Import session-notes/*.md into agent-context/memory/session-history.md and
agent-context/memory/project-memory.md so existing human session notes become
available to future agents.

Options:
  --target <path>  Target project path (default: .)
  --all            Import all session notes
  --file <path>    Import one session note file
  --dry-run        Show import output without writing files
  --help           Print this help message
EOF
}

TARGET="."
IMPORT_ALL=0
NOTE_FILE=""
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --all)
      IMPORT_ALL=1
      shift
      ;;
    --file)
      NOTE_FILE="${2:-}"
      shift 2
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

if [[ "${IMPORT_ALL}" -eq 1 && -n "${NOTE_FILE}" ]]; then
  echo "Error: use either --all or --file, not both" >&2
  exit 1
fi

if [[ "${IMPORT_ALL}" -eq 0 && -z "${NOTE_FILE}" ]]; then
  echo "Error: one of --all or --file is required" >&2
  usage >&2
  exit 1
fi

TARGET="$(cd "${TARGET}" && pwd)"
session_notes_dir="${TARGET}/session-notes"
memory_dir="${TARGET}/agent-context/memory"
session_history="${memory_dir}/session-history.md"
project_memory="${memory_dir}/project-memory.md"

notes=()
if [[ "${IMPORT_ALL}" -eq 1 ]]; then
  shopt -s nullglob
  notes=("${session_notes_dir}"/*.md)
  shopt -u nullglob
else
  if [[ "${NOTE_FILE}" != /* ]]; then
    NOTE_FILE="${TARGET}/${NOTE_FILE}"
  fi
  notes=("${NOTE_FILE}")
fi

if ((${#notes[@]} == 0)); then
  echo "No session notes found." >&2
  exit 1
fi

if [[ "${DRY_RUN}" -eq 0 ]]; then
  mkdir -p "${memory_dir}"
  if [[ ! -f "${session_history}" ]]; then
    printf '# Session History\n\n## Sessions\n' > "${session_history}"
  fi
  if [[ ! -f "${project_memory}" ]]; then
    printf '# Project Memory\n\n' > "${project_memory}"
  fi
fi

imported=0
skipped=0

for note in "${notes[@]}"; do
  if [[ ! -f "${note}" ]]; then
    echo "Session note not found: ${note}" >&2
    exit 1
  fi

  rel="${note#${TARGET}/}"
  marker="Imported session note: ${rel}"
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  if [[ "${DRY_RUN}" -eq 0 && -f "${session_history}" ]] && grep -Fq "${marker}" "${session_history}"; then
    skipped=$((skipped + 1))
    continue
  fi

  entry="$(cat <<EOF

### ${timestamp} - ${marker}

Source: ${rel}

$(cat "${note}")
EOF
)"

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "${entry}"
  else
    printf '%s\n' "${entry}" >> "${session_history}"
    {
      echo
      echo "### ${timestamp} - ${rel}"
      echo
      echo "- Imported session note into durable memory."
    } >> "${project_memory}"
  fi
  imported=$((imported + 1))
done

echo "Imported session notes: ${imported}"
echo "Skipped existing imports: ${skipped}"
if [[ "${imported}" -gt 0 ]]; then
  echo
  echo "Planning review prompt (see docs/sdlc-spdd/planning-prompt-standard.md):"
  echo "  Read @agent-context/memory/session-history.md entries imported from session-notes. Summarize recurring themes, open risks, and Work IDs mentioned."
fi
