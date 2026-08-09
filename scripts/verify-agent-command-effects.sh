#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"

usage() {
  cat <<'EOF'
Usage: verify-agent-command-effects.sh --target <path> --work-id <WORK-ID> --step <step> [--operation <Txx>] [--milestone <file>] [--require-roadmap]

Best-effort verification that an assistant command was invoked and produced
expected repository artifacts (storage v3: single sdlc-spdd/ home, lessons
ledger + staged captures). This checks deterministic side-effects only.

Steps:
  init           Verify SDLC-SPDD home scaffold and memory ledgers
  plan           Verify canvas + requirement artifacts
  architect      Verify plan artifacts + readiness marker in canvas
  code           Verify session evidence for the operation in staged/ledger records
  review         Verify review artifacts and status marker
  prompt-update  Verify canvas + captured evidence for updated intent
  sync           Verify sync artifacts
  retro          Verify retro evidence (accepted lessons in the committed ledger)
  capture        Verify staged session records after capture-session-memory.sh

When the sdlc-engine Python CLI is importable, `sdlc-engine context parity`
also runs as an extra consistency check (skipped otherwise).

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

TARGET="$(sdlc_resolve_target "${TARGET}")"
export SDLC_ROOT="${TARGET}"
HOME_DIR="$(sdlc_home "${TARGET}")"
CANVAS="${HOME_DIR}/spdd/canvas/${WORK_ID}.md"
MILESTONE_REQ="${HOME_DIR}/requirements/milestones/${WORK_ID}.md"
SPDD_REVIEW="${HOME_DIR}/spdd/reviews/${WORK_ID}-review.md"
SPDD_SYNC="${HOME_DIR}/spdd/sync/${WORK_ID}-sync.md"
LEDGER="$(sdlc_ledger "${TARGET}")"
STAGE="$(sdlc_stage "${TARGET}")"

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

# Session/lesson evidence lives in JSONL records: staged captures first
# (.sdlc/staged/lessons.jsonl), then the committed ledger after accept.
check_records_contain_regex() {
  local label="$1"
  local regex="$2"
  local path
  for path in "${STAGE}" "${LEDGER}"; do
    if [[ -f "${path}" ]] && grep -Eq "${regex}" "${path}"; then
      echo "  ok  ${label}: ${path}"
      return
    fi
  done
  echo "  FAIL ${label}: no staged or committed record matches: ${regex}" >&2
  echo "        (stage: ${STAGE}; ledger: ${LEDGER})" >&2
  failures=$((failures + 1))
}

check_ledger_contains_regex() {
  local label="$1"
  local regex="$2"
  if [[ -f "${LEDGER}" ]] && grep -Eq "${regex}" "${LEDGER}"; then
    echo "  ok  ${label}: ${LEDGER}"
  else
    echo "  FAIL ${label}: ${LEDGER} (pattern not found: ${regex}; run 'sdlc.sh accept --work-id ${WORK_ID}')" >&2
    failures=$((failures + 1))
  fi
}

run_engine_parity() {
  local engine_cmd=()
  if command -v sdlc-engine >/dev/null 2>&1; then
    engine_cmd=(sdlc-engine)
  else
    local candidate
    for candidate in python3 python; do
      if command -v "${candidate}" >/dev/null 2>&1 \
        && "${candidate}" -c 'import sdlc_engine' >/dev/null 2>&1; then
        engine_cmd=("${candidate}" -m sdlc_engine)
        break
      fi
    done
  fi
  if ((${#engine_cmd[@]} == 0)); then
    echo "  skip engine parity: sdlc-engine not importable"
    return
  fi
  if (cd "${TARGET}" && "${engine_cmd[@]}" context parity); then
    echo "  ok  engine parity: sdlc-engine context parity"
  else
    echo "  FAIL engine parity: sdlc-engine context parity reported drift (try --repair)" >&2
    failures=$((failures + 1))
  fi
}

echo "Verifying command effects"
echo "  target: ${TARGET}"
echo "  home:   ${HOME_DIR}"
echo "  work-id: ${WORK_ID}"
echo "  step: ${STEP}"
echo

if [[ "${STEP}" == "init" ]]; then
  check_exists "framework home" "${HOME_DIR}"
  check_exists "requirements dir" "${HOME_DIR}/requirements"
  check_exists "spdd dir" "${HOME_DIR}/spdd"
  check_exists "lessons ledger" "${LEDGER}"
  check_exists "work registry" "$(sdlc_registry "${TARGET}")"
  check_exists "quality gates" "$(sdlc_harness_dir "${TARGET}")/quality-gates.md"
  check_exists "workflow CLI" "${HOME_DIR}/scripts/sdlc.sh"
fi

if [[ "${STEP}" == "plan" || "${STEP}" == "architect" || "${STEP}" == "code" || "${STEP}" == "review" || "${STEP}" == "prompt-update" || "${STEP}" == "sync" || "${STEP}" == "retro" || "${STEP}" == "capture" ]]; then
  check_exists "canvas" "${CANVAS}"
  check_exists "requirement" "${MILESTONE_REQ}"
fi

if [[ "${STEP}" == "plan" || "${STEP}" == "architect" || "${STEP}" == "prompt-update" ]]; then
  check_contains_regex "canvas operations section" "${CANVAS}" "^## O - Operations"
  check_contains_regex "canvas safeguards section" "${CANVAS}" "^## S - Safeguards"
fi

if [[ "${STEP}" == "architect" ]]; then
  check_contains_regex "architect readiness marker" "${CANVAS}" "Ready For Coding|Needs Analysis|Needs Clarification|Needs Redesign|Blocked"
fi

if [[ "${STEP}" == "code" ]]; then
  check_records_contain_regex "session evidence of operation" \
    "${OPERATION}|[Ii]mplement|[Cc]omplete|[Ff]iles changed"
  # Soft gate: when readiness is declared, it should be Ready For Coding.
  if grep -qE '^-[[:space:]]*[Rr]eadiness:[[:space:]]*|^readiness:[[:space:]]*' "${CANVAS}" 2>/dev/null; then
    check_contains_regex "code readiness Ready For Coding" "${CANVAS}" "Ready For Coding|ready-for-coding"
  fi
fi

if [[ "${STEP}" == "prompt-update" ]]; then
  check_records_contain_regex "captured record mentions work-id" "${WORK_ID}"
fi

if [[ "${STEP}" == "review" ]]; then
  check_exists "review artifact" "${SPDD_REVIEW}"
  if [[ -f "${SPDD_REVIEW}" ]]; then
    check_contains_regex "review status marker" "${SPDD_REVIEW}" \
      "Approved|Approved With Notes|Changes Requested|Blocked"
  fi
fi

if [[ "${STEP}" == "sync" ]]; then
  check_exists "sync report" "${SPDD_SYNC}"
fi

if [[ "${STEP}" == "retro" ]]; then
  # Retro promotes staged captures into the committed ledger.
  check_ledger_contains_regex "accepted lesson for work-id" "\"work_id\": ?\"${WORK_ID}\"|${WORK_ID}"
fi

if [[ "${STEP}" == "capture" ]]; then
  # capture-session-memory.sh stages kind=session records for the work-id.
  check_records_contain_regex "staged session record for work-id" "${WORK_ID}"

  if [[ -n "${MILESTONE}" ]]; then
    milestone_path="${MILESTONE}"
    if [[ "${milestone_path}" != /* ]]; then
      if [[ -f "${HOME_DIR}/${milestone_path#./}" ]]; then
        milestone_path="${HOME_DIR}/${milestone_path#./}"
      else
        milestone_path="${TARGET}/${milestone_path#./}"
      fi
    fi
    check_contains_regex "milestone mention work-id" "${milestone_path}" "${WORK_ID}"
  fi
  if [[ "${REQUIRE_ROADMAP}" -eq 1 ]]; then
    roadmap_path="${HOME_DIR}/ROADMAP.md"
    [[ -f "${roadmap_path}" ]] || roadmap_path="${TARGET}/ROADMAP.md"
    check_contains_regex "roadmap mention work-id" "${roadmap_path}" "${WORK_ID}"
  fi
fi

run_engine_parity

echo
if [[ "${failures}" -gt 0 ]]; then
  echo "Verification failed with ${failures} issue(s)." >&2
  exit 1
fi
echo "Verification passed."
