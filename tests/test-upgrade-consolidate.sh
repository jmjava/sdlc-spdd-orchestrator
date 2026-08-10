#!/usr/bin/env bash
# Full regression suite for storage-v3 upgrade consolidation:
#   A. Pure legacy sprawl (no home yet) → single sdlc-spdd/ home
#   B. Dual layout merge when home already exists (dest wins)
#   C. Leftover agent-context archived (not left at root)
#   D. Idempotent second upgrade
#   E. Dry-run + --consolidate no-op flag
#   F. Orchestrator-shaped target keeps agent-context/ + scripts/ source
#   G. verify-project-install accepts orchestrator after stay-set move
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SETUP="${REPO_ROOT}/scripts/setup-agent-prompts.sh"
INIT="${REPO_ROOT}/scripts/init-project.sh"
UPGRADE="${REPO_ROOT}/scripts/upgrade-project.sh"
VERIFY="${REPO_ROOT}/scripts/verify-project-install.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

assert_absent() {
  local root="$1" path="$2" label="${3:-$2}"
  if [[ ! -e "${root}/${path}" ]]; then ok "absent: ${label}"; else bad "should be absent: ${label}"; fi
}
assert_file() {
  local f="$1" label="${2:-$1}"
  if [[ -f "${f}" ]]; then ok "exists: ${label}"; else bad "missing: ${label}"; fi
}
assert_file_contains() {
  local f="$1" expected="$2" label="${3:-$1}"
  if [[ -f "${f}" ]] && grep -Fq "${expected}" "${f}"; then
    ok "contains (${label}): ${expected}"
  else
    bad "missing (${label}): ${expected}"
  fi
}
assert_dir() {
  local d="$1" label="${2:-$1}"
  if [[ -d "${d}" ]]; then ok "dir: ${label}"; else bad "missing dir: ${label}"; fi
}

seed_legacy_sprawl() {
  local target="$1"
  mkdir -p \
    "${target}/requirements/milestones" \
    "${target}/spdd/canvas" \
    "${target}/spdd/memory" \
    "${target}/session-notes" \
    "${target}/docs/sdlc-spdd" \
    "${target}/harness/skills" \
    "${target}/agent-context/harness/skills" \
    "${target}/agent-context/playbooks" \
    "${target}/agent-context/custom" \
    "${target}/scripts/sdlc-spdd" \
    "${target}/.sdlc/sessions"
  printf '%s\n' '# Legacy ROADMAP' > "${target}/ROADMAP.md"
  printf '%s\n' '# Legacy req' > "${target}/requirements/legacy-req.md"
  printf '%s\n' '# Legacy canvas' > "${target}/spdd/canvas/LEGACY-001.md"
  : > "${target}/spdd/memory/lessons.jsonl"
  : > "${target}/spdd/memory/registry.jsonl"
  printf '%s\n' '# Legacy note' > "${target}/session-notes/legacy.md"
  printf '%s\n' '# Legacy docs hub' > "${target}/docs/sdlc-spdd/README.md"
  printf '%s\n' '# Project-local doc keep' > "${target}/docs/sdlc-spdd/project-local.md"
  printf '%s\n' '# Root harness skill' > "${target}/harness/skills/root-skill.md"
  printf '%s\n' '# AC harness skill' > "${target}/agent-context/harness/skills/ac-skill.md"
  printf '%s\n' '# playbook' > "${target}/agent-context/playbooks/legacy-widget-playbook.md"
  printf '%s\n' '# custom leftover' > "${target}/agent-context/custom/note.md"
  printf '%s\n' '#!/bin/sh' > "${target}/scripts/sdlc-spdd/legacy-marker.sh"
  printf '%s\n' 'session-at-root' > "${target}/.sdlc/sessions/root-session.txt"
  printf '%s\n' '# Milestone' > "${target}/milestone-legacy.md"
  # Minimal adapters so upgrade --cursor can refresh without init.
  mkdir -p "${target}/.cursor/commands" "${target}/.cursor/rules"
  printf '%s\n' '# stub' > "${target}/.cursor/commands/sdlc-spdd-plan.md"
  printf '%s\n' '# stub' > "${target}/.cursor/commands/sdlc-spdd-init.md"
  printf '%s\n' 'stub' > "${target}/.cursor/rules/sdlc-spdd.mdc"
  printf '%s\n' $'\n' > "${target}/.gitignore"
}

# ---------------------------------------------------------------------------
echo "== A. Pure legacy sprawl → sdlc-spdd/ home =="
# ---------------------------------------------------------------------------
A="${WORK}/pure-legacy"
mkdir -p "${A}"
seed_legacy_sprawl "${A}"
AH="${A}/sdlc-spdd"

"${UPGRADE}" --target "${A}" --cursor --no-backup >/dev/null

assert_dir "${AH}" "home created"
assert_absent "${A}" "requirements"
assert_absent "${A}" "spdd"
assert_absent "${A}" "session-notes"
assert_absent "${A}" "ROADMAP.md"
assert_absent "${A}" "harness"
assert_absent "${A}" "docs/sdlc-spdd"
assert_absent "${A}" "scripts/sdlc-spdd"
assert_absent "${A}" ".sdlc"
assert_absent "${A}" "agent-context"
assert_absent "${A}" "milestone-legacy.md"

assert_file_contains "${AH}/ROADMAP.md" "Legacy ROADMAP" "home ROADMAP"
assert_file_contains "${AH}/requirements/legacy-req.md" "Legacy req" "home req"
assert_file_contains "${AH}/spdd/canvas/LEGACY-001.md" "Legacy canvas" "home canvas"
assert_file_contains "${AH}/session-notes/legacy.md" "Legacy note" "home session note"
# Framework refresh may overwrite docs/README.md; project-local docs must remain.
assert_file_contains "${AH}/docs/project-local.md" "Project-local doc keep" "home project-local docs"
assert_file "${AH}/docs/README.md" "home docs hub present"
assert_file_contains "${AH}/harness/skills/root-skill.md" "Root harness skill" "root harness skill"
assert_file_contains "${AH}/harness/skills/ac-skill.md" "AC harness skill" "ac harness skill"
assert_file_contains "${AH}/scripts/legacy-marker.sh" "#!/bin/sh" "legacy scripts merged"
assert_file_contains "${AH}/.sdlc/sessions/root-session.txt" "session-at-root" "runtime merged"
assert_file "${AH}/milestone-legacy.md" "milestone moved"
assert_file "${AH}/spdd/memory/lessons.jsonl" "lessons ledger"
assert_file "${AH}/spdd/memory/registry.jsonl" "registry ledger"

shopt -s nullglob
archive_hits=("${AH}"/.sdlc/legacy-layout-archive/*/agent-context/custom/note.md)
shopt -u nullglob
if ((${#archive_hits[@]} > 0)); then
  ok "A: leftover agent-context archived"
else
  bad "A: leftover agent-context not archived"
fi

if "${VERIFY}" --target "${A}" --require-cursor >/dev/null; then
  ok "A: verify passes after pure-legacy upgrade"
else
  bad "A: verify failed after pure-legacy upgrade"
fi

# ---------------------------------------------------------------------------
echo "== B. Dual layout merge (home already exists; dest wins) =="
# ---------------------------------------------------------------------------
B="${WORK}/dual"
mkdir -p "${B}"
"${SETUP}" --target "${B}" --cursor >/dev/null
BH="${B}/sdlc-spdd"

printf '%s\n' '# Home canvas' > "${BH}/spdd/canvas/HOME-001.md"
printf '%s\n' '# Home ROADMAP keep' > "${BH}/ROADMAP.md"
mkdir -p "${B}/spdd/canvas" "${B}/requirements" "${B}/scripts/sdlc-spdd" \
  "${B}/session-notes" "${BH}/.sdlc/staged" "${B}/.sdlc/sessions" \
  "${B}/agent-context/custom"
printf '%s\n' '# Legacy canvas' > "${B}/spdd/canvas/LEGACY-001.md"
printf '%s\n' '# Legacy req' > "${B}/requirements/legacy-req.md"
printf '%s\n' '# Home req' > "${BH}/requirements/home-req.md"
printf '%s\n' '# root roadmap lose' > "${B}/ROADMAP.md"
printf '%s\n' '# legacy script' > "${B}/scripts/sdlc-spdd/legacy-marker.sh"
printf '%s\n' 'staged-at-home' > "${BH}/.sdlc/staged/note.txt"
printf '%s\n' 'session-at-root' > "${B}/.sdlc/sessions/root-session.txt"
printf '%s\n' '# leftover custom' > "${B}/agent-context/custom/note.md"
printf '%s\n' '# legacy note' > "${B}/session-notes/legacy.md"

"${UPGRADE}" --target "${B}" --cursor --no-backup >/dev/null

assert_absent "${B}" "requirements"
assert_absent "${B}" "spdd"
assert_absent "${B}" "scripts/sdlc-spdd"
assert_absent "${B}" ".sdlc"
assert_absent "${B}" "agent-context"
assert_absent "${B}" "ROADMAP.md"
assert_absent "${B}" "session-notes"

assert_file_contains "${BH}/spdd/canvas/HOME-001.md" "Home canvas" "B home canvas kept"
assert_file_contains "${BH}/spdd/canvas/LEGACY-001.md" "Legacy canvas" "B legacy canvas merged"
assert_file_contains "${BH}/requirements/home-req.md" "Home req" "B home req kept"
assert_file_contains "${BH}/requirements/legacy-req.md" "Legacy req" "B legacy req merged"
assert_file_contains "${BH}/ROADMAP.md" "Home ROADMAP keep" "B dest ROADMAP wins"
assert_file_contains "${BH}/.sdlc/staged/note.txt" "staged-at-home" "B staged kept"
assert_file_contains "${BH}/.sdlc/sessions/root-session.txt" "session-at-root" "B runtime merged"
assert_file_contains "${BH}/session-notes/legacy.md" "legacy note" "B session notes merged"
assert_file "${BH}/scripts/legacy-marker.sh" "B legacy scripts merged"

shopt -s nullglob
archive_hits=("${BH}"/.sdlc/legacy-layout-archive/*/agent-context/custom/note.md)
shopt -u nullglob
if ((${#archive_hits[@]} > 0)); then
  ok "B: leftover agent-context archived"
else
  bad "B: leftover agent-context not archived"
fi

if "${VERIFY}" --target "${B}" --require-cursor >/dev/null; then
  ok "B: verify passes after dual-layout upgrade"
else
  bad "B: verify failed after dual-layout upgrade"
fi

# ---------------------------------------------------------------------------
echo "== C. Idempotent second upgrade =="
# ---------------------------------------------------------------------------
before_canvas="$(cat "${BH}/spdd/canvas/HOME-001.md")"
"${UPGRADE}" --target "${B}" --cursor --no-backup >/dev/null
after_canvas="$(cat "${BH}/spdd/canvas/HOME-001.md")"
if [[ "${before_canvas}" == "${after_canvas}" ]]; then
  ok "C: second upgrade preserves project canvas"
else
  bad "C: second upgrade mutated project canvas"
fi
assert_absent "${B}" "requirements" "C still absent requirements"
assert_absent "${B}" "spdd" "C still absent spdd"
assert_absent "${B}" "agent-context" "C still absent agent-context"
if "${VERIFY}" --target "${B}" --require-cursor >/dev/null; then
  ok "C: verify still passes"
else
  bad "C: verify failed after second upgrade"
fi

# ---------------------------------------------------------------------------
echo "== D. Dry-run + --consolidate no-op =="
# ---------------------------------------------------------------------------
D="${WORK}/dry-run"
mkdir -p "${D}"
seed_legacy_sprawl "${D}"
if "${UPGRADE}" --target "${D}" --cursor --dry-run --consolidate >/dev/null 2>&1; then
  ok "D: dry-run + --consolidate accepted"
else
  bad "D: dry-run/--consolidate failed"
fi
if [[ -d "${D}/requirements" && -d "${D}/spdd" && ! -d "${D}/sdlc-spdd" ]]; then
  ok "D: dry-run left legacy tree untouched"
else
  bad "D: dry-run mutated or created home unexpectedly"
fi

# ---------------------------------------------------------------------------
echo "== E. Orchestrator-shaped target keeps install source =="
# ---------------------------------------------------------------------------
E="${WORK}/orch-shaped"
mkdir -p "${E}"
# Minimal orchestrator markers + stay-set sprawl + install source tree.
mkdir -p \
  "${E}/scripts" \
  "${E}/templates/cursor" \
  "${E}/engine/src" \
  "${E}/agent-context/harness/skills" \
  "${E}/requirements" \
  "${E}/spdd/canvas" \
  "${E}/session-notes" \
  "${E}/.sdlc/sessions" \
  "${E}/.cursor/commands" \
  "${E}/.cursor/rules"
# Point upgrade's REPO_ROOT copies are from real orchestrator; target only needs
# markers so framework_is_orchestrator_root returns true for the *target*.
cp "${REPO_ROOT}/scripts/init-project.sh" "${E}/scripts/init-project.sh"
cp "${REPO_ROOT}/scripts/upgrade-project.sh" "${E}/scripts/upgrade-project.sh"
# Real upgrade still reads REPO_ROOT (orchestrator checkout), not E/scripts.
printf '%s\n' '# orch harness source' > "${E}/agent-context/harness/quality-gates.md"
printf '%s\n' '# orch skill source' > "${E}/agent-context/harness/skills/source-skill.md"
printf '%s\n' '#!/bin/sh' > "${E}/agent-context/sdlc-workflow.sh"
chmod +x "${E}/agent-context/sdlc-workflow.sh"
printf '%s\n' '# orch README' > "${E}/agent-context/README.md"
printf '%s\n' '# stay-set req' > "${E}/requirements/orch-req.md"
printf '%s\n' '# stay-set canvas' > "${E}/spdd/canvas/ORCH-001.md"
printf '%s\n' '# stay-set note' > "${E}/session-notes/orch.md"
printf '%s\n' '# stay-set roadmap' > "${E}/ROADMAP.md"
printf '%s\n' 'session' > "${E}/.sdlc/sessions/s.txt"
printf '%s\n' '# stub' > "${E}/.cursor/commands/sdlc-spdd-plan.md"
printf '%s\n' '# stub' > "${E}/.cursor/commands/sdlc-spdd-init.md"
printf '%s\n' 'stub' > "${E}/.cursor/rules/sdlc-spdd.mdc"
printf '%s\n' $'\n' > "${E}/.gitignore"
# Extra file under scripts so prune must not remove the tree.
printf '%s\n' '# keep' > "${E}/scripts/keep-me.sh"

EH="${E}/sdlc-spdd"
"${UPGRADE}" --target "${E}" --cursor --no-backup >/dev/null

assert_absent "${E}" "requirements" "E stay-set requirements moved"
assert_absent "${E}" "spdd" "E stay-set spdd moved"
assert_absent "${E}" "session-notes" "E stay-set session-notes moved"
assert_absent "${E}" "ROADMAP.md" "E stay-set ROADMAP moved"
assert_absent "${E}" ".sdlc" "E root .sdlc moved"

if [[ -f "${E}/agent-context/harness/quality-gates.md" \
   && -f "${E}/agent-context/sdlc-workflow.sh" \
   && -f "${E}/scripts/keep-me.sh" \
   && -f "${E}/scripts/init-project.sh" ]]; then
  ok "E: orchestrator source trees preserved"
else
  bad "E: orchestrator source trees were consumed"
fi

assert_file_contains "${EH}/requirements/orch-req.md" "stay-set req" "E home req"
assert_file_contains "${EH}/spdd/canvas/ORCH-001.md" "stay-set canvas" "E home canvas"
assert_file_contains "${EH}/ROADMAP.md" "stay-set roadmap" "E home ROADMAP"
# Seed copies missing files from agent-context/harness; phase 3 may refresh
# framework-owned quality-gates.md from the real orchestrator REPO_ROOT.
assert_file_contains "${EH}/harness/skills/source-skill.md" "orch skill source" "E seeded skill"
assert_file "${EH}/harness/quality-gates.md" "E home harness quality-gates present"
assert_file_contains "${E}/agent-context/harness/quality-gates.md" "orch harness source" "E source harness still present"
assert_file_contains "${E}/agent-context/harness/skills/source-skill.md" "orch skill source" "E source skill still present"

if "${VERIFY}" --target "${E}" --require-cursor >/dev/null; then
  ok "E: verify passes for orchestrator-shaped target"
else
  bad "E: verify failed for orchestrator-shaped target"
fi

# ---------------------------------------------------------------------------
echo "== F. Fresh init already v3 — upgrade is no-op for layout =="
# ---------------------------------------------------------------------------
F="${WORK}/fresh-v3"
mkdir -p "${F}"
"${INIT}" --target "${F}" --cursor --no-backup >/dev/null 2>&1 \
  || "${SETUP}" --target "${F}" --cursor >/dev/null
FH="${F}/sdlc-spdd"
assert_dir "${FH}" "F v3 home from init/setup"
printf '%s\n' '# project canvas' > "${FH}/spdd/canvas/FRESH-001.md"
"${UPGRADE}" --target "${F}" --cursor --no-backup >/dev/null
assert_absent "${F}" "requirements" "F no root requirements"
assert_absent "${F}" "spdd" "F no root spdd"
assert_file_contains "${FH}/spdd/canvas/FRESH-001.md" "project canvas" "F project content kept"
if "${VERIFY}" --target "${F}" --require-cursor >/dev/null; then
  ok "F: verify passes on fresh v3 after upgrade"
else
  bad "F: verify failed on fresh v3 after upgrade"
fi

# ---------------------------------------------------------------------------
echo "== G. Nested helper unit suite =="
# ---------------------------------------------------------------------------
if "${REPO_ROOT}/tests/test-framework-install-consolidate.sh" >/dev/null; then
  ok "G: framework-install consolidate unit tests"
else
  bad "G: framework-install consolidate unit tests"
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
echo "All upgrade-consolidate tests passed."
