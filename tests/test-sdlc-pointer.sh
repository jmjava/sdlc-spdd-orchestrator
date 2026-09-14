#!/usr/bin/env bash
# Pointer contract for the Python engine (storage v3, one engine):
#   1. pointer get is empty (exit 0) when unset
#   2. pointer set writes sdlc-spdd/.sdlc/pointer; get reads it back
#   3. pointer reset clears it
#   4. claim sets the pointer; shelf clears it; resume restores it
#   5. --target from the orchestrator dispatcher operates on the target
#   6. start-agent-session.sh --work-id sets the pointer
#
# Usage: ./tests/test-sdlc-pointer.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/harness.sh
source "${SCRIPT_DIR}/lib/harness.sh"

START="${HARNESS_REPO_ROOT}/scripts/start-agent-session.sh"

T="$(harness_new_target)"
trap 'rm -rf "${T}"' EXIT
HOME_DIR="$(harness_home "${T}")"
POINTER_FILE="${HOME_DIR}/.sdlc/pointer"

# ---------------------------------------------------------------------------
echo "== Test 1: pointer get is empty and exits 0 when unset =="
rc=0
current="$(harness_sdlc "${T}" pointer get)" || rc=$?
if [[ "${rc}" -eq 0 ]]; then ok "pointer get exits 0 when unset"; else bad "pointer get exit ${rc} when unset"; fi
if [[ -z "${current}" ]]; then ok "pointer get prints empty when unset"; else bad "expected empty pointer, got '${current}'"; fi

# ---------------------------------------------------------------------------
echo "== Test 2: pointer set writes sdlc-spdd/.sdlc/pointer =="
harness_sdlc "${T}" pointer set FEAT-001 >/dev/null
if [[ -f "${POINTER_FILE}" ]]; then ok "pointer file created under sdlc-spdd/.sdlc"; else bad "missing ${POINTER_FILE}"; fi
stored="$(tr -d '[:space:]' < "${POINTER_FILE}")"
if [[ "${stored}" == "FEAT-001" ]]; then ok "pointer file holds FEAT-001"; else bad "pointer file holds '${stored}'"; fi
if [[ ! -e "${T}/.sdlc/pointer" ]]; then ok "no root-level .sdlc/pointer (legacy layout)"; else bad "pointer written to legacy root .sdlc"; fi
current="$(harness_sdlc "${T}" pointer get)"
if [[ "${current}" == "FEAT-001" ]]; then ok "set/get round-trip"; else bad "expected FEAT-001, got '${current}'"; fi

# ---------------------------------------------------------------------------
echo "== Test 3: pointer reset clears it =="
harness_sdlc "${T}" pointer reset >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ -z "${current}" ]]; then ok "reset clears pointer"; else bad "expected empty pointer after reset, got '${current}'"; fi
if [[ ! -s "${POINTER_FILE}" ]]; then ok "pointer file absent or empty after reset"; else bad "pointer file still holds '$(cat "${POINTER_FILE}")'"; fi

# ---------------------------------------------------------------------------
echo "== Test 4: claim sets, shelf clears, resume restores =="
harness_seed_work "${T}" FEAT-002-claim
SDLC_USER="pointer-test" harness_sdlc "${T}" claim FEAT-002-claim >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ "${current}" == "FEAT-002-claim" ]]; then ok "claim sets pointer"; else bad "claim: expected FEAT-002-claim, got '${current}'"; fi

harness_sdlc "${T}" shelf --reason "pointer test" >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ -z "${current}" ]]; then ok "shelf clears pointer"; else bad "shelf: expected empty pointer, got '${current}'"; fi

harness_sdlc "${T}" resume FEAT-002-claim >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ "${current}" == "FEAT-002-claim" ]]; then ok "resume restores pointer"; else bad "resume: expected FEAT-002-claim, got '${current}'"; fi

harness_sdlc "${T}" release >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ -z "${current}" ]]; then ok "release clears pointer"; else bad "release: expected empty pointer, got '${current}'"; fi

# ---------------------------------------------------------------------------
echo "== Test 5: orchestrator sdlc.sh --target operates on the target pointer =="
ORCH_SDLC="${HARNESS_REPO_ROOT}/scripts/sdlc.sh"
harness_export_engine
"${ORCH_SDLC}" --target "${T}" pointer set SPIKE-001 >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ "${current}" == "SPIKE-001" ]]; then ok "--target pointer set lands in target"; else bad "--target set: got '${current}'"; fi
current="$("${ORCH_SDLC}" pointer get --target "${T}")"
if [[ "${current}" == "SPIKE-001" ]]; then ok "trailing --target pointer get reads target"; else bad "trailing --target get: got '${current}'"; fi
"${ORCH_SDLC}" --target "${T}" pointer reset >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ -z "${current}" ]]; then ok "--target pointer reset clears target"; else bad "--target reset: got '${current}'"; fi

# ---------------------------------------------------------------------------
echo "== Test 6: start-agent-session.sh sets pointer from --work-id =="
harness_seed_work "${T}" FEAT-003-session
"${START}" --target "${T}" --work-id FEAT-003-session --phase plan >/dev/null
current="$(harness_sdlc "${T}" pointer get)"
if [[ "${current}" == "FEAT-003-session" ]]; then
  ok "start-agent-session sets pointer"
else
  bad "expected FEAT-003-session from session start, got '${current}'"
fi

# ---------------------------------------------------------------------------
echo "== Test 7: init-project installs no bash pointer twin =="
if [[ ! -e "${HOME_DIR}/scripts/sdlc-pointer.sh" ]]; then
  ok "sdlc-pointer.sh twin is not installed"
else
  bad "retired sdlc-pointer.sh twin installed"
fi
if [[ -x "${HOME_DIR}/scripts/sdlc.sh" ]]; then
  ok "sdlc.sh dispatcher installed"
else
  bad "sdlc.sh dispatcher missing"
fi

harness_finish
