#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/areas.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/milestone.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/readiness.sh"

usage() {
  cat <<'EOF'
Usage: capture-session-memory.sh --work-id <WORK-ID> --summary <text> [options]

Persist session context: hot brief touch-up + staged lesson records (storage v3).
Captures write to .sdlc/staged/lessons.jsonl only — run `sdlc.sh accept` at retro/sync.

Options:
  --target <path>       Target project path (default: .)
  --work-id <WORK-ID>   Work ID to update (required)
  --phase <phase>       SDLC phase (default: resume)
  --summary <text>      Session summary
  --summary-file <path> Read session summary from a file; use - for stdin
  --validation <text>   Validation or tests performed
  --decisions <text>    Architecture or product decisions
  --pitfalls <text>     Pitfalls to remember
  --patterns <text>     Reusable patterns to remember
  --areas <text>        Override/supplement parsed code areas (comma/space separated)
  --no-session-areas    Do not parse session content for categories
  --milestone <path>    When set, append progress to this milestone doc
  --roadmap-note <text> Append a progress note to ROADMAP.md
  --session-note        Write session-notes/YYYY-MM-DD.md (opt-in)
  --next <text>         Next recommended command or action
  --history-limit <n>   Ignored (legacy; kept for CLI compatibility)
  --no-history-rotate   Ignored (legacy; kept for CLI compatibility)
  --readiness <text>    Optional capture metric: canvas readiness value
  --review-result <v>   Optional: pass|fail|mixed|blocked
  --rework <n>          Optional non-negative integer
  --context-files <n>   Optional non-negative integer
  --validate-cycles <n> Optional non-negative integer
  --review-cycles <n>   Optional non-negative integer
  --dry-run             Print staged records without writing
  --help                Print this help message
EOF
}

TARGET="."
WORK_ID=""
PHASE="resume"
SUMMARY=""
SUMMARY_FILE=""
VALIDATION=""
DECISIONS=""
PITFALLS=""
PATTERNS=""
AREAS=""
MILESTONE=""
ROADMAP_NOTE=""
NEXT_STEP=""
WRITE_SESSION_NOTE=0
HISTORY_LIMIT=20
ROTATE_HISTORY=1
RESOLVE_SESSION_AREAS=1
DRY_RUN=0
METRIC_READINESS=""
METRIC_REVIEW_RESULT=""
METRIC_REWORK=""
METRIC_CONTEXT_FILES=""
METRIC_VALIDATE_CYCLES=""
METRIC_REVIEW_CYCLES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --work-id) WORK_ID="${2:-}"; shift 2 ;;
    --phase) PHASE="${2:-}"; shift 2 ;;
    --summary) SUMMARY="${2:-}"; shift 2 ;;
    --summary-file) SUMMARY_FILE="${2:-}"; shift 2 ;;
    --validation) VALIDATION="${2:-}"; shift 2 ;;
    --decisions) DECISIONS="${2:-}"; shift 2 ;;
    --pitfalls) PITFALLS="${2:-}"; shift 2 ;;
    --patterns) PATTERNS="${2:-}"; shift 2 ;;
    --areas) AREAS="${2:-}"; shift 2 ;;
    --milestone) MILESTONE="${2:-}"; shift 2 ;;
    --roadmap-note) ROADMAP_NOTE="${2:-}"; shift 2 ;;
    --next) NEXT_STEP="${2:-}"; shift 2 ;;
    --session-note) WRITE_SESSION_NOTE=1; shift ;;
    --no-session-note) WRITE_SESSION_NOTE=0; shift ;;
    --history-limit) HISTORY_LIMIT="${2:-}"; shift 2 ;;
    --no-history-rotate) ROTATE_HISTORY=0; shift ;;
    --no-session-areas) RESOLVE_SESSION_AREAS=0; shift ;;
    --readiness) METRIC_READINESS="${2:-}"; shift 2 ;;
    --review-result) METRIC_REVIEW_RESULT="${2:-}"; shift 2 ;;
    --rework) METRIC_REWORK="${2:-}"; shift 2 ;;
    --context-files) METRIC_CONTEXT_FILES="${2:-}"; shift 2 ;;
    --validate-cycles) METRIC_VALIDATE_CYCLES="${2:-}"; shift 2 ;;
    --review-cycles) METRIC_REVIEW_CYCLES="${2:-}"; shift 2 ;;
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

if [[ -n "${SUMMARY_FILE}" ]]; then
  if [[ "${SUMMARY_FILE}" == "-" ]]; then
    SUMMARY="$(cat)"
  else
    [[ -f "${SUMMARY_FILE}" ]] || { echo "Summary file not found: ${SUMMARY_FILE}" >&2; exit 1; }
    SUMMARY="$(<"${SUMMARY_FILE}")"
  fi
fi

if [[ -z "${SUMMARY}" ]]; then
  echo "Error: --summary or --summary-file is required" >&2
  usage >&2
  exit 1
fi

TARGET="$(sdlc_resolve_target "${TARGET}")"
export SDLC_ROOT="${TARGET}"
HOME="$(sdlc_home "${TARGET}")"
timestamp="$(sdlc_timestamp_iso)"
session_day="$(sdlc_timestamp_day)"

session_dir="$(sdlc_sessions_dir "${TARGET}")"
stage_file="$(sdlc_stage "${TARGET}")"
current_session="${session_dir}/current-session.md"
session_notes_dir="${HOME}/session-notes"
daily_session_note="${session_notes_dir}/${session_day}.md"
roadmap_file="${HOME}/ROADMAP.md"
canvas_file="${HOME}/spdd/canvas/${WORK_ID}.md"
analysis_file="${HOME}/spdd/analysis/${WORK_ID}-analysis.md"

milestone_file=""
if [[ -n "${MILESTONE}" ]]; then
  if [[ "${MILESTONE}" == /* ]]; then
    milestone_file="${MILESTONE}"
  else
    milestone_file="${HOME}/${MILESTONE#./}"
  fi
  [[ -f "${milestone_file}" ]] || { echo "Milestone not found: ${milestone_file}" >&2; exit 1; }
fi

# --- area resolution (for lesson area + keywords) ---
normalize_content_for_match() {
  local c="$1"
  c="$(printf '%s' "${c}" | tr '[:upper:]' '[:lower:]')"
  c="$(printf '%s' "${c}" | tr '\n' ' ' | tr -s ' ')"
  printf '%s' "${c}"
}

collect_session_content() {
  local _parts=""
  _parts+="${SUMMARY}"$'\n'
  [[ -f "${current_session}" ]] && _parts+="$(<"${current_session}")"$'\n'
  local _latest=""
  _latest="$(ls -1t "${session_dir}"/20*.md 2>/dev/null | sed -n '1p' || true)"
  [[ -n "${_latest}" && -f "${_latest}" ]] && _parts+="$(<"${_latest}")"$'\n'
  [[ -f "${daily_session_note}" ]] && _parts+="$(<"${daily_session_note}")"$'\n'
  [[ -f "${canvas_file}" ]] && _parts+="$(<"${canvas_file}")"$'\n'
  [[ -f "${analysis_file}" ]] && _parts+="$(<"${analysis_file}")"$'\n'
  [[ -n "${VALIDATION}" ]] && _parts+="${VALIDATION}"$'\n'
  [[ -n "${DECISIONS}" ]] && _parts+="${DECISIONS}"$'\n'
  [[ -n "${PITFALLS}" ]] && _parts+="${PITFALLS}"$'\n'
  [[ -n "${PATTERNS}" ]] && _parts+="${PATTERNS}"$'\n'
  printf '%s' "${_parts}"
}

area_path_excluded() {
  local norm="$1"
  case "${norm}" in
    agent-context/*|spdd/canvas/*|docs/*|session-notes/*|requirements/*|.cursor/*|.sdlc/*)
      return 0 ;;
  esac
  return 1
}

strip_path_filename() {
  local p="$1"
  local base="${p##*/}"
  if [[ "${base}" == *.* && "${p}" == */* ]]; then
    p="${p%/*}"
  fi
  printf '%s' "${p}"
}

path_token_to_area() {
  local token="$1"
  token="$(normalize_area "${token}")"
  token="${token%"${token##*[[:alnum:]_/-]}"}"
  [[ -z "${token}" ]] && return 0
  token="$(strip_path_filename "${token}")"
  [[ -z "${token}" ]] && return 0
  if [[ "${token}" =~ ^src/(main|test)/java/(.+)$ ]]; then
    printf '%s' "${BASH_REMATCH[2]//\//.}"
    return 0
  fi
  area_path_excluded "${token}" && return 0
  if [[ "${token}" == */* ]]; then
    local first rest second
    first="${token%%/*}"
    rest="${token#*/}"
    second="${rest%%/*}"
    area_path_excluded "${first}/${second}" && return 0
    printf '%s' "${first}/${second}"
  fi
}

extract_areas_from_session_content() {
  local content="$1" token area
  while IFS= read -r token; do
    [[ -z "${token}" ]] && continue
    area="$(path_token_to_area "${token}")"
    [[ -n "${area}" ]] && printf '%s\n' "${area}"
  done < <(printf '%s' "${content}" | grep -oE '(src|scripts|tests|lib|pkg|internal|cmd|packages|modules)/[A-Za-z0-9_./-]+' 2>/dev/null || true)
}

areas=()
declare -A _resolved_norm=()
register_area_candidate() {
  local candidate="$1"
  [[ -z "${candidate}" ]] && return 0
  local _norm
  _norm="$(normalize_area "${candidate}")"
  [[ -z "${_norm}" || -n "${_resolved_norm[${_norm}]:-}" ]] && return 0
  _resolved_norm[${_norm}]=1
  areas+=("${candidate}")
}

_session_content="$(collect_session_content)"
if [[ "${RESOLVE_SESSION_AREAS}" -eq 1 && -n "${_session_content}" ]]; then
  while IFS= read -r _extracted; do
    [[ -z "${_extracted}" ]] && continue
    register_area_candidate "${_extracted}"
  done < <(extract_areas_from_session_content "${_session_content}")
fi
if [[ -n "${AREAS}" ]]; then
  IFS=', ' read -ra _areas_raw <<< "${AREAS}"
  for _a in "${_areas_raw[@]}"; do
    register_area_candidate "${_a}"
  done
fi

primary_area=""
extra_keywords=""
if ((${#areas[@]} > 0)); then
  primary_area="${areas[0]}"
  if ((${#areas[@]} > 1)); then
    extra_keywords="$(IFS=,; echo "${areas[*]:1}")"
  fi
fi

# Metrics in session body
METRIC_PARTS=()
[[ -n "${METRIC_READINESS}" ]] && METRIC_PARTS+=("readiness=$(sdlc_oneline "${METRIC_READINESS}" 80)")
[[ -n "${METRIC_REVIEW_RESULT}" ]] && METRIC_PARTS+=("review-result=${METRIC_REVIEW_RESULT}")
[[ -n "${METRIC_REWORK}" ]] && METRIC_PARTS+=("rework=${METRIC_REWORK}")
[[ -n "${METRIC_CONTEXT_FILES}" ]] && METRIC_PARTS+=("context-files=${METRIC_CONTEXT_FILES}")
METRIC_ENTRY=""
if ((${#METRIC_PARTS[@]} > 0)); then
  local_ifs="${IFS}"
  IFS='; '
  METRIC_ENTRY="${METRIC_PARTS[*]}"
  IFS="${local_ifs}"
fi

session_body="$(cat <<EOF
Phase: ${PHASE}
Summary: ${SUMMARY}
Validation: ${VALIDATION:-Not recorded}
Next: ${NEXT_STEP:-Not recorded}
Areas: ${areas[*]:-none}
${METRIC_ENTRY:+Metrics: ${METRIC_ENTRY}}
EOF
)"

stage_record() {
  local kind="$1" title="$2" body="$3" source="$4"
  local kw_csv="${extra_keywords}"
  sdlc_build_lesson_json "${kind}" "${WORK_ID}" "${primary_area}" "${PHASE}" \
    "${timestamp}" "${title}" "${body}" "${source}" "${kw_csv}" "" "${TARGET}"
}

staged_records=()
staged_records+=("$(stage_record session "${SUMMARY}" "${session_body}" "capture")")
[[ -n "${DECISIONS}" ]] && staged_records+=("$(stage_record decision "Decision: ${WORK_ID}" "${DECISIONS}" "capture")")
[[ -n "${PITFALLS}" ]] && staged_records+=("$(stage_record pitfall "Pitfall: ${WORK_ID}" "${PITFALLS}" "capture")")
[[ -n "${PATTERNS}" ]] && staged_records+=("$(stage_record pattern "Pattern: ${WORK_ID}" "${PATTERNS}" "capture")")

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "Dry-run staged records:"
  for rec in "${staged_records[@]}"; do
    printf '%s\n' "${rec}"
  done
  exit 0
fi

mkdir -p "${session_dir}" "$(dirname "${stage_file}")"
for rec in "${staged_records[@]}"; do
  sdlc_append_jsonl "${stage_file}" "${rec}"
done

if [[ -f "${current_session}" ]]; then
  {
    echo
    echo "## Captured Memory"
    echo
    echo "- Captured at: ${timestamp}"
    echo "- Summary: ${SUMMARY}"
    echo "- Validation: ${VALIDATION:-Not recorded}"
    echo "- Next: ${NEXT_STEP:-Not recorded}"
  } >> "${current_session}"
fi

if [[ "${WRITE_SESSION_NOTE}" -eq 1 ]]; then
  mkdir -p "${session_notes_dir}"
  sdlc_ensure_file "${daily_session_note}" "Session Notes: ${session_day}" 0
  {
    echo
    echo "### ${timestamp} - ${WORK_ID} - ${PHASE}"
    echo
    echo "- Summary: ${SUMMARY}"
    echo "- Validation: ${VALIDATION:-Not recorded}"
    echo "- Next: ${NEXT_STEP:-Not recorded}"
  } >> "${daily_session_note}"
fi

if [[ -n "${milestone_file}" ]]; then
  {
    echo
    echo "### ${timestamp} - ${WORK_ID} - ${PHASE}"
    echo
    echo "- Summary: ${SUMMARY}"
    echo "- Validation: ${VALIDATION:-Not recorded}"
    echo "- Next: ${NEXT_STEP:-Not recorded}"
  } >> "${milestone_file}"
fi

if [[ -n "${ROADMAP_NOTE}" ]]; then
  sdlc_ensure_file "${roadmap_file}" "Roadmap" 0
  {
    echo
    echo "### ${timestamp} - ${WORK_ID} - ${PHASE}"
    echo
    echo "- ${ROADMAP_NOTE}"
    echo "- Summary: ${SUMMARY}"
    echo "- Next: ${NEXT_STEP:-Not recorded}"
  } >> "${roadmap_file}"
fi

workflow_script="${TARGET}/agent-context/sdlc-workflow.sh"
if [[ -f "${workflow_script}" ]]; then
  SDLC_ROOT="${TARGET}"
  # shellcheck source=/dev/null
  source "${workflow_script}"
  sdlc_workflow_record_capture "${WORK_ID}" "${PHASE}"
fi

echo "staged ${#staged_records[@]} records → ${stage_file#${TARGET}/}; run 'sdlc.sh accept --work-id ${WORK_ID}' at retro/sync"
