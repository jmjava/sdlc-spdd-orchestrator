#!/usr/bin/env bash
# Storage v3 layout contract for upgrade-project.sh:
#   A. Pre-v3 sprawl with no sdlc-spdd/ home → refused (exit 3), nothing moved
#   B. Dual layout (home + leftover legacy paths) → refused, nothing moved
#   C. Clean v3 install → upgrade succeeds, is idempotent, verify passes
#   D. Retired bash twins are never installed and are pruned on upgrade
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

INIT="${REPO_ROOT}/scripts/init-project.sh"
UPGRADE="${REPO_ROOT}/scripts/upgrade-project.sh"
VERIFY="${REPO_ROOT}/scripts/verify-project-install.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

seed_legacy_sprawl() {
  local target="$1"
  mkdir -p \
    "${target}/requirements/milestones" \
    "${target}/spdd/canvas" \
    "${target}/session-notes" \
    "${target}/agent-context/harness"
  echo "# legacy canvas" > "${target}/spdd/canvas/FEAT-001-legacy.md"
  printf 'work_id\tstatus\n' > "${target}/agent-context/work-registry.tsv"
}

run_upgrade() {
  local target="$1"
  local out rc=0
  out="$("${UPGRADE}" --target "${target}" 2>&1)" || rc=$?
  printf '%s\n' "${out}" > "${target}.upgrade.log"
  return "${rc}"
}

echo "== A. Pre-v3 sprawl without home is refused =="
mkdir -p "${WORK}/a"
seed_legacy_sprawl "${WORK}/a"
if run_upgrade "${WORK}/a"; then
  bad "upgrade should refuse pre-v3 layout"
else
  rc=$?
  [[ "${rc}" -eq 3 ]] && ok "exit 3 on pre-v3 layout" || bad "expected exit 3, got ${rc}"
fi
grep -q "pre-v3 SDLC-SPDD layout detected" "${WORK}/a.upgrade.log" && ok "refusal message printed" || bad "missing refusal message"
grep -q "init-project.sh --target" "${WORK}/a.upgrade.log" && ok "points at init-project" || bad "missing init hint"
[[ -f "${WORK}/a/spdd/canvas/FEAT-001-legacy.md" ]] && ok "legacy canvas untouched" || bad "legacy canvas was moved"
[[ ! -d "${WORK}/a/sdlc-spdd" ]] && ok "no home created on refusal" || bad "home created despite refusal"

echo "== B. Dual layout (home + legacy leftovers) is refused =="
mkdir -p "${WORK}/b"
"${INIT}" --target "${WORK}/b" >/dev/null 2>&1 || bad "init failed for B"
mkdir -p "${WORK}/b/agent-context/memory"
echo "x" > "${WORK}/b/agent-context/memory/lessons.md"
if run_upgrade "${WORK}/b"; then
  bad "upgrade should refuse dual layout"
else
  ok "dual layout refused"
fi
grep -q "re-run this upgrade" "${WORK}/b.upgrade.log" && ok "dual-layout hint printed" || bad "missing dual-layout hint"
[[ -f "${WORK}/b/agent-context/memory/lessons.md" ]] && ok "legacy leftover untouched" || bad "legacy leftover was moved"
[[ ! -d "${WORK}/b/sdlc-spdd/.sdlc/legacy-layout-archive" ]] && ok "no legacy archive dir" || bad "legacy archive dir created"

echo "== C. Clean v3 install upgrades idempotently =="
mkdir -p "${WORK}/c"
"${INIT}" --target "${WORK}/c" >/dev/null 2>&1 && ok "init v3" || bad "init failed for C"
echo "# project canvas" > "${WORK}/c/sdlc-spdd/spdd/canvas/FEAT-002-keep.md"
run_upgrade "${WORK}/c" && ok "first upgrade" || bad "first upgrade failed: $(cat "${WORK}/c.upgrade.log")"
run_upgrade "${WORK}/c" && ok "second upgrade" || bad "second upgrade failed"
[[ -f "${WORK}/c/sdlc-spdd/spdd/canvas/FEAT-002-keep.md" ]] && ok "project canvas preserved" || bad "project canvas lost"
if "${VERIFY}" --target "${WORK}/c" >"${WORK}/c.verify.log" 2>&1; then
  ok "verify passes after upgrade"
else
  bad "verify failed: $(tail -20 "${WORK}/c.verify.log")"
fi

echo "== D. Retired bash twins are not installed and are pruned =="
for twin in sdlc-workflow.sh sdlc-team-registry.sh sdlc-pointer.sh accept-lessons.sh; do
  [[ ! -e "${WORK}/c/sdlc-spdd/scripts/${twin}" ]] && ok "not installed: ${twin}" || bad "installed: ${twin}"
done
touch "${WORK}/c/sdlc-spdd/scripts/sdlc-workflow.sh"
run_upgrade "${WORK}/c" || bad "upgrade with stale twin failed"
[[ ! -e "${WORK}/c/sdlc-spdd/scripts/sdlc-workflow.sh" ]] && ok "stale twin pruned" || bad "stale twin left behind"
[[ -x "${WORK}/c/sdlc-spdd/scripts/sdlc.sh" ]] && ok "sdlc.sh dispatcher present" || bad "sdlc.sh missing"
grep -q "python -m sdlc_engine\|sdlc_engine" "${WORK}/c/sdlc-spdd/scripts/sdlc.sh" && ok "dispatcher targets Python engine" || bad "dispatcher does not target engine"

echo
echo "Results: ${pass} passed, ${fail} failed"
(( fail == 0 ))
