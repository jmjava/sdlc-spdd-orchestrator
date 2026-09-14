#!/usr/bin/env bash
# Regression harness for completed/cancelled Work ID archive (storage v3: remove artifacts).
#
# Runs the Python engine through the installed sdlc-spdd/scripts/sdlc.sh on a
# fresh init-project target per case. Contract under test:
#   - archive refuses non-terminal Final Status unless --force
#   - archive deletes canvas/analysis/review/sync + workflow state + session brief
#   - the milestone requirement and lessons.jsonl are never touched
#   - registry.jsonl gets an archived row with an archived:<kind> note token
#   - there is NO archive/ folder; stray legacy archive paths are ignored
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/harness.sh
source "${SCRIPT_DIR}/lib/harness.sh"

TARGETS=()
cleanup() {
  local t
  for t in "${TARGETS[@]}"; do rm -rf "${t}"; done
  return 0
}
trap cleanup EXIT

# Sets T (installed target) and H (its sdlc-spdd home). Not a subshell, so the
# target is tracked for cleanup.
new_target() {
  T="$(harness_new_target)"
  H="$(harness_home "${T}")"
  TARGETS+=("${T}")
}

registry_file() {
  printf '%s' "$(harness_home "$1")/spdd/memory/registry.jsonl"
}

registry_matches() {
  local t="$1" work_id="$2" regex="$3"
  local reg
  reg="$(registry_file "${t}")"
  [[ -f "${reg}" ]] && grep -q "\"work_id\": \"${work_id}\"" "${reg}" && grep -Eq "${regex}" "${reg}"
}

# Requirement + canvas (harness_seed_work) plus every sidecar the archive verb removes.
setup_work() {
  local t="$1" work_id="$2" final_status="$3"
  local home
  home="$(harness_home "${t}")"
  harness_seed_work "${t}" "${work_id}" "${final_status}"
  mkdir -p \
    "${home}/spdd/analysis" \
    "${home}/spdd/reviews" \
    "${home}/spdd/sync" \
    "${home}/.sdlc/workflows" \
    "${home}/.sdlc/sessions"
  printf '# analysis\n' > "${home}/spdd/analysis/${work_id}-analysis.md"
  printf '# review\n' > "${home}/spdd/reviews/${work_id}-review.md"
  printf '# sync\n' > "${home}/spdd/sync/${work_id}-sync.md"
  printf 'phase=code\nactive=1\n' > "${home}/.sdlc/workflows/${work_id}.state"
  printf '# session for %s\n' "${work_id}" > "${home}/.sdlc/sessions/20260727T000000Z-plan-${work_id}.md"
  printf '# current\n' > "${home}/.sdlc/sessions/current-session.md"
}

echo "== Test 1: refuse in-progress work without --force =="
new_target
setup_work "${T}" "FEAT-100-active" "In Progress"
if harness_sdlc "${T}" archive FEAT-100-active >/dev/null 2>&1; then
  bad "archive should refuse In Progress"
else
  ok "archive refuses In Progress"
fi
if [[ -f "${H}/spdd/canvas/FEAT-100-active.md" ]]; then
  ok "in-progress canvas left in place"
else
  bad "in-progress canvas was removed"
fi

echo "== Test 2: archive completed work removes artifacts =="
new_target
setup_work "${T}" "FEAT-101-done" "Complete"
SDLC_USER="archiver" harness_sdlc "${T}" claim FEAT-101-done >/dev/null
harness_sdlc "${T}" archive FEAT-101-done >/dev/null
if [[ ! -f "${H}/spdd/canvas/FEAT-101-done.md" \
   && ! -f "${H}/spdd/analysis/FEAT-101-done-analysis.md" \
   && ! -f "${H}/spdd/reviews/FEAT-101-done-review.md" \
   && ! -f "${H}/spdd/sync/FEAT-101-done-sync.md" ]]; then
  ok "canvas and sidecar artifacts removed"
else
  bad "contract artifacts still present after archive"
fi
if [[ ! -f "${H}/.sdlc/workflows/FEAT-101-done.state" ]]; then
  ok "workflow state removed"
else
  bad "workflow state still present after archive"
fi
if [[ -f "${H}/requirements/milestones/FEAT-101-done.md" ]]; then
  ok "milestone requirement left in place"
else
  bad "milestone should not be removed"
fi
if [[ ! -f "${H}/.sdlc/sessions/20260727T000000Z-plan-FEAT-101-done.md" \
   && -f "${H}/.sdlc/sessions/current-session.md" ]]; then
  ok "matching session brief removed; current-session kept"
else
  bad "session archive behavior incorrect"
fi
if registry_matches "${T}" "FEAT-101-done" '"status": "archived"'; then
  ok "registry status set to archived"
else
  bad "registry missing archived row"
fi
if [[ ! -e "${H}/spdd/canvas/archive" && ! -e "${H}/spdd/archive" && ! -e "${H}/archive" ]]; then
  ok "no archive/ folder created"
else
  bad "archive created an archive/ folder"
fi
ptr="$(harness_sdlc "${T}" pointer get)"
if [[ -z "${ptr}" ]]; then ok "pointer cleared on archive"; else bad "pointer still set (${ptr})"; fi

echo "== Test 3: archive cancelled work =="
new_target
setup_work "${T}" "FEAT-102-cancel" "Cancelled"
harness_sdlc "${T}" archive FEAT-102-cancel >/dev/null
if [[ ! -f "${H}/spdd/canvas/FEAT-102-cancel.md" ]] \
  && registry_matches "${T}" "FEAT-102-cancel" '"status": "archived"' \
  && registry_matches "${T}" "FEAT-102-cancel" 'archived:cancelled'; then
  ok "cancelled work archived with note token"
else
  bad "cancelled archive failed"
fi

echo "== Test 4: canceled spelling (US) treated as cancelled =="
new_target
setup_work "${T}" "FEAT-103-us" "Canceled — scope cut"
harness_sdlc "${T}" archive FEAT-103-us >/dev/null
if [[ ! -f "${H}/spdd/canvas/FEAT-103-us.md" ]]; then
  ok "Canceled spelling is archivable"
else
  bad "Canceled spelling not accepted"
fi

echo "== Test 5: dry-run does not remove files =="
new_target
setup_work "${T}" "FEAT-104-dry" "Complete"
out="$(harness_sdlc "${T}" archive FEAT-104-dry --dry-run)"
if [[ -f "${H}/spdd/canvas/FEAT-104-dry.md" ]]; then
  ok "dry-run leaves canvas in place"
else
  bad "dry-run removed canvas"
fi
if grep -Fq '[dry-run]' <<< "${out}"; then
  ok "dry-run prints planned removals"
else
  bad "dry-run missing plan output"
fi
if ! registry_matches "${T}" "FEAT-104-dry" '"status": "archived"'; then
  ok "dry-run does not write the registry"
else
  bad "dry-run wrote an archived registry row"
fi

echo "== Test 6: --all archives every eligible Work ID =="
new_target
setup_work "${T}" "FEAT-105-a" "Complete"
setup_work "${T}" "FEAT-105-b" "Cancelled"
setup_work "${T}" "FEAT-105-c" "In Progress"
harness_sdlc "${T}" archive --all >/dev/null
if [[ ! -f "${H}/spdd/canvas/FEAT-105-a.md" \
   && ! -f "${H}/spdd/canvas/FEAT-105-b.md" \
   && -f "${H}/spdd/canvas/FEAT-105-c.md" ]]; then
  ok "--all archives complete+cancelled, skips in-progress"
else
  bad "--all selection incorrect"
fi

echo "== Test 7: list-work ignores stray legacy archive paths =="
new_target
setup_work "${T}" "FEAT-106-live" "In Progress"
mkdir -p "${H}/spdd/canvas/archive"
printf '# old canvas\n' > "${H}/spdd/canvas/archive/FEAT-999-old.md"
out="$(harness_sdlc "${T}" list-work)"
if grep -q 'FEAT-106-live' <<< "${out}" && ! grep -q 'FEAT-999-old' <<< "${out}"; then
  ok "list-work skips Work IDs only under legacy archive paths"
else
  bad "list-work discover leaked archive entries"
fi

echo "== Test 8: sync-team marks cancelled without archiving =="
new_target
setup_work "${T}" "FEAT-107-sync" "Cancelled"
harness_sdlc "${T}" sync-team >/dev/null
if registry_matches "${T}" "FEAT-107-sync" '"status": "cancelled"' \
  && [[ -f "${H}/spdd/canvas/FEAT-107-sync.md" ]]; then
  ok "sync-team sets cancelled and leaves files"
else
  bad "sync-team cancelled behavior wrong"
fi

# Former Test 9 ("sdlc.sh wrapper archive path") is gone: with the bash twin
# deleted, the installed sdlc.sh dispatcher is the only path and every case
# above already exercises it.

echo "== Test 10: --force archives non-terminal work =="
new_target
setup_work "${T}" "FEAT-109-force" "In Progress"
if harness_sdlc "${T}" archive FEAT-109-force --force >/dev/null \
  && [[ ! -f "${H}/spdd/canvas/FEAT-109-force.md" ]] \
  && registry_matches "${T}" "FEAT-109-force" 'archived:forced'; then
  ok "--force archives non-terminal work"
else
  bad "--force archive failed"
fi

echo "== Test 12: archive leaves lessons.jsonl in place =="
new_target
setup_work "${T}" "FEAT-111-mem" "Complete"
mkdir -p "${H}/spdd/memory"
printf '%s\n' '{"id":"pitfall:FEAT-111-mem:engine:test","kind":"pitfall","work_id":"FEAT-111-mem","area":"engine","title":"keep me","body":"archive must not drop this dogfood record from lessons.jsonl.","source":"test","keywords":[],"schema":1}' > "${H}/spdd/memory/lessons.jsonl"
before="$(cat "${H}/spdd/memory/lessons.jsonl")"
out="$(harness_sdlc "${T}" archive FEAT-111-mem)"
after="$(cat "${H}/spdd/memory/lessons.jsonl")"
if [[ "${before}" == "${after}" ]] && grep -Fq 'lessons.jsonl' <<< "${out}"; then
  ok "archive leaves lessons.jsonl unchanged and says so"
else
  bad "archive mutated lessons.jsonl or omitted leave-ledger message"
fi

echo "== Test 11: re-archive is a no-op for --all =="
new_target
setup_work "${T}" "FEAT-110-once" "Complete"
harness_sdlc "${T}" archive FEAT-110-once >/dev/null
out="$(harness_sdlc "${T}" archive --all)"
if grep -q 'processed 0 eligible' <<< "${out}"; then
  ok "--all skips already-archived registry rows"
else
  if [[ ! -f "${H}/spdd/canvas/FEAT-110-once.md" ]]; then
    ok "--all did not duplicate archive (artifacts remain removed)"
  else
    bad "re-archive behavior unexpected: ${out}"
  fi
fi

harness_finish
