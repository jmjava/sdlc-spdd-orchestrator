#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/readiness.sh"

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

STRICT_READINESS=0
if [[ "${SDLC_CANVAS_STRICT_READINESS:-}" == "1" ]]; then
  STRICT_READINESS=1
fi

section_has_content() {
  local file="$1"
  local heading="$2"
  awk -v h="${heading}" '
    index($0, "## " h) == 1 { grab=1; next }
    grab && /^## / { exit }
    grab {
      line=$0
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
      if (line != "" && substr(line, 1, 1) != "#") { found=1; exit }
    }
    END { exit found ? 0 : 1 }
  ' "${file}"
}

has_operation_with_status() {
  local file="$1"
  awk '
    /^## O - Operations/ || /^## Operations/ { inops=1; next }
    inops && /^## / { exit }
    inops && /^###[[:space:]]+T[0-9]+/ { op=1; next }
    inops && op && /^-[[:space:]]*Status:[[:space:]]*[^[:space:]]/ { found=1; exit }
    END { exit found ? 0 : 1 }
  ' "${file}"
}

check_readiness() {
  local file="$1"
  local raw canon
  raw="$(extract_readiness_raw "${file}")"
  if [[ -z "${raw}" ]]; then
    echo "  readiness: (absent — OK, backward compatible)"
    return 0
  fi
  canon="$(normalize_readiness "${raw}")"
  if [[ -z "${canon}" ]]; then
    if [[ "${STRICT_READINESS}" -eq 1 ]]; then
      echo "Invalid canvas: ${file}" >&2
      echo "Unrecognized readiness '${raw}' (expected: ${READINESS_CANONICAL[*]})" >&2
      echo "  readiness: '${raw}' (unrecognized — fail under --strict-readiness)" >&2
      return 1
    fi
    echo "Warning: ${file}: unrecognized readiness '${raw}' (expected: ${READINESS_CANONICAL[*]})" >&2
    echo "  readiness: '${raw}' (unrecognized — warn only)"
    return 0
  fi
  echo "  readiness: ${canon} (from '${raw}')"
  return 0
}

check_semantic_minima() {
  local file="$1"
  local issues=()
  if ! section_has_content "${file}" "R - Requirements" && ! section_has_content "${file}" "Requirements"; then
    issues+=("empty Requirements section")
  fi
  if ! has_operation_with_status "${file}"; then
    issues+=("no T## operation with Status")
  fi
  if ((${#issues[@]} > 0)); then
    echo "Invalid canvas: ${file}" >&2
    echo "Semantic minima failed (headings-only is not a contract):" >&2
    printf '  - %s\n' "${issues[@]}" >&2
    return 1
  fi
  return 0
}

validate_file() {
  local file="$1"
  local missing=()
  local section
  local work_id

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

  check_semantic_minima "${file}" || return 1
  check_readiness "${file}" || return 1

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
Usage: validate-reasons-canvas.sh [--strict-readiness] <file-or-directory>

Validate REASONS Canvas files for required sections, semantic minima
(non-empty Requirements, at least one T## operation with Status), and
optional readiness.

Exit 0 when all files are valid; non-zero otherwise.

Readiness (optional, FEAT-005 / FEAT-014):
  YAML frontmatter `readiness:` or Metadata bullet `- Readiness:`.
  Canonical values: needs-analysis | needs-clarification | needs-redesign |
  ready-for-coding | blocked | reviewed | complete (Title Case aliases accepted).
  Missing → OK for this script (code-phase gate still requires it).
  Unrecognized → warning only, unless --strict-readiness or
  SDLC_CANVAS_STRICT_READINESS=1 (then fail).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict-readiness)
      STRICT_READINESS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

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
