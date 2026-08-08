#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/areas.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/context-index.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/milestone.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/readiness.sh"

usage() {
  cat <<'EOF'
Usage: capture-session-memory.sh --work-id <WORK-ID> --summary <text> [options]

Persist current agent-session context into SDLC-SPDD memory so future sessions can resume.

Options:
  --target <path>       Target project path (default: .)
  --work-id <WORK-ID>   Work ID to update (required)
  --phase <phase>       SDLC phase, such as plan, code, review, sync (default: resume)
  --summary <text>      Session summary
  --summary-file <path> Read session summary from a file; use - for stdin
  --validation <text>   Validation or tests performed
  --decisions <text>    Architecture or product decisions to append
  --pitfalls <text>     Pitfalls to remember
  --patterns <text>     Reusable patterns to remember
  --areas <text>        Optional override: extra code areas (space- or comma-separated).
                        Normally the script parses session documents/content:
                        summary, session-notes, current-session.md, the latest
                        timestamped session brief in agent-context/sessions/,
                        canvas, and progress log to create new categories.
                        Use only to correct or supplement parsed areas.
  --no-session-areas    Do not parse session content for categories (tests only)
  --milestone <path>    Milestone doc to append, such as milestone-1.md. When
                        omitted, searches milestone-*.md for the Work ID.
  --roadmap-note <text> Append a progress note to ROADMAP.md
  --no-session-note     Do not write session-notes/YYYY-MM-DD.md
  --next <text>         Next recommended command or action
  --history-limit <n>   Keep at most n recent entries inline in session-history.md;
                        older entries move to agent-context/memory/archive/ (default 20)
  --no-history-rotate   Keep session-history.md append-only (do not rotate/archive)
  --readiness <text>    Optional capture metric: canvas readiness value.
                        When omitted, auto-fills from canvas Metadata/YAML
                        readiness if present (FEAT-005).
  --review-result <v>   Optional capture metric: pass|fail|mixed|blocked
                        (unknown values warn and are skipped; capture continues)
  --rework <n>          Optional capture metric: non-negative integer (corrective
                        prompt-update/sync cycles after first Ready For Coding)
  --context-files <n>   Optional capture metric: approximate context file count
  --validate-cycles <n> Optional leading indicator: non-negative validate cycle count
  --review-cycles <n>   Optional leading indicator: non-negative review cycle count
  --dry-run             Print the memory entry without writing files
  --help                Print this help message

Examples:
  ./scripts/capture-session-memory.sh --work-id FEAT-001-order-status-api --phase code --summary "Implemented T01 in com.acme.order" --validation "mvn test"
  ./scripts/capture-session-memory.sh --work-id FEAT-002-payments --phase code --summary "Added src/payments module and wired checkout"
  ./scripts/capture-session-memory.sh --work-id BUG-003-null-discount --summary-file notes.md --pitfalls "Discount can be null in legacy orders"
  ./scripts/capture-session-memory.sh --work-id FEAT-004-prompt-optimization-ledger --phase code \
    --summary "Captured metrics" --areas "scripts/capture-session-memory.sh" \
    --readiness "Ready For Coding" --review-result pass --rework 0 --context-files 12
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
WRITE_SESSION_NOTE=1
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
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --work-id)
      WORK_ID="${2:-}"
      shift 2
      ;;
    --phase)
      PHASE="${2:-}"
      shift 2
      ;;
    --summary)
      SUMMARY="${2:-}"
      shift 2
      ;;
    --summary-file)
      SUMMARY_FILE="${2:-}"
      shift 2
      ;;
    --validation)
      VALIDATION="${2:-}"
      shift 2
      ;;
    --decisions)
      DECISIONS="${2:-}"
      shift 2
      ;;
    --pitfalls)
      PITFALLS="${2:-}"
      shift 2
      ;;
    --patterns)
      PATTERNS="${2:-}"
      shift 2
      ;;
    --areas)
      AREAS="${2:-}"
      shift 2
      ;;
    --milestone)
      MILESTONE="${2:-}"
      shift 2
      ;;
    --roadmap-note)
      ROADMAP_NOTE="${2:-}"
      shift 2
      ;;
    --next)
      NEXT_STEP="${2:-}"
      shift 2
      ;;
    --no-session-note)
      WRITE_SESSION_NOTE=0
      shift
      ;;
    --history-limit)
      HISTORY_LIMIT="${2:-}"
      shift 2
      ;;
    --no-history-rotate)
      ROTATE_HISTORY=0
      shift
      ;;
    --no-session-areas)
      RESOLVE_SESSION_AREAS=0
      shift
      ;;
    --readiness)
      METRIC_READINESS="${2:-}"
      shift 2
      ;;
    --review-result)
      METRIC_REVIEW_RESULT="${2:-}"
      shift 2
      ;;
    --rework)
      METRIC_REWORK="${2:-}"
      shift 2
      ;;
    --context-files)
      METRIC_CONTEXT_FILES="${2:-}"
      shift 2
      ;;
    --validate-cycles)
      METRIC_VALIDATE_CYCLES="${2:-}"
      shift 2
      ;;
    --review-cycles)
      METRIC_REVIEW_CYCLES="${2:-}"
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

if [[ -z "${WORK_ID}" ]]; then
  echo "Error: --work-id is required" >&2
  usage >&2
  exit 1
fi

if ! [[ "${HISTORY_LIMIT}" =~ ^[0-9]+$ ]] || [[ "${HISTORY_LIMIT}" -lt 1 ]]; then
  echo "Error: --history-limit must be a positive integer" >&2
  exit 1
fi

if [[ -n "${SUMMARY_FILE}" ]]; then
  if [[ "${SUMMARY_FILE}" == "-" ]]; then
    SUMMARY="$(cat)"
  else
    if [[ ! -f "${SUMMARY_FILE}" ]]; then
      echo "Summary file not found: ${SUMMARY_FILE}" >&2
      exit 1
    fi
    SUMMARY="$(<"${SUMMARY_FILE}")"
  fi
fi

if [[ -z "${SUMMARY}" ]]; then
  echo "Error: --summary or --summary-file is required" >&2
  usage >&2
  exit 1
fi

TARGET="$(sdlc_resolve_target "${TARGET}")"
timestamp="$(sdlc_timestamp_iso)"
safe_timestamp="$(sdlc_timestamp_file)"
session_day="$(sdlc_timestamp_day)"

memory_dir="${TARGET}/agent-context/memory"
# Lean stay-set memory is always primary (#83/#85/#86).
lean_memory_dir="${TARGET}/spdd/memory"
feature_dir="${TARGET}/agent-context/features/${WORK_ID}"
# Hot sessions (#85): .sdlc/sessions; legacy agent-context/sessions is fallback for reads.
session_dir="${TARGET}/.sdlc/sessions"
legacy_session_dir="${TARGET}/agent-context/sessions"
session_notes_dir="${TARGET}/session-notes"
session_entry_dir="${lean_memory_dir}/sessions"
archive_dir="${memory_dir}/archive"
if [[ "${DRY_RUN}" -eq 0 ]]; then
  mkdir -p "${memory_dir}" "${lean_memory_dir}/entries" "${lean_memory_dir}/sessions" \
    "${session_dir}" "${session_notes_dir}"
  # Do not create feature mirrors (#86).
fi

session_history="${memory_dir}/session-history.md"
session_index="${memory_dir}/session-index.md"
# Primary context index is lean; dual-write legacy for transition.
code_area_index="${lean_memory_dir}/context-index.md"
legacy_code_area_index="${memory_dir}/context-index.md"
session_entry_file="${session_entry_dir}/${safe_timestamp}-${WORK_ID}-${PHASE}.md"
archive_history="${archive_dir}/session-history.md"
project_memory="${memory_dir}/project-memory.md"
architecture_decisions="${memory_dir}/architecture-decisions.md"
known_pitfalls="${memory_dir}/known-pitfalls.md"
reusable_patterns="${memory_dir}/reusable-patterns.md"
prompt_optimization_log="${memory_dir}/prompt-optimization-log.md"
archive_ledger="${archive_dir}/prompt-optimization-log.md"
progress_log="${lean_memory_dir}/entries/progress.md"
current_session="${session_dir}/current-session.md"
if [[ ! -f "${current_session}" && -f "${legacy_session_dir}/current-session.md" ]]; then
  current_session="${legacy_session_dir}/current-session.md"
fi
# Also scan hot + legacy timestamped briefs for capture inputs.
_session_scan_dirs=("${session_dir}" "${legacy_session_dir}")
daily_session_note="${session_notes_dir}/${session_day}.md"
roadmap_file="${TARGET}/ROADMAP.md"

milestone_file="$(resolve_milestone "${TARGET}" "${WORK_ID}" "${MILESTONE}" absolute || true)"
milestone_rel=""
if [[ -n "${milestone_file}" ]]; then
  milestone_rel="${milestone_file#${TARGET}/}"
  if [[ -z "${MILESTONE}" ]]; then
    MILESTONE="${milestone_rel}"
  fi
fi

prepend_session_index_row() {
  # Maintain a newest-first index so agents can search history progressively
  # backward: the most recent session is always the first data row. Existing
  # rows are preserved below the new one.
  local row="$1"
  local header
  header="$(cat <<'IDX'
# Session Index

One row per captured session, newest first. Retrieve by relevance, not recency:
filter by Work ID or Area to find related sessions regardless of when they
happened, then read matches newest-first. For area-based lookup across Work IDs
see context-index.md. Full detail for each row lives in
agent-context/memory/sessions/<entry>.

| Timestamp | Work ID | Phase | Areas | Summary | Entry |
|-----------|---------|-------|-------|---------|-------|
IDX
)"
  local existing_rows=""
  if [[ -f "${session_index}" ]]; then
    existing_rows="$(awk '/^\| / && $0 !~ /^\| Timestamp/' "${session_index}")"
  fi
  {
    printf '%s\n' "${header}"
    printf '%s\n' "${row}"
    if [[ -n "${existing_rows}" ]]; then
      printf '%s\n' "${existing_rows}"
    fi
  } > "${session_index}"
}

rotate_session_history() {
  # Keep only the most recent ${limit} entries inline; move older entries to the
  # archive so the recent window stays small as the project grows.
  local file="$1"
  local limit="$2"
  local archive="$3"
  [[ -f "${file}" ]] || return 0
  local total
  total="$(grep -c '^### ' "${file}" 2>/dev/null || true)"
  total="${total:-0}"
  if (( total <= limit )); then
    return 0
  fi
  mkdir -p "$(dirname "${archive}")"
  if [[ ! -f "${archive}" ]]; then
    printf '# Session History Archive\n\nOlder session entries moved out of session-history.md to keep the recent window small. Newest archived entries are appended at the end.\n' > "${archive}"
  fi
  local tmp
  tmp="$(mktemp)"
  awk -v limit="${limit}" -v archive="${archive}" -v tmp="${tmp}" '
    /^### / { block++ }
    {
      if (block == 0) { preamble = preamble $0 "\n"; next }
      blocks[block] = blocks[block] $0 "\n"
    }
    END {
      total = block
      keep_from = total - limit + 1
      for (i = 1; i < keep_from; i++) printf "%s", blocks[i] >> archive
      printf "%s", preamble >> tmp
      for (i = keep_from; i <= total; i++) printf "%s", blocks[i] >> tmp
    }
  ' "${file}"
  mv "${tmp}" "${file}"
}

append_context_index_for_areas() {
  local kind="$1"
  local source="$2"
  local entry="$3"
  [[ "${areas_display}" == "none" ]] && return 0
  local rows=""
  for _a in "${areas[@]}"; do
    [[ -z "${_a}" ]] && continue
    rows+="| ${_a} | ${kind} | ${WORK_ID} | ${PHASE} | ${timestamp} | ${source} | ${entry} |"$'\n'
  done
  rows="${rows%$'\n'}"
  [[ -z "${rows}" ]] && return 0
  prepend_context_index_rows "${code_area_index}" "${rows}"
  # Dual-write legacy index during transition (Guide / older tools).
  prepend_context_index_rows "${legacy_code_area_index}" "${rows}"
}

# Code areas come from parsing session notes, not from manual --areas by default.
#
# Flow at capture:
#   1. Load the canonical category list (code-areas.md).
#   2. Collect current-session notes (summary, brief, canvas, progress log, etc.).
#   3. Match session text against known categories.
#   4. Parse session text for new path/package tokens → new categories.
#   5. Optional --areas override/supplement.
#   6. Append new categories to the registry.
known_areas_registry="${memory_dir}/code-areas.md"

normalize_content_for_match() {
  local c="$1"
  c="$(printf '%s' "${c}" | tr '[:upper:]' '[:lower:]')"
  c="$(printf '%s' "${c}" | tr '\n' ' ' | tr -s ' ')"
  printf '%s' "${c}"
}

declare -A _known_area_canonical=()
_known_area_order=()

load_area_registry() {
  _known_area_order=()
  if [[ -f "${known_areas_registry}" ]]; then
    while IFS= read -r _line; do
      [[ "${_line}" =~ ^-\ (.+)$ ]] || continue
      _canon="${BASH_REMATCH[1]}"
      _norm="$(normalize_area "${_canon}")"
      [[ -z "${_norm}" ]] && continue
      if [[ -z "${_known_area_canonical[${_norm}]:-}" ]]; then
        _known_area_canonical[${_norm}]="${_canon}"
        _known_area_order+=("${_canon}")
      fi
    done < "${known_areas_registry}"
  fi
}

collect_session_content() {
  local _parts=""
  _parts+="${SUMMARY}"$'\n'
  if [[ -f "${current_session}" ]]; then
    _parts+="$(<"${current_session}")"$'\n'
  fi
  # Include the full latest timestamped session brief (not just current-session.md)
  # so indexing has the entire last session context.
  local _latest_session_doc=""
  # Prefer hot .sdlc/sessions, then legacy agent-context/sessions (#85).
  _latest_session_doc="$(ls -1t "${session_dir}"/20*.md "${legacy_session_dir}"/20*.md 2>/dev/null | sed -n '1p' || true)"
  if [[ -n "${_latest_session_doc}" ]] && [[ -f "${_latest_session_doc}" ]]; then
    _parts+="$(<"${_latest_session_doc}")"$'\n'
  fi
  if [[ -f "${daily_session_note}" ]]; then
    _parts+="$(<"${daily_session_note}")"$'\n'
  fi
  local _canvas="${TARGET}/spdd/canvas/${WORK_ID}.md"
  local _feature_canvas="${feature_dir}/reasons-canvas.md"
  if [[ -f "${_canvas}" ]]; then
    _parts+="$(<"${_canvas}")"$'\n'
  elif [[ -f "${_feature_canvas}" ]]; then
    _parts+="$(<"${_feature_canvas}")"$'\n'
  fi
  if [[ -f "${progress_log}" ]]; then
    _parts+="$(tail -n 80 "${progress_log}" 2>/dev/null || true)"$'\n'
  fi
  local _analysis="${TARGET}/spdd/analysis/${WORK_ID}-analysis.md"
  local _feature_analysis="${feature_dir}/analysis-context.md"
  if [[ -f "${_analysis}" ]]; then
    _parts+="$(<"${_analysis}")"$'\n'
  elif [[ -f "${_feature_analysis}" ]]; then
    _parts+="$(<"${_feature_analysis}")"$'\n'
  fi
  if [[ -n "${VALIDATION}" ]]; then
    _parts+="${VALIDATION}"$'\n'
  fi
  if [[ -n "${DECISIONS}" ]]; then
    _parts+="${DECISIONS}"$'\n'
  fi
  if [[ -n "${PITFALLS}" ]]; then
    _parts+="${PITFALLS}"$'\n'
  fi
  if [[ -n "${PATTERNS}" ]]; then
    _parts+="${PATTERNS}"$'\n'
  fi
  printf '%s' "${_parts}"
}

area_path_excluded() {
  local norm="$1"
  case "${norm}" in
    agent-context/*|spdd/canvas/*|spdd/canvas|docs/*|docs/sdlc-spdd/*|session-notes/*|requirements/*|.cursor/*|.github/*|templates/*|examples/*)
      return 0 ;;
  esac
  case "${norm}" in
    src/main|src/test|src/main/java|src/test/java)
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
  # Drop prose punctuation captured next to inline paths, e.g. `src/payments`.
  token="${token%"${token##*[[:alnum:]_/-]}"}"
  token="${token#\`}"
  token="${token%\`}"
  [[ -z "${token}" ]] && return 0
  token="$(strip_path_filename "${token}")"
  [[ -z "${token}" ]] && return 0

  if [[ "${token}" =~ ^src/(main|test)/java/(.+)$ ]]; then
    local pkg="${BASH_REMATCH[2]}"
    pkg="${pkg//\//.}"
    printf '%s' "${pkg}"
    return 0
  fi

  if area_path_excluded "${token}"; then
    return 0
  fi

  if [[ "${token}" == */* ]]; then
    local first="${token%%/*}"
    local rest="${token#*/}"
    local second="${rest%%/*}"
    local bucket="${first}/${second}"
    if area_path_excluded "${bucket}"; then
      return 0
    fi
    printf '%s' "${bucket}"
  fi
}

is_plausible_java_package() {
  local pkg="$1"
  pkg="$(normalize_area "${pkg}")"
  [[ "${pkg}" == *.* ]] || return 1
  case "${pkg%%.*}" in
    com|org|net|io|dev|app|co|edu|gov|javax|kotlin|android|androidx)
      return 0 ;;
  esac
  return 1
}

extract_areas_from_session_content() {
  local content="$1"
  local token area

  while IFS= read -r token; do
    [[ -z "${token}" ]] && continue
    token="${token#\`}"
    token="${token%\`}"
    area="$(path_token_to_area "${token}")"
    [[ -n "${area}" ]] && printf '%s\n' "${area}"
  done < <(printf '%s' "${content}" | grep -oE '(src|scripts|tests|lib|pkg|internal|cmd|packages|modules)/[A-Za-z0-9_./-]+' 2>/dev/null || true)

  while IFS= read -r token; do
    [[ -z "${token}" ]] && continue
    if is_plausible_java_package "${token}"; then
      printf '%s\n' "$(normalize_area "${token}")"
    fi
  done < <(printf '%s' "${content}" | grep -oE '(com|org|net|io|dev|app|co)\.[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)+' 2>/dev/null || true)
}

match_known_areas_in_content() {
  local content_norm="$1"
  local _canon _norm
  for _canon in "${_known_area_order[@]}"; do
    _norm="$(normalize_area "${_canon}")"
    [[ -z "${_norm}" ]] && continue
    if [[ "${content_norm}" == *"${_norm}"* ]]; then
      printf '%s\n' "${_canon}"
    fi
  done
}

areas=()
new_areas=()
declare -A _resolved_norm=()

register_area_candidate() {
  local candidate="$1"
  [[ -z "${candidate}" ]] && return 0
  local _norm
  _norm="$(normalize_area "${candidate}")"
  [[ -z "${_norm}" ]] && return 0
  [[ -n "${_resolved_norm[${_norm}]:-}" ]] && return 0
  _resolved_norm[${_norm}]=1

  if [[ -n "${_known_area_canonical[${_norm}]:-}" ]]; then
    areas+=("${_known_area_canonical[${_norm}]}")
  else
    areas+=("${candidate}")
    new_areas+=("${candidate}")
    _known_area_canonical[${_norm}]="${candidate}"
    _known_area_order+=("${candidate}")
  fi
}

load_area_registry
_session_content="$(collect_session_content)"
_session_content_norm="$(normalize_content_for_match "${_session_content}")"

# Step 1: match session text against known categories.
if [[ "${RESOLVE_SESSION_AREAS}" -eq 1 ]] && [[ -n "${_session_content_norm}" ]]; then
  while IFS= read -r _matched; do
    [[ -z "${_matched}" ]] && continue
    register_area_candidate "${_matched}"
  done < <(match_known_areas_in_content "${_session_content_norm}")
fi

# Step 2: parse session documents/content for path/package tokens -> new categories.
if [[ "${RESOLVE_SESSION_AREAS}" -eq 1 ]] && [[ -n "${_session_content}" ]]; then
  while IFS= read -r _extracted; do
    [[ -z "${_extracted}" ]] && continue
    register_area_candidate "${_extracted}"
  done < <(extract_areas_from_session_content "${_session_content}")
fi

# Step 3: optional --areas override/supplement.
if [[ -n "${AREAS}" ]]; then
  IFS=', ' read -ra _areas_raw <<< "${AREAS}"
  for _a in "${_areas_raw[@]}"; do
    register_area_candidate "${_a}"
  done
fi

areas_display=""
for _a in "${areas[@]:-}"; do
  [[ -z "${_a}" ]] && continue
  areas_display+="${_a}, "
done
areas_display="${areas_display%, }"
[[ -z "${areas_display}" ]] && areas_display="none"

# Optional capture metrics (FEAT-004 T02). Invalid values warn and are skipped.
METRIC_PARTS=()
if [[ -n "${METRIC_REVIEW_RESULT}" ]]; then
  case "${METRIC_REVIEW_RESULT}" in
    pass|fail|mixed|blocked) ;;
    *)
      echo "Warning: --review-result '${METRIC_REVIEW_RESULT}' is not pass|fail|mixed|blocked; skipping." >&2
      METRIC_REVIEW_RESULT=""
      ;;
  esac
fi
if [[ -n "${METRIC_REWORK}" ]]; then
  if ! [[ "${METRIC_REWORK}" =~ ^[0-9]+$ ]]; then
    echo "Warning: --rework '${METRIC_REWORK}' must be a non-negative integer; skipping." >&2
    METRIC_REWORK=""
  fi
fi
if [[ -n "${METRIC_CONTEXT_FILES}" ]]; then
  if ! [[ "${METRIC_CONTEXT_FILES}" =~ ^[0-9]+$ ]]; then
    echo "Warning: --context-files '${METRIC_CONTEXT_FILES}' must be a non-negative integer; skipping." >&2
    METRIC_CONTEXT_FILES=""
  fi
fi
if [[ -n "${METRIC_VALIDATE_CYCLES}" ]]; then
  if ! [[ "${METRIC_VALIDATE_CYCLES}" =~ ^[0-9]+$ ]]; then
    echo "Warning: --validate-cycles '${METRIC_VALIDATE_CYCLES}' must be a non-negative integer; skipping." >&2
    METRIC_VALIDATE_CYCLES=""
  fi
fi
if [[ -n "${METRIC_REVIEW_CYCLES}" ]]; then
  if ! [[ "${METRIC_REVIEW_CYCLES}" =~ ^[0-9]+$ ]]; then
    echo "Warning: --review-cycles '${METRIC_REVIEW_CYCLES}' must be a non-negative integer; skipping." >&2
    METRIC_REVIEW_CYCLES=""
  fi
fi
# Auto-fill readiness from canvas when the caller did not pass --readiness.
if [[ -z "${METRIC_READINESS}" ]]; then
  _canvas_for_metric="${TARGET}/spdd/canvas/${WORK_ID}.md"
  if [[ ! -f "${_canvas_for_metric}" ]]; then
    _canvas_for_metric="${TARGET}/agent-context/features/${WORK_ID}/reasons-canvas.md"
  fi
  if [[ -f "${_canvas_for_metric}" ]]; then
    METRIC_READINESS="$(canvas_readiness "${_canvas_for_metric}" || true)"
  fi
  unset _canvas_for_metric
fi
[[ -n "${METRIC_READINESS}" ]] && METRIC_PARTS+=("readiness=$(sdlc_oneline "${METRIC_READINESS}" 80)")
[[ -n "${METRIC_REVIEW_RESULT}" ]] && METRIC_PARTS+=("review-result=${METRIC_REVIEW_RESULT}")
[[ -n "${METRIC_REWORK}" ]] && METRIC_PARTS+=("rework=${METRIC_REWORK}")
[[ -n "${METRIC_CONTEXT_FILES}" ]] && METRIC_PARTS+=("context-files=${METRIC_CONTEXT_FILES}")
[[ -n "${METRIC_VALIDATE_CYCLES}" ]] && METRIC_PARTS+=("validate-cycles=${METRIC_VALIDATE_CYCLES}")
[[ -n "${METRIC_REVIEW_CYCLES}" ]] && METRIC_PARTS+=("review-cycles=${METRIC_REVIEW_CYCLES}")
METRIC_ENTRY=""
if ((${#METRIC_PARTS[@]} > 0)); then
  local_ifs="${IFS}"
  IFS='; '
  METRIC_ENTRY="${METRIC_PARTS[*]}"
  IFS="${local_ifs}"
fi

sdlc_ensure_file "${session_history}" "Session History" "${DRY_RUN}"
sdlc_ensure_file "${project_memory}" "Project Memory" "${DRY_RUN}"
sdlc_ensure_file "${architecture_decisions}" "Architecture Decisions" "${DRY_RUN}"
sdlc_ensure_file "${known_pitfalls}" "Known Pitfalls" "${DRY_RUN}"
sdlc_ensure_file "${reusable_patterns}" "Reusable Patterns" "${DRY_RUN}"
sdlc_ensure_file "${progress_log}" "Progress Log: ${WORK_ID}" "${DRY_RUN}"
if [[ "${WRITE_SESSION_NOTE}" -eq 1 ]]; then
  sdlc_ensure_file "${daily_session_note}" "Session Notes: ${session_day}" "${DRY_RUN}"
fi

metric_line=""
if [[ -n "${METRIC_ENTRY}" ]]; then
  metric_line=$'\n'"- Metrics: ${METRIC_ENTRY}"
fi

entry="$(cat <<EOF

### ${timestamp} - ${WORK_ID} - ${PHASE}

- Summary: ${SUMMARY}
- Code areas: ${areas_display}
- Validation: ${VALIDATION:-Not recorded}
- Decisions: ${DECISIONS:-None}
- Pitfalls: ${PITFALLS:-None}
- Reusable patterns: ${PATTERNS:-None}
- Milestone: ${MILESTONE:-None}
- Roadmap note: ${ROADMAP_NOTE:-None}
- Next: ${NEXT_STEP:-Not recorded}${metric_line}
EOF
)"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "${entry}"
  if [[ -n "${METRIC_ENTRY}" && "${areas_display}" != "none" ]]; then
    echo
    echo "# dry-run context-index metric rows (Kind: metric)"
    for _a in "${areas[@]}"; do
      [[ -z "${_a}" ]] && continue
      echo "| ${_a} | metric | ${WORK_ID} | ${PHASE} | ${timestamp} | capture-metrics | ${METRIC_ENTRY} |"
    done
  fi
  exit 0
fi

printf '%s\n' "${entry}" >> "${session_history}"
printf '%s\n' "${entry}" >> "${progress_log}"

# Durable per-session entry (granular, immutable) the index points at — lean primary.
{
  printf '# Session: %s - %s\n' "${WORK_ID}" "${PHASE}"
  printf '%s\n' "${entry}"
} > "${session_entry_file}"
# Dual-write legacy memory/sessions for transition harnesses.
mkdir -p "${memory_dir}/sessions"
cp "${session_entry_file}" "${memory_dir}/sessions/$(basename "${session_entry_file}")"

# Newest-first session index row, retrievable by Work ID or Area.
index_row="| ${timestamp} | ${WORK_ID} | ${PHASE} | $(sdlc_oneline "${areas_display}" 80) | $(sdlc_oneline "${SUMMARY}") | sessions/$(basename "${session_entry_file}") |"
prepend_session_index_row "${index_row}"

# Context index: one row per area for each artifact type touched this session.
_session_entry_rel="sessions/$(basename "${session_entry_file}")"
_section_anchor="### ${timestamp} - ${WORK_ID}"
if [[ "${areas_display}" != "none" ]]; then
  append_context_index_for_areas "session" "spdd/canvas/${WORK_ID}.md" "${_session_entry_rel}"
fi

if [[ -n "${METRIC_ENTRY}" && "${areas_display}" != "none" ]]; then
  append_context_index_for_areas "metric" "capture-metrics" "${METRIC_ENTRY}"
fi

# Grow the canonical category registry with areas not previously seen.
if [[ ${#new_areas[@]} -gt 0 ]]; then
  if [[ ! -f "${known_areas_registry}" ]]; then
    cat > "${known_areas_registry}" <<'AREAS'
# Code Areas

Canonical list of code areas (categories) seen across sessions. At capture the
script loads this list, collects session documents/content (summary,
session-notes, current-session.md, latest timestamped session brief, canvas,
progress log), matches known categories, and parses path/package tokens to
create new ones. Optional --areas can override or supplement parsed areas.
This keeps context-index.md consistent instead of fragmenting into near-duplicate areas.

AREAS
  fi
  for _a in "${new_areas[@]}"; do
    printf -- '- %s\n' "${_a}" >> "${known_areas_registry}"
  done
fi

# Bound the recent window unless the caller opted out.
if [[ "${ROTATE_HISTORY}" -eq 1 ]]; then
  rotate_session_history "${session_history}" "${HISTORY_LIMIT}" "${archive_history}"
  # Same rotation pattern for the prompt-optimization ledger (FEAT-004 T04).
  if [[ -f "${prompt_optimization_log}" ]]; then
    rotate_session_history "${prompt_optimization_log}" "${HISTORY_LIMIT}" "${archive_ledger}"
  fi
fi

if [[ "${WRITE_SESSION_NOTE}" -eq 1 ]]; then
  printf '%s\n' "${entry}" >> "${daily_session_note}"
fi

{
  echo
  echo "### ${timestamp} - ${WORK_ID}"
  echo
  echo "- Phase: ${PHASE}"
  echo "- Summary: ${SUMMARY}"
  echo "- Next: ${NEXT_STEP:-Not recorded}"
} >> "${project_memory}"

if [[ -n "${DECISIONS}" ]]; then
  {
    echo
    echo "${_section_anchor}"
    echo
    echo "- Code areas: ${areas_display}"
    echo "- Status: Accepted"
    echo "- Context: Captured during ${PHASE} session."
    echo "- Decision: ${DECISIONS}"
    echo "- Consequences: Review future work against this decision."
  } >> "${architecture_decisions}"
  append_context_index_for_areas "decision" "architecture-decisions.md" "${_section_anchor}"
fi

if [[ -n "${PITFALLS}" ]]; then
  {
    echo
    echo "${_section_anchor}"
    echo
    echo "- Code areas: ${areas_display}"
    echo "- ${PITFALLS}"
  } >> "${known_pitfalls}"
  append_context_index_for_areas "pitfall" "known-pitfalls.md" "${_section_anchor}"
fi

if [[ -n "${PATTERNS}" ]]; then
  {
    echo
    echo "${_section_anchor}"
    echo
    echo "- Code areas: ${areas_display}"
    echo "- ${PATTERNS}"
  } >> "${reusable_patterns}"
  append_context_index_for_areas "pattern" "reusable-patterns.md" "${_section_anchor}"
fi

if [[ -n "${milestone_file}" ]]; then
  sdlc_ensure_file "${milestone_file}" "$(basename "${milestone_file}" .md)" "${DRY_RUN}"
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
  sdlc_ensure_file "${roadmap_file}" "Roadmap" "${DRY_RUN}"
  {
    echo
    echo "### ${timestamp} - ${WORK_ID} - ${PHASE}"
    echo
    echo "- ${ROADMAP_NOTE}"
    echo "- Summary: ${SUMMARY}"
    echo "- Next: ${NEXT_STEP:-Not recorded}"
  } >> "${roadmap_file}"
fi

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

workflow_script="${TARGET}/agent-context/sdlc-workflow.sh"
if [[ -f "${workflow_script}" ]]; then
  SDLC_ROOT="${TARGET}"
  # shellcheck source=/dev/null
  source "${workflow_script}"
  sdlc_workflow_record_capture "${WORK_ID}" "${PHASE}"
fi

echo "Captured session memory:"
echo "  ${session_history}"
echo "  ${session_entry_file}"
echo "  ${session_index}"
if [[ "${areas_display}" != "none" ]]; then
  echo "  ${code_area_index}"
  echo "  ${known_areas_registry}"
fi
echo "  ${progress_log}"
if [[ "${WRITE_SESSION_NOTE}" -eq 1 ]]; then
  echo "  ${daily_session_note}"
fi
if [[ -n "${milestone_file}" ]]; then
  echo "  ${milestone_file}"
fi
if [[ -n "${ROADMAP_NOTE}" ]]; then
  echo "  ${roadmap_file}"
fi
echo "Updated durable memory as applicable."
echo
echo "Planning capture prompt standard: docs/sdlc-spdd/planning-prompt-standard.md"
if [[ -n "${milestone_rel}" ]]; then
  echo "Active milestone: ${milestone_rel}"
fi
if [[ -z "${milestone_rel}" ]]; then
  echo "No milestone linked. Add --milestone milestone-1.md when work belongs to a milestone."
fi
if [[ -z "${ROADMAP_NOTE}" ]]; then
  echo "Tip: add --roadmap-note \"<progress>\" to update @ROADMAP.md Current Focus."
else
  echo
  echo "Review roadmap focus:"
  echo "  Read @ROADMAP.md. Does Current Focus match Work ID ${WORK_ID} and next step: ${NEXT_STEP:-Not recorded}?"
fi
