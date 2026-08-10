#!/usr/bin/env bash
# Regression: upgrade merges legacy root layout into an existing sdlc-spdd/ home.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SETUP="${REPO_ROOT}/scripts/setup-agent-prompts.sh"
UPGRADE="${REPO_ROOT}/scripts/upgrade-project.sh"
VERIFY="${REPO_ROOT}/scripts/verify-project-install.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT
TARGET="${WORK}/target"
HOME="${TARGET}/sdlc-spdd"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

rel() { echo "${1#"${TARGET}"/}"; }

assert_absent() {
  if [[ ! -e "$1" ]]; then ok "absent: $(rel "$1")"; else bad "should be absent: $(rel "$1")"; fi
}
assert_file_contains() {
  if [[ -f "$1" ]] && grep -Fq "$2" "$1"; then ok "contains in $(rel "$1"): $2"; else bad "missing in $(rel "$1"): $2"; fi
}

echo "== Setup v3 home + simulate legacy root sprawl =="
mkdir -p "${TARGET}"
"${SETUP}" --target "${TARGET}" --cursor >/dev/null

printf '%s\n' '# Home canvas' > "${HOME}/spdd/canvas/HOME-001.md"
mkdir -p "${TARGET}/spdd/canvas" "${TARGET}/requirements" "${TARGET}/scripts/sdlc-spdd"
printf '%s\n' '# Legacy canvas' > "${TARGET}/spdd/canvas/LEGACY-001.md"
printf '%s\n' '# Home req' > "${HOME}/requirements/home-req.md"
printf '%s\n' '# Legacy req' > "${TARGET}/requirements/legacy-req.md"
printf '%s\n' '# legacy script marker' > "${TARGET}/scripts/sdlc-spdd/legacy-marker.sh"
mkdir -p "${HOME}/.sdlc/staged" "${TARGET}/.sdlc/sessions"
printf '%s\n' 'staged-at-home' > "${HOME}/.sdlc/staged/note.txt"
printf '%s\n' 'session-at-root' > "${TARGET}/.sdlc/sessions/root-session.txt"

echo "== Upgrade merges root trees into home =="
"${UPGRADE}" --target "${TARGET}" --cursor >/dev/null

assert_absent "${TARGET}/requirements"
assert_absent "${TARGET}/spdd"
assert_absent "${TARGET}/scripts/sdlc-spdd"
assert_absent "${TARGET}/.sdlc"

assert_file_contains "${HOME}/spdd/canvas/HOME-001.md" "Home canvas"
assert_file_contains "${HOME}/spdd/canvas/LEGACY-001.md" "Legacy canvas"
assert_file_contains "${HOME}/requirements/home-req.md" "Home req"
assert_file_contains "${HOME}/requirements/legacy-req.md" "Legacy req"
assert_file_contains "${HOME}/.sdlc/staged/note.txt" "staged-at-home"
assert_file_contains "${HOME}/.sdlc/sessions/root-session.txt" "session-at-root"

if [[ -f "${HOME}/scripts/legacy-marker.sh" ]]; then
  ok "legacy scripts merged into home/scripts"
else
  bad "legacy scripts not merged into home/scripts"
fi

echo "== Verify install after consolidation =="
if "${VERIFY}" --target "${TARGET}" --require-cursor >/dev/null; then
  ok "verify-project-install passes"
else
  bad "verify-project-install failed after upgrade"
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
echo "All upgrade-consolidate tests passed."
