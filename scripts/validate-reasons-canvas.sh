#!/usr/bin/env bash
set -euo pipefail

REQUIRED_SECTIONS=(
  "Metadata"
  "R - Requirements"
  "E - Entities"
  "A - Approach"
  "S - Structure"
  "O - Operations"
  "N - Norms"
  "S - Safeguards"
  "Review Checklist"
  "Sync Notes"
  "Final Status"
)

validate_file() {
  local file="$1"
  local missing=()
  local section

  if [[ ! -f "${file}" ]]; then
    echo "File not found: ${file}" >&2
    return 1
  fi

  for section in "${REQUIRED_SECTIONS[@]}"; do
    if ! grep -Fq "## ${section}" "${file}"; then
      missing+=("${section}")
    fi
  done

  if ((${#missing[@]} > 0)); then
    echo "Invalid canvas: ${file}" >&2
    echo "Missing sections:" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    work_id="$(basename "${file}" .md)"
    echo >&2
    echo "SPDD fix prompts (see docs/sdlc-spdd/spdd-prompt-standard.md):" >&2
    echo "  /sdlc-spdd-plan @requirements/milestones/${work_id}.md @milestone-1.md" >&2
    echo "  (milestone work) or /sdlc-spdd-plan @requirements/<file>.md (ad-hoc)" >&2
    echo "  Or complete missing REASONS sections in ${file} before /sdlc-spdd-architect." >&2
    return 1
  fi

  work_id="$(basename "${file}" .md)"
  echo "Valid canvas: ${file}"
  echo
  echo "Next SPDD prompts (see docs/sdlc-spdd/spdd-prompt-standard.md):"
  echo "  /sdlc-spdd-architect @spdd/canvas/${work_id}.md"
  echo "  Then when Ready For Coding: /sdlc-spdd-code @spdd/canvas/${work_id}.md operation T01"
  return 0
}

usage() {
  cat <<'EOF'
Usage: validate-reasons-canvas.sh <file-or-directory>

Validate REASONS Canvas files for required sections.
Exit 0 when all files are valid; non-zero otherwise.
EOF
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

target="$1"
failures=0

if [[ -d "${target}" ]]; then
  shopt -s nullglob
  files=("${target}"/*.md)
  shopt -u nullglob
  if ((${#files[@]} == 0)); then
    echo "No canvas files found in ${target}" >&2
    exit 1
  fi
  for file in "${files[@]}"; do
    validate_file "${file}" || failures=$((failures + 1))
  done
else
  validate_file "${target}" || failures=$?
fi

exit "${failures}"
