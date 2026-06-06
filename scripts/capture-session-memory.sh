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
NEXT_STEP=""
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
    --next)
      NEXT_STEP="${2:-}"
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

memory_dir="${TARGET}/agent-context/memory"
feature_dir="${TARGET}/agent-context/features/${WORK_ID}"
session_dir="${TARGET}/agent-context/sessions"
mkdir -p "${memory_dir}" "${feature_dir}" "${session_dir}"

session_history="${memory_dir}/session-history.md"
project_memory="${memory_dir}/project-memory.md"
architecture_decisions="${memory_dir}/architecture-decisions.md"
known_pitfalls="${memory_dir}/known-pitfalls.md"
reusable_patterns="${memory_dir}/reusable-patterns.md"
progress_log="${feature_dir}/progress-log.md"
current_session="${session_dir}/current-session.md"

ensure_file() {
  local path="$1"
  local title="$2"
  if [[ ! -f "${path}" ]]; then
    printf '# %s\n\n' "${title}" > "${path}"
  fi
}

ensure_file "${session_history}" "Session History"
ensure_file "${project_memory}" "Project Memory"
ensure_file "${architecture_decisions}" "Architecture Decisions"
ensure_file "${known_pitfalls}" "Known Pitfalls"
ensure_file "${reusable_patterns}" "Reusable Patterns"
ensure_file "${progress_log}" "Progress Log: ${WORK_ID}"

entry="$(cat <<EOF

### ${timestamp} - ${WORK_ID} - ${PHASE}

- Summary: ${SUMMARY}
- Validation: ${VALIDATION:-Not recorded}
- Decisions: ${DECISIONS:-None}
- Pitfalls: ${PITFALLS:-None}
- Reusable patterns: ${PATTERNS:-None}
- Next: ${NEXT_STEP:-Not recorded}
EOF
)"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "${entry}"
  exit 0
fi

printf '%s\n' "${entry}" >> "${session_history}"
printf '%s\n' "${entry}" >> "${progress_log}"

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
echo "Updated durable memory as applicable."
