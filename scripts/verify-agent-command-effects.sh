#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: verify-agent-command-effects.sh --target <path> --work-id <WORK-ID> --step <step> [--operation <Txx>] [--milestone <file>] [--require-roadmap]

Best-effort verification that an assistant command was invoked and produced
expected repository artifacts. This checks deterministic side-effects only.

Steps:
  init           Verify SDLC-SPDD scaffold and memory files
  plan           Verify canvas + feature workspace artifacts
  architect      Verify plan artifacts + readiness marker in canvas
  code           Verify progress log includes operation/activity evidence
  review         Verify review artifacts and status marker
  prompt-update  Verify canvas + progress artifacts for updated intent
  sync           Verify sync artifacts
  retro          Verify retro + durable memory artifacts
  capture        Verify session-memory + planning sync artifacts after capture-session-memory.sh

Examples:
  ./scripts/verify-agent-command-effects.sh --target . --work-id FEAT-001-foo --step plan
  ./scripts/verify-agent-command-effects.sh --target . --work-id FEAT-001-foo --step code --operation T01
  ./scripts/verify-agent-command-effects.sh --target . --work-id FEAT-001-foo --step capture --milestone milestone-1.md --require-roadmap
EOF
}

TARGET="."
WORK_ID=""
STEP=""
OPERATION="T01"
MILESTONE=""
REQUIRE_ROADMAP=0

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
    --step)
      STEP="${2:-}"
      shift 2
      ;;
    --operation)
      OPERATION="${2:-}"
      shift 2
      ;;
    --milestone)
      MILESTONE="${2:-}"
      shift 2
      ;;
    --require-roadmap)
      REQUIRE_ROADMAP=1
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

if [[ -z "${WORK_ID}" || -z "${STEP}" ]]; then
  echo "Error: --work-id and --step are required" >&2
  usage >&2
  exit 1
fi

case "${STEP}" in
  init|plan|architect|code|review|prompt-update|sync|retro|capture) ;;
  *)
    echo "Unsupported --step '${STEP}'" >&2
    usage >&2
    exit 1
    ;;
esac

TARGET="$(cd "${TARGET}" && pwd)"
FEATURE_DIR="${TARGET}/agent-context/features/${WORK_ID}"
CANVAS="${TARGET}/spdd/canvas/${WORK_ID}.md"

failures=0

check_exists() {
  local label="$1"
  local path="$2"
  if [[ -e "${path}" ]]; then
    echo "  ok  ${label}: ${path}"
  else
    echo "  FAIL ${label}: ${path}" >&2
    failures=$((failures + 1))
  fi
}

check_contains_regex() {
  local label="$1"
  local path="$2"
  local regex="$3"
  if [[ ! -f "${path}" ]]; then
    echo "  FAIL ${label}: ${path} (missing file)" >&2
    failures=$((failures + 1))
    return
  fi
  if grep -Eq "${regex}" "${path}"; then
    echo "  ok  ${label}: ${path}"
  else
    echo "  FAIL ${label}: ${path} (pattern not found: ${regex})" >&2
    failures=$((failures + 1))
  fi
}

check_any_session_note_contains_work_id() {
  local notes_dir="$1"
  if [[ ! -d "${notes_dir}" ]]; then
    echo "  FAIL session-notes directory: ${notes_dir}" >&2
    failures=$((failures + 1))
    return
  fi
  if grep -Rqs "${WORK_ID}" "${notes_dir}"; then
    echo "  ok  session-notes mention work-id: ${WORK_ID}"
  else
    echo "  FAIL session-notes mention work-id: ${WORK_ID} (run capture-session-memory.sh with --summary/--milestone)" >&2
    failures=$((failures + 1))
  fi
}

echo "Verifying command effects"
echo "  target: ${TARGET}"
echo "  work-id: ${WORK_ID}"
echo "  step: ${STEP}"
echo

if [[ "${STEP}" == "init" ]]; then
  check_exists "requirements dir" "${TARGET}/requirements"
  check_exists "spdd dir" "${TARGET}/spdd"
  check_exists "agent-context dir" "${TARGET}/agent-context"
  check_exists "project memory" "${TARGET}/agent-context/memory/project-memory.md"
  check_exists "quality gates" "${TARGET}/agent-context/harness/quality-gates.md"
fi

if [[ "${STEP}" == "plan" || "${STEP}" == "architect" || "${STEP}" == "code" || "${STEP}" == "review" || "${STEP}" == "prompt-update" || "${STEP}" == "sync" || "${STEP}" == "retro" || "${STEP}" == "capture" ]]; then
  check_exists "canvas" "${CANVAS}"
  check_exists "feature dir" "${FEATURE_DIR}"
  check_exists "feature requirement" "${FEATURE_DIR}/requirement.md"
  check_exists "progress log" "${FEATURE_DIR}/progress-log.md"
fi

if [[ "${STEP}" == "plan" || "${STEP}" == "architect" || "${STEP}" == "prompt-update" ]]; then
  check_contains_regex "canvas operations section" "${CANVAS}" "^## O - Operations"
  check_contains_regex "canvas safeguards section" "${CANVAS}" "^## S - Safeguards"
fi

if [[ "${STEP}" == "architect" ]]; then
  check_contains_regex "architect readiness marker" "${CANVAS}" "Ready For Coding|Needs Clarification|Needs Redesign|Blocked"
fi

if [[ "${STEP}" == "code" ]]; then
  check_contains_regex "progress log operation evidence" "${FEATURE_DIR}/progress-log.md" "${OPERATION}|[Ii]mplement|[Cc]omplete|[Ff]iles changed"
fi

if [[ "${STEP}" == "review" ]]; then
  check_exists "feature review" "${FEATURE_DIR}/review.md"
  check_exists "spdd review" "${TARGET}/spdd/reviews/${WORK_ID}-review.md"
  check_contains_regex "review status marker" "${FEATURE_DIR}/review.md" "Approved|Approved With Notes|Changes Requested|Blocked"
fi

if [[ "${STEP}" == "sync" ]]; then
  check_exists "feature sync log" "${FEATURE_DIR}/sync-log.md"
  check_exists "spdd sync report" "${TARGET}/spdd/sync/${WORK_ID}-sync.md"
fi

if [[ "${STEP}" == "retro" ]]; then
  check_exists "feature retro" "${FEATURE_DIR}/retro.md"
  check_exists "known pitfalls memory" "${TARGET}/agent-context/memory/known-pitfalls.md"
  check_exists "reusable patterns memory" "${TARGET}/agent-context/memory/reusable-patterns.md"
fi

if [[ "${STEP}" == "capture" ]]; then
  check_exists "session history memory" "${TARGET}/agent-context/memory/session-history.md"
  check_any_session_note_contains_work_id "${TARGET}/session-notes"
  # capture-session-memory.sh always appends a "### <ts> - <WORK-ID> - <phase>"
  # header to the progress log, so the Work ID is a deterministic anchor here.
  check_contains_regex "progress log mention work-id" "${FEATURE_DIR}/progress-log.md" "${WORK_ID}"

  if [[ -n "${MILESTONE}" ]]; then
    check_contains_regex "milestone mention work-id" "${TARGET}/${MILESTONE}" "${WORK_ID}"
  fi
  if [[ "${REQUIRE_ROADMAP}" -eq 1 ]]; then
    check_contains_regex "roadmap mention work-id" "${TARGET}/ROADMAP.md" "${WORK_ID}"
  fi
fi

echo
if [[ "${failures}" -gt 0 ]]; then
  echo "Verification failed with ${failures} issue(s)." >&2
  exit 1
fi
echo "Verification passed."
