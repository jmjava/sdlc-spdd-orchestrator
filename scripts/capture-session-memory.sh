#!/usr/bin/env bash
set -euo pipefail

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
  --areas <text>        Code areas this session touched (space- or comma-separated),
                        as determined by the agent from the prose REASONS Canvas and
                        the code it matched (e.g. a Java package or a directory).
                        Drives the reverse code-area index used for relevance-based
                        retrieval. Omit when not yet known.
  --milestone <path>    Milestone doc to append, such as milestone-1.md. When
                        omitted, searches milestone-*.md for the Work ID.
  --roadmap-note <text> Append a progress note to ROADMAP.md
  --no-session-note     Do not write session-notes/YYYY-MM-DD.md
  --next <text>         Next recommended command or action
  --history-limit <n>   Keep at most n recent entries inline in session-history.md;
                        older entries move to agent-context/memory/archive/ (default 20)
  --no-history-rotate   Keep session-history.md append-only (do not rotate/archive)
  --dry-run             Print the memory entry without writing files
  --help                Print this help message

Examples:
  ./scripts/capture-session-memory.sh --work-id FEAT-001-order-status-api --phase code --summary "Implemented T01" --validation "mvn test" --next "/sdlc-spdd-review @spdd/canvas/FEAT-001-order-status-api.md"
  ./scripts/capture-session-memory.sh --work-id BUG-003-null-discount --summary-file notes.md --pitfalls "Discount can be null in legacy orders"
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
DRY_RUN=0

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

TARGET="$(cd "${TARGET}" && pwd)"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
safe_timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
session_day="$(date -u +"%Y-%m-%d")"

memory_dir="${TARGET}/agent-context/memory"
feature_dir="${TARGET}/agent-context/features/${WORK_ID}"
session_dir="${TARGET}/agent-context/sessions"
session_notes_dir="${TARGET}/session-notes"
session_entry_dir="${memory_dir}/sessions"
archive_dir="${memory_dir}/archive"
if [[ "${DRY_RUN}" -eq 0 ]]; then
  mkdir -p "${memory_dir}" "${feature_dir}" "${session_dir}" "${session_notes_dir}" "${session_entry_dir}"
fi

session_history="${memory_dir}/session-history.md"
session_index="${memory_dir}/session-index.md"
code_area_index="${memory_dir}/code-area-index.md"
session_entry_file="${session_entry_dir}/${safe_timestamp}-${WORK_ID}-${PHASE}.md"
archive_history="${archive_dir}/session-history.md"
project_memory="${memory_dir}/project-memory.md"
architecture_decisions="${memory_dir}/architecture-decisions.md"
known_pitfalls="${memory_dir}/known-pitfalls.md"
reusable_patterns="${memory_dir}/reusable-patterns.md"
progress_log="${feature_dir}/progress-log.md"
current_session="${session_dir}/current-session.md"
daily_session_note="${session_notes_dir}/${session_day}.md"
roadmap_file="${TARGET}/ROADMAP.md"

resolve_milestone() {
  local candidate="${1:-}"
  if [[ -n "${candidate}" ]]; then
    if [[ "${candidate}" != *.md ]]; then
      candidate="${candidate}.md"
    fi
    if [[ -f "${TARGET}/${candidate}" ]]; then
      echo "${TARGET}/${candidate}"
      return 0
    fi
    if [[ -f "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
    echo ""
    return 1
  fi

  shopt -s nullglob
  local milestone_files=("${TARGET}"/milestone-*.md)
  shopt -u nullglob
  for file in "${milestone_files[@]}"; do
    if grep -q "${WORK_ID}" "${file}" 2>/dev/null; then
      echo "${file}"
      return 0
    fi
  done
  echo ""
  return 1
}

milestone_file="$(resolve_milestone "${MILESTONE}" || true)"
milestone_rel=""
if [[ -n "${milestone_file}" ]]; then
  milestone_rel="${milestone_file#${TARGET}/}"
  if [[ -z "${MILESTONE}" ]]; then
    MILESTONE="${milestone_rel}"
  fi
fi

ensure_file() {
  local path="$1"
  local title="$2"
  if [[ ! -f "${path}" ]]; then
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      echo "[dry-run] would create ${path}"
    else
      mkdir -p "$(dirname "${path}")"
      printf '# %s\n\n' "${title}" > "${path}"
    fi
  fi
}

oneline() {
  # Collapse newlines/whitespace, drop table-breaking pipes, and truncate so the
  # index stays compact and scannable.
  local text="$1"
  local max="${2:-100}"
  text="$(printf '%s' "${text}" | tr '\n|' ' /' | tr -s ' ')"
  text="${text# }"
  text="${text% }"
  if (( ${#text} > max )); then
    text="${text:0:max}..."
  fi
  printf '%s' "${text}"
}

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
see code-area-index.md. Full detail for each row lives in
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

prepend_code_area_index_rows() {
  # Reverse index: code area -> work/sessions that touched it. Newest rows first.
  # Areas are determined by the agent (which maps the prose REASONS Canvas to the
  # code it matched) and passed via --areas; this script only records them.
  local new_rows="$1"
  local header
  header="$(cat <<'CAI'
# Code Area Index

Maps code areas to the work and sessions that touched them. The agent determines
each session's areas by matching the prose REASONS Canvas to the code (a Java
package or a directory). Find the area you are about to work in, then read the
linked canvas and session entry - regardless of Work ID or when the work happened.
Newest first.

| Area | Work ID | Phase | Timestamp | Canvas | Entry |
|------|---------|-------|-----------|--------|-------|
CAI
)"
  local existing_rows=""
  if [[ -f "${code_area_index}" ]]; then
    existing_rows="$(awk '/^\| / && $0 !~ /^\| Area/' "${code_area_index}")"
  fi
  {
    printf '%s\n' "${header}"
    printf '%s\n' "${new_rows}"
    if [[ -n "${existing_rows}" ]]; then
      printf '%s\n' "${existing_rows}"
    fi
  } > "${code_area_index}"
}

# Code areas this session touched, as determined by the agent and passed via
# --areas. The canvas is prose; the agent maps it to code. No canvas parsing here.
areas=()
if [[ -n "${AREAS}" ]]; then
  IFS=', ' read -ra _areas_raw <<< "${AREAS}"
  declare -A _seen_area=()
  for _a in "${_areas_raw[@]}"; do
    [[ -z "${_a}" ]] && continue
    if [[ -z "${_seen_area[${_a}]:-}" ]]; then
      _seen_area[${_a}]=1
      areas+=("${_a}")
    fi
  done
fi

areas_display=""
for _a in "${areas[@]:-}"; do
  [[ -z "${_a}" ]] && continue
  areas_display+="${_a}, "
done
areas_display="${areas_display%, }"
[[ -z "${areas_display}" ]] && areas_display="none"

ensure_file "${session_history}" "Session History"
ensure_file "${project_memory}" "Project Memory"
ensure_file "${architecture_decisions}" "Architecture Decisions"
ensure_file "${known_pitfalls}" "Known Pitfalls"
ensure_file "${reusable_patterns}" "Reusable Patterns"
ensure_file "${progress_log}" "Progress Log: ${WORK_ID}"
if [[ "${WRITE_SESSION_NOTE}" -eq 1 ]]; then
  ensure_file "${daily_session_note}" "Session Notes: ${session_day}"
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
- Next: ${NEXT_STEP:-Not recorded}
EOF
)"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "${entry}"
  exit 0
fi

printf '%s\n' "${entry}" >> "${session_history}"
printf '%s\n' "${entry}" >> "${progress_log}"

# Durable per-session entry (granular, immutable) the index points at.
{
  printf '# Session: %s - %s\n' "${WORK_ID}" "${PHASE}"
  printf '%s\n' "${entry}"
} > "${session_entry_file}"

# Newest-first session index row, retrievable by Work ID or Area.
index_row="| ${timestamp} | ${WORK_ID} | ${PHASE} | $(oneline "${areas_display}" 80) | $(oneline "${SUMMARY}") | sessions/$(basename "${session_entry_file}") |"
prepend_session_index_row "${index_row}"

# Reverse code-area index: one row per area this session touched. Populated only
# once the canvas declares real files (post-architect); empty/TBD canvases add
# nothing here.
if [[ "${areas_display}" != "none" ]]; then
  area_rows=""
  for _a in "${areas[@]}"; do
    [[ -z "${_a}" ]] && continue
    area_rows+="| ${_a} | ${WORK_ID} | ${PHASE} | ${timestamp} | spdd/canvas/${WORK_ID}.md | sessions/$(basename "${session_entry_file}") |"$'\n'
  done
  area_rows="${area_rows%$'\n'}"
  if [[ -n "${area_rows}" ]]; then
    prepend_code_area_index_rows "${area_rows}"
  fi
fi

# Bound the recent window unless the caller opted out.
if [[ "${ROTATE_HISTORY}" -eq 1 ]]; then
  rotate_session_history "${session_history}" "${HISTORY_LIMIT}" "${archive_history}"
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
    echo "### ${timestamp} - ${WORK_ID}"
    echo
    echo "- Status: Accepted"
    echo "- Context: Captured during ${PHASE} session."
    echo "- Decision: ${DECISIONS}"
    echo "- Consequences: Review future work against this decision."
  } >> "${architecture_decisions}"
fi

if [[ -n "${PITFALLS}" ]]; then
  {
    echo
    echo "### ${timestamp} - ${WORK_ID}"
    echo
    echo "- ${PITFALLS}"
  } >> "${known_pitfalls}"
fi

if [[ -n "${PATTERNS}" ]]; then
  {
    echo
    echo "### ${timestamp} - ${WORK_ID}"
    echo
    echo "- ${PATTERNS}"
  } >> "${reusable_patterns}"
fi

if [[ -n "${milestone_file}" ]]; then
  ensure_file "${milestone_file}" "$(basename "${milestone_file}" .md)"
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
  ensure_file "${roadmap_file}" "Roadmap"
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

echo "Captured session memory:"
echo "  ${session_history}"
echo "  ${session_entry_file}"
echo "  ${session_index}"
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
