#!/usr/bin/env bash
set -euo pipefail

# Regression harness for agent-context/sdlc-pointer.sh
#
# Usage: ./tests/test-sdlc-pointer.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
POINTER="${REPO_ROOT}/agent-context/sdlc-pointer.sh"
START="${REPO_ROOT}/scripts/start-agent-session.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

run_pointer() {
  SDLC_ROOT="${1}" "${POINTER}" "${@:2}"
}

source_pointer() {
  SDLC_ROOT="${1}"
  # shellcheck source=/dev/null
  source "${POINTER}"
}

# ---------------------------------------------------------------------------
echo "== Test 1: CLI set/get/reset =="
T="${WORK}/cli"
mkdir -p "${T}"
run_pointer "${T}" set FEAT-001 >/dev/null
current="$(run_pointer "${T}" get)"
if [[ "${current}" == "FEAT-001" ]]; then ok "set/get round-trip"; else bad "expected FEAT-001, got '${current}'"; fi
run_pointer "${T}" reset >/dev/null
current="$(run_pointer "${T}" get)"
if [[ -z "${current}" ]]; then ok "reset clears pointer"; else bad "expected empty pointer after reset"; fi

# ---------------------------------------------------------------------------
echo "== Test 2: run_against_pointer guards execution =="
T="${WORK}/guard"
mkdir -p "${T}"
source_pointer "${T}"
sdlc_set_pointer "CHORE-123" >/dev/null
if run_against_pointer "CHORE-123" -- printf ok | grep -q ok; then
  ok "guarded run succeeds when pointer matches"
else
  bad "guarded run should succeed when pointer matches"
fi
if run_against_pointer "CHORE-999" -- printf fail >/dev/null 2>&1; then
  bad "guarded run should fail on mismatch"
else
  ok "guarded run refuses mismatch"
fi

# ---------------------------------------------------------------------------
echo "== Test 3: sdlc_init honors SDLC_POINTER_OVERRIDE =="
T="${WORK}/init"
mkdir -p "${T}"
SDLC_ROOT="${T}" SDLC_POINTER_OVERRIDE=SPIKE-001 "${POINTER}" init >/dev/null
current="$(run_pointer "${T}" get)"
if [[ "${current}" == "SPIKE-001" ]]; then ok "sdlc_init sets override"; else bad "sdlc_init override failed"; fi

# ---------------------------------------------------------------------------
echo "== Test 4: start-agent-session.sh sets pointer from --work-id =="
T="${WORK}/session"
mkdir -p "${T}/agent-context/sessions"
cp "${POINTER}" "${T}/agent-context/sdlc-pointer.sh"
chmod +x "${T}/agent-context/sdlc-pointer.sh"
"${START}" --target "${T}" --work-id FEAT-002-session --phase plan >/dev/null
current="$(SDLC_ROOT="${T}" "${T}/agent-context/sdlc-pointer.sh" get)"
if [[ "${current}" == "FEAT-002-session" ]]; then
  ok "start-agent-session sets pointer"
else
  bad "expected FEAT-002-session from session start, got '${current}'"
fi

# ---------------------------------------------------------------------------
echo "== Test 5: init-project installs pointer script =="
T="${WORK}/install"
mkdir -p "${T}"
"${REPO_ROOT}/scripts/init-project.sh" --target "${T}" >/dev/null
if [[ -x "${T}/agent-context/sdlc-pointer.sh" ]]; then
  ok "init-project installs executable pointer script"
else
  bad "init-project missing agent-context/sdlc-pointer.sh"
fi

# ---------------------------------------------------------------------------
echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
