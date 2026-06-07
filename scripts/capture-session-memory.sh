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
  --milestone <path>    Milestone doc to append, such as milestone-1.md. When
                        omitted, searches milestone-*.md for the Work ID.
  --roadmap-note <text> Append a progress note to ROADMAP.md
  --no-session-note     Do not write session-notes/YYYY-MM-DD.md
  --next <text>         Next recommended command or action
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
MILESTONE=""
ROADMAP_NOTE=""
NEXT_STEP=""
WRITE_SESSION_NOTE=1
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
session_day="$(date -u +"%Y-%m-%d")"

memory_dir="${TARGET}/agent-context/memory"
feature_dir="${TARGET}/agent-context/features/${WORK_ID}"
session_dir="${TARGET}/agent-context/sessions"
session_notes_dir="${TARGET}/session-notes"
if [[ "${DRY_RUN}" -eq 0 ]]; then
  mkdir -p "${memory_dir}" "${feature_dir}" "${session_dir}" "${session_notes_dir}"
fi

session_history="${memory_dir}/session-history.md"
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
