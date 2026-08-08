#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/areas.sh"

usage() {
  cat <<'EOF'
Usage: index-spdd-analysis.sh --work-id <WORK-ID> [options]

Stage ONE kind=analysis lesson record from spdd/analysis/<WORK-ID>-analysis.md.
Run after /sdlc-spdd-analysis writes the analysis artifact.

Options:
  --target <path>   Target project path (default: .)
  --work-id <id>    Work ID (required)
  --phase <phase>   Phase label (default: analysis)
  --dry-run         Print staged record without writing
  --help            Print this help message
EOF
}

TARGET="."
WORK_ID=""
PHASE="analysis"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --work-id) WORK_ID="${2:-}"; shift 2 ;;
    --phase) PHASE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "${WORK_ID}" ]]; then
  echo "Error: --work-id is required" >&2
  usage >&2
  exit 1
fi

TARGET="$(sdlc_resolve_target "${TARGET}")"
export SDLC_ROOT="${TARGET}"
HOME="$(sdlc_home "${TARGET}")"
timestamp="$(sdlc_timestamp_iso)"
analysis_file="${HOME}/spdd/analysis/${WORK_ID}-analysis.md"
stage_file="$(sdlc_stage "${TARGET}")"

if [[ ! -f "${analysis_file}" ]]; then
  echo "Analysis file not found: ${analysis_file}" >&2
  exit 1
fi

declare -a keywords=()
declare -a areas=()
while IFS= read -r _kw; do
  _kw="$(normalize_token "${_kw}")"
  [[ -n "${_kw}" ]] && keywords+=("${_kw}")
done < <(parse_section_bullets "${analysis_file}" "Domain Keywords")

while IFS= read -r _ar; do
  _ar="$(normalize_area "${_ar}")"
  [[ -n "${_ar}" ]] && areas+=("${_ar}")
done < <(parse_section_bullets "${analysis_file}" "Code Areas")

if ((${#keywords[@]} == 0 && ${#areas[@]} == 0)); then
  echo "No Domain Keywords or Code Areas found in ${analysis_file}" >&2
  exit 1
fi

primary_area=""
if ((${#areas[@]} > 0)); then
  primary_area="${areas[0]}"
fi

all_keywords=("${keywords[@]}")
if ((${#areas[@]} > 1)); then
  all_keywords+=("${areas[@]:1}")
fi
keywords_csv="$(IFS=,; echo "${all_keywords[*]}")"

scope_summary="$(awk '
  /^## Scope Summary/ { in_s=1; next }
  /^## / { if (in_s) exit }
  in_s && /^[^#]/ { gsub(/^[[:space:]]+|[[:space:]]+$/, ""); if (length($0)) { print; exit } }
' "${analysis_file}")"
[[ -z "${scope_summary}" ]] && scope_summary="Analysis indexed for ${WORK_ID}"

record="$(sdlc_build_lesson_json analysis "${WORK_ID}" "${primary_area}" "${PHASE}" \
  "${timestamp}" "Analysis: ${WORK_ID}" "${scope_summary}" "analysis" "${keywords_csv}" "" "${TARGET}")"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "${record}"
  exit 0
fi

sdlc_append_jsonl "${stage_file}" "${record}"
echo "Staged analysis record for ${WORK_ID} → ${stage_file#${TARGET}/}"
echo "  keywords (${#keywords[@]}): ${keywords[*]:-none}"
echo "  code areas (${#areas[@]}): ${areas[*]:-none}"
echo "Run: ./scripts/sdlc.sh accept --work-id ${WORK_ID}"
