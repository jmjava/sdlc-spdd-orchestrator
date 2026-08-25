#!/usr/bin/env bash
# Unit tests for storage-v3 consolidate/archive helpers in framework-install.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=../scripts/lib/framework-install.sh
source "${REPO_ROOT}/scripts/lib/framework-install.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

echo "== framework_is_orchestrator_root =="
if framework_is_orchestrator_root "${REPO_ROOT}"; then
  ok "detects this orchestrator repo"
else
  bad "failed to detect orchestrator repo"
fi
mkdir -p "${WORK}/plain"
if ! framework_is_orchestrator_root "${WORK}/plain"; then
  ok "rejects plain target"
else
  bad "false positive orchestrator detect"
fi

echo "== framework_consolidate_path: move when dest missing =="
mkdir -p "${WORK}/t1/src-dir"
echo move-me > "${WORK}/t1/src-dir/a.txt"
line="$(framework_consolidate_path "${WORK}/t1/src-dir" "${WORK}/t1/dest-dir" 0 "${WORK}/t1")"
if [[ "${line}" == move\ * && -f "${WORK}/t1/dest-dir/a.txt" && ! -e "${WORK}/t1/src-dir" ]]; then
  ok "move when dest missing"
else
  bad "move when dest missing (got: ${line})"
fi

echo "== framework_consolidate_path: merge dirs, dest wins on conflict =="
mkdir -p "${WORK}/t2/src/sub" "${WORK}/t2/dest/sub"
echo from-src-only > "${WORK}/t2/src/only-src.txt"
echo from-dest > "${WORK}/t2/dest/conflict.txt"
echo from-src > "${WORK}/t2/src/conflict.txt"
echo nested-src > "${WORK}/t2/src/sub/nested.txt"
echo nested-dest > "${WORK}/t2/dest/sub/keep.txt"
framework_consolidate_path "${WORK}/t2/src" "${WORK}/t2/dest" 0 "${WORK}/t2" >/dev/null
if [[ -f "${WORK}/t2/dest/only-src.txt" \
   && "$(cat "${WORK}/t2/dest/conflict.txt")" == "from-dest" \
   && -f "${WORK}/t2/dest/sub/nested.txt" \
   && -f "${WORK}/t2/dest/sub/keep.txt" \
   && ! -e "${WORK}/t2/src" ]]; then
  ok "merge dirs with dest-wins conflict"
else
  bad "merge dirs with dest-wins conflict"
fi

echo "== framework_consolidate_path: dry-run leaves source =="
mkdir -p "${WORK}/t3/src"
echo x > "${WORK}/t3/src/f.txt"
framework_consolidate_path "${WORK}/t3/src" "${WORK}/t3/dest" 1 "${WORK}/t3" >/dev/null 2>&1
if [[ -f "${WORK}/t3/src/f.txt" && ! -e "${WORK}/t3/dest" ]]; then
  ok "dry-run consolidate does not move"
else
  bad "dry-run consolidate mutated tree"
fi

echo "== framework_archive_legacy_path =="
mkdir -p "${WORK}/t4/home/.sdlc" "${WORK}/t4/requirements"
echo req > "${WORK}/t4/requirements/r.md"
line="$(framework_archive_legacy_path "${WORK}/t4" "${WORK}/t4/home" "requirements" "STAMP1" 0)"
if [[ "${line}" == archive\ requirements\ -\>* \
   && -f "${WORK}/t4/home/.sdlc/legacy-layout-archive/STAMP1/requirements/r.md" \
   && ! -e "${WORK}/t4/requirements" ]]; then
  ok "archive moves leftover under legacy-layout-archive"
else
  bad "archive legacy path (got: ${line})"
fi

echo "== framework_archive_remaining_legacy_layout archives agent-context always =="
mkdir -p "${WORK}/t5/home/.sdlc" "${WORK}/t5/agent-context/custom"
echo custom > "${WORK}/t5/agent-context/custom/n.md"
echo roadmap > "${WORK}/t5/ROADMAP.md"
framework_archive_remaining_legacy_layout "${WORK}/t5" "${WORK}/t5/home" 0 "STAMP2" >/dev/null
if [[ ! -e "${WORK}/t5/agent-context" \
   && ! -e "${WORK}/t5/ROADMAP.md" \
   && -f "${WORK}/t5/home/.sdlc/legacy-layout-archive/STAMP2/agent-context/custom/n.md" ]]; then
  ok "target archives agent-context + ROADMAP leftovers"
else
  bad "target archive remaining leftovers"
fi

# Fake orchestrator: agent-context still archived; root scripts/ kept.
mkdir -p "${WORK}/t6/home/.sdlc" \
  "${WORK}/t6/agent-context/harness" \
  "${WORK}/t6/scripts" \
  "${WORK}/t6/templates" \
  "${WORK}/t6/engine" \
  "${WORK}/t6/requirements"
: > "${WORK}/t6/scripts/init-project.sh"
: > "${WORK}/t6/scripts/upgrade-project.sh"
echo keep-src > "${WORK}/t6/agent-context/harness/quality-gates.md"
echo leftover-req > "${WORK}/t6/requirements/x.md"
printf '%s\n' '# keep' > "${WORK}/t6/scripts/keep-me.sh"
framework_archive_remaining_legacy_layout "${WORK}/t6" "${WORK}/t6/home" 0 "STAMP3" >/dev/null
if [[ ! -e "${WORK}/t6/agent-context" \
   && -f "${WORK}/t6/scripts/keep-me.sh" \
   && ! -e "${WORK}/t6/requirements" \
   && -f "${WORK}/t6/home/.sdlc/legacy-layout-archive/STAMP3/agent-context/harness/quality-gates.md" \
   && -f "${WORK}/t6/home/.sdlc/legacy-layout-archive/STAMP3/requirements/x.md" ]]; then
  ok "orchestrator archives agent-context; keeps root scripts/"
else
  bad "orchestrator archive remaining leftovers"
fi

echo "== framework_rewrite_adapter_paths (no GNU sed -i) =="
cat > "${WORK}/rewrite.md" <<'EOF'
See ./scripts/sdlc.sh and docs/sdlc-spdd/foo.md
Then spdd/canvas/ and .sdlc/staged/lessons.jsonl
Also requirements/x.md session-notes/ and ROADMAP.md
EOF
framework_rewrite_adapter_paths "${WORK}/rewrite.md"
got="$(cat "${WORK}/rewrite.md")"
if grep -Fq './sdlc-spdd/scripts/sdlc.sh' "${WORK}/rewrite.md" \
  && grep -Fq 'sdlc-spdd/docs/foo.md' "${WORK}/rewrite.md" \
  && grep -Fq 'sdlc-spdd/spdd/canvas/' "${WORK}/rewrite.md" \
  && grep -Fq 'sdlc-spdd/.sdlc/staged/lessons.jsonl' "${WORK}/rewrite.md" \
  && grep -Fq 'sdlc-spdd/requirements/x.md' "${WORK}/rewrite.md" \
  && grep -Fq 'sdlc-spdd/session-notes/' "${WORK}/rewrite.md" \
  && grep -Fq 'sdlc-spdd/ROADMAP.md' "${WORK}/rewrite.md"; then
  ok "rewrites adapter paths without sed -i"
else
  bad "rewrite failed: ${got}"
fi

echo
echo "Results: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  exit 1
fi
echo "All framework-install consolidate unit tests passed."
