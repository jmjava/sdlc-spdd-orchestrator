#!/usr/bin/env bash
# Regression harness for completed/cancelled Work ID archive (storage v3: remove artifacts).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKFLOW="${REPO_ROOT}/templates/agent-context/sdlc-workflow.sh"
POINTER="${REPO_ROOT}/templates/agent-context/sdlc-pointer.sh"
TEAM="${REPO_ROOT}/templates/agent-context/sdlc-team-registry.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

registry_file() {
  local t="$1"
  printf '%s' "${t}/sdlc-spdd/spdd/memory/registry.jsonl"
}

registry_matches() {
  local t="$1" work_id="$2" regex="$3"
  local reg
  reg="$(registry_file "${t}")"
  [[ -f "${reg}" ]] && grep -q "\"work_id\": \"${work_id}\"" "${reg}" && grep -Eq "${regex}" "${reg}"
}

wf() { SDLC_ROOT="${1}" "${WORKFLOW}" "${@:2}"; }

setup_work() {
  local t="$1"
  local work_id="$2"
  local final_status="$3"
  mkdir -p \
    "${t}/sdlc-spdd/scripts" \
    "${t}/sdlc-spdd/spdd/canvas" \
    "${t}/sdlc-spdd/spdd/analysis" \
    "${t}/sdlc-spdd/spdd/reviews" \
    "${t}/sdlc-spdd/spdd/sync" \
    "${t}/sdlc-spdd/requirements/milestones" \
    "${t}/sdlc-spdd/.sdlc/workflows" \
    "${t}/sdlc-spdd/.sdlc/sessions" \
    "${t}/sdlc-spdd/scripts"
  cp "${POINTER}" "${t}/sdlc-spdd/scripts/sdlc-pointer.sh"
  cp "${WORKFLOW}" "${t}/sdlc-spdd/scripts/sdlc-workflow.sh"
  cp "${TEAM}" "${t}/sdlc-spdd/scripts/sdlc-team-registry.sh"
  mkdir -p "${t}/sdlc-spdd/spdd/memory" "${t}/sdlc-spdd/scripts/lib"
  cp "${REPO_ROOT}/scripts/lib/paths.sh" "${t}/sdlc-spdd/scripts/lib/paths.sh"
  : > "${t}/sdlc-spdd/spdd/memory/registry.jsonl"
  cp "${REPO_ROOT}/scripts/sdlc.sh" "${t}/sdlc-spdd/scripts/sdlc.sh"
  chmod +x \
    "${t}/sdlc-spdd/scripts/sdlc-pointer.sh" \
    "${t}/sdlc-spdd/scripts/sdlc-workflow.sh" \
    "${t}/sdlc-spdd/scripts/sdlc-team-registry.sh" \
    "${t}/sdlc-spdd/scripts/sdlc.sh"

  cat > "${t}/sdlc-spdd/spdd/canvas/${work_id}.md" <<EOF
# ${work_id}

## Final Status

- Status: ${final_status}
EOF
  printf '# analysis\n' > "${t}/sdlc-spdd/spdd/analysis/${work_id}-analysis.md"
  printf '# review\n' > "${t}/sdlc-spdd/spdd/reviews/${work_id}-review.md"
  printf '# sync\n' > "${t}/sdlc-spdd/spdd/sync/${work_id}-sync.md"
  printf '# feature\n' > "${t}/sdlc-spdd/requirements/milestones/${work_id}.md"
  printf 'phase=code\nactive=1\n' > "${t}/sdlc-spdd/.sdlc/workflows/${work_id}.state"
  printf '# session for %s\n' "${work_id}" > "${t}/sdlc-spdd/.sdlc/sessions/20260727T000000Z-plan-${work_id}.md"
  printf '# current\n' > "${t}/sdlc-spdd/.sdlc/sessions/current-session.md"
}

echo "== Test 1: refuse in-progress work without --force =="
T="${WORK}/refuse"
setup_work "${T}" "FEAT-100-active" "In Progress"
if SDLC_ROOT="${T}" wf "${T}" archive FEAT-100-active >/dev/null 2>&1; then
  bad "archive should refuse In Progress"
else
  ok "archive refuses In Progress"
fi
if [[ -f "${T}/sdlc-spdd/spdd/canvas/FEAT-100-active.md" ]]; then
  ok "in-progress canvas left in place"
else
  bad "in-progress canvas was removed"
fi

echo "== Test 2: archive completed work removes artifacts =="
T="${WORK}/complete"
setup_work "${T}" "FEAT-101-done" "Complete"
SDLC_USER="archiver" SDLC_ROOT="${T}" wf "${T}" claim FEAT-101-done >/dev/null
SDLC_ROOT="${T}" wf "${T}" archive FEAT-101-done >/dev/null
if [[ ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-101-done.md" \
   && ! -f "${T}/sdlc-spdd/spdd/analysis/FEAT-101-done-analysis.md" \
   && ! -f "${T}/sdlc-spdd/spdd/reviews/FEAT-101-done-review.md" \
   && ! -f "${T}/sdlc-spdd/spdd/sync/FEAT-101-done-sync.md" ]]; then
  ok "canvas and sidecar artifacts removed"
else
  bad "contract artifacts still present after archive"
fi
if [[ -f "${T}/sdlc-spdd/requirements/milestones/FEAT-101-done.md" ]]; then
  ok "milestone requirement left in place"
else
  bad "milestone should not be removed"
fi
if [[ ! -f "${T}/sdlc-spdd/.sdlc/sessions/20260727T000000Z-plan-FEAT-101-done.md" \
   && -f "${T}/sdlc-spdd/.sdlc/sessions/current-session.md" ]]; then
  ok "matching session brief removed; current-session kept"
else
  bad "session archive behavior incorrect"
fi
if registry_matches "${T}" "FEAT-101-done" '"status": "archived"'; then
  ok "registry status set to archived"
else
  bad "registry missing archived row"
fi
ptr="$(SDLC_ROOT="${T}" "${T}/sdlc-spdd/scripts/sdlc-pointer.sh" get)"
if [[ -z "${ptr}" ]]; then ok "pointer cleared on archive"; else bad "pointer still set (${ptr})"; fi

echo "== Test 3: archive cancelled work =="
T="${WORK}/cancelled"
setup_work "${T}" "FEAT-102-cancel" "Cancelled"
SDLC_ROOT="${T}" wf "${T}" archive FEAT-102-cancel >/dev/null
if [[ ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-102-cancel.md" ]] \
  && registry_matches "${T}" "FEAT-102-cancel" '"status": "archived"' \
  && registry_matches "${T}" "FEAT-102-cancel" 'archived:cancelled'; then
  ok "cancelled work archived with note token"
else
  bad "cancelled archive failed"
fi

echo "== Test 4: canceled spelling (US) treated as cancelled =="
T="${WORK}/canceled-us"
setup_work "${T}" "FEAT-103-us" "Canceled — scope cut"
SDLC_ROOT="${T}" wf "${T}" archive FEAT-103-us >/dev/null
if [[ ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-103-us.md" ]]; then
  ok "Canceled spelling is archivable"
else
  bad "Canceled spelling not accepted"
fi

echo "== Test 5: dry-run does not remove files =="
T="${WORK}/dry"
setup_work "${T}" "FEAT-104-dry" "Complete"
out="$(SDLC_ROOT="${T}" wf "${T}" archive FEAT-104-dry --dry-run)"
if [[ -f "${T}/sdlc-spdd/spdd/canvas/FEAT-104-dry.md" ]]; then
  ok "dry-run leaves canvas in place"
else
  bad "dry-run removed canvas"
fi
if grep -Fq '[dry-run]' <<< "${out}"; then
  ok "dry-run prints planned removals"
else
  bad "dry-run missing plan output"
fi

echo "== Test 6: --all archives every eligible Work ID =="
T="${WORK}/all"
setup_work "${T}" "FEAT-105-a" "Complete"
setup_work "${T}" "FEAT-105-b" "Cancelled"
setup_work "${T}" "FEAT-105-c" "In Progress"
SDLC_ROOT="${T}" wf "${T}" archive --all >/dev/null
if [[ ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-105-a.md" \
   && ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-105-b.md" \
   && -f "${T}/sdlc-spdd/spdd/canvas/FEAT-105-c.md" ]]; then
  ok "--all archives complete+cancelled, skips in-progress"
else
  bad "--all selection incorrect"
fi

echo "== Test 7: list-work ignores stray legacy archive paths =="
T="${WORK}/discover"
setup_work "${T}" "FEAT-106-live" "In Progress"
mkdir -p "${T}/sdlc-spdd/spdd/canvas/archive"
printf '# old canvas\n' > "${T}/sdlc-spdd/spdd/canvas/archive/FEAT-999-old.md"
out="$(SDLC_ROOT="${T}" wf "${T}" list-work)"
if grep -q 'FEAT-106-live' <<< "${out}" && ! grep -q 'FEAT-999-old' <<< "${out}"; then
  ok "list-work skips Work IDs only under legacy archive paths"
else
  bad "list-work discover leaked archive entries"
fi

echo "== Test 8: sync-team marks cancelled without archiving =="
T="${WORK}/sync-cancel"
setup_work "${T}" "FEAT-107-sync" "Cancelled"
SDLC_ROOT="${T}" wf "${T}" sync-team >/dev/null
if registry_matches "${T}" "FEAT-107-sync" '"status": "cancelled"' \
  && [[ -f "${T}/sdlc-spdd/spdd/canvas/FEAT-107-sync.md" ]]; then
  ok "sync-team sets cancelled and leaves files"
else
  bad "sync-team cancelled behavior wrong"
fi

echo "== Test 9: sdlc.sh wrapper archive path =="
T="${WORK}/wrapper"
setup_work "${T}" "FEAT-108-wrap" "Complete"
if SDLC_ROOT="${T}" "${T}/sdlc-spdd/scripts/sdlc.sh" archive FEAT-108-wrap >/dev/null \
  && [[ ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-108-wrap.md" ]]; then
  ok "sdlc.sh archive wrapper works"
else
  bad "sdlc.sh archive wrapper failed"
fi

echo "== Test 10: --force archives non-terminal work =="
T="${WORK}/force"
setup_work "${T}" "FEAT-109-force" "In Progress"
if SDLC_ROOT="${T}" wf "${T}" archive FEAT-109-force --force >/dev/null \
  && [[ ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-109-force.md" ]] \
  && registry_matches "${T}" "FEAT-109-force" 'archived:forced'; then
  ok "--force archives non-terminal work"
else
  bad "--force archive failed"
fi

echo "== Test 12: archive leaves lessons.jsonl in place =="
T="${WORK}/ledger"
setup_work "${T}" "FEAT-111-mem" "Complete"
mkdir -p "${T}/sdlc-spdd/spdd/memory"
printf '%s\n' '{"id":"pitfall:FEAT-111-mem:engine:test","kind":"pitfall","work_id":"FEAT-111-mem","area":"engine","title":"keep me","body":"archive must not drop this dogfood record from lessons.jsonl.","source":"test","keywords":[],"schema":1}' > "${T}/sdlc-spdd/spdd/memory/lessons.jsonl"
before="$(cat "${T}/sdlc-spdd/spdd/memory/lessons.jsonl")"
out="$(SDLC_ROOT="${T}" wf "${T}" archive FEAT-111-mem)"
after="$(cat "${T}/sdlc-spdd/spdd/memory/lessons.jsonl")"
if [[ "${before}" == "${after}" ]] && grep -Fq 'lessons.jsonl' <<< "${out}"; then
  ok "archive leaves lessons.jsonl unchanged and says so"
else
  bad "archive mutated lessons.jsonl or omitted leave-ledger message"
fi

echo "== Test 11: re-archive is a no-op for --all =="
T="${WORK}/rearchive"
setup_work "${T}" "FEAT-110-once" "Complete"
SDLC_ROOT="${T}" wf "${T}" archive FEAT-110-once >/dev/null
out="$(SDLC_ROOT="${T}" wf "${T}" archive --all)"
if grep -q 'processed 0 eligible' <<< "${out}"; then
  ok "--all skips already-archived registry rows"
else
  if [[ ! -f "${T}/sdlc-spdd/spdd/canvas/FEAT-110-once.md" ]]; then
    ok "--all did not duplicate archive (artifacts remain removed)"
  else
    bad "re-archive behavior unexpected: ${out}"
  fi
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
echo "All archive-work tests passed."
