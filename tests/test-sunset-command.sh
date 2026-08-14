#!/usr/bin/env bash
# Regression harness for /sdlc-spdd-sunset adapters + engine routing.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass=0
fail=0

ok() { echo "  OK: $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $1" >&2; fail=$((fail + 1)); }

assert_file() {
  if [[ -f "$1" ]]; then ok "file ${1#${REPO_ROOT}/}"; else bad "missing file $1"; fi
}

assert_contains() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if grep -Fq -- "${pattern}" "${path}" 2>/dev/null; then
    ok "${label}"
  else
    bad "${label} (missing in ${path#${REPO_ROOT}/}: ${pattern})"
  fi
}

CURSOR="${REPO_ROOT}/templates/cursor/sdlc-spdd-sunset.md"
COPILOT="${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-sunset.prompt.md"
CLAUDE="${REPO_ROOT}/templates/claude/commands/sdlc-spdd-sunset.md"
SPEC="${REPO_ROOT}/spec/commands/lifecycle-sunset.spec.md"
ENGINE="${REPO_ROOT}/engine/src/sdlc_engine/sunset.py"
SDLC_SH="${REPO_ROOT}/scripts/sdlc.sh"

echo "== Test 1: spec, adapters, and engine module exist =="
assert_file "${SPEC}"
assert_file "${CURSOR}"
assert_file "${COPILOT}"
assert_file "${CLAUDE}"
assert_file "${ENGINE}"

echo "== Test 2: engine delegation + ledger contract =="
for path in "${CURSOR}" "${COPILOT}" "${CLAUDE}"; do
  assert_contains "${path}" "Do not implement code" "no-code guardrail (${path##*/})"
  assert_contains "${path}" "sdlc.sh sunset" "engine delegation (${path##*/})"
  assert_contains "${path}" "GitHub PR" "GitHub PR collection (${path##*/})"
  assert_contains "${path}" "Jira" "Jira collection (${path##*/})"
  assert_contains "${path}" "lessons.jsonl" "ledger destination (${path##*/})"
  assert_contains "${path}" "--apply" "apply stages snapshot (${path##*/})"
done
assert_contains "${SDLC_SH}" 'sunset)' "sdlc.sh routes sunset to Python engine"

echo "== Test 3: generator --check and adapter validation =="
if "${REPO_ROOT}/scripts/generate-command-adapters.sh" --check >/dev/null; then
  ok "generate-command-adapters --check"
else
  bad "generate-command-adapters --check"
fi
if "${REPO_ROOT}/scripts/validate-command-adapters.sh" >/dev/null; then
  ok "validate-command-adapters"
else
  bad "validate-command-adapters"
fi

echo "== Test 4: engine sunset CLI smoke (isolated repo) =="
smoke_root="$(mktemp -d)"
trap 'rm -rf "${smoke_root}"' EXIT
git -C "${smoke_root}" init -q
git -C "${smoke_root}" config user.email "ci@example.com"
git -C "${smoke_root}" config user.name "CI"
printf '# smoke\n' > "${smoke_root}/README.md"
git -C "${smoke_root}" add README.md
git -C "${smoke_root}" commit -q -m "init"
mkdir -p "${smoke_root}/requirements/milestones" "${smoke_root}/spdd/canvas" "${smoke_root}/spdd/memory"
cat > "${smoke_root}/requirements/milestones/FEAT-014-feature-sunset.md" <<'EOF'
# Requirement: FEAT-014-feature-sunset

## Summary

Smoke sunset.

## Jira

- Key: ORCH-42
- Summary: Smoke sunset
EOF
printf '%s\n' '# REASONS Canvas: FEAT-014-feature-sunset' '' '## Final Status' '' '- Status: Complete' \
  > "${smoke_root}/spdd/canvas/FEAT-014-feature-sunset.md"
if PYTHONPATH="${REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
  python3 -m sdlc_engine --root "${smoke_root}" sunset --work-id FEAT-014-feature-sunset --apply \
  >/tmp/sdlc-sunset-smoke.out 2>/tmp/sdlc-sunset-smoke.err
then
  if grep -Fq 'sunset: FEAT-014-feature-sunset' /tmp/sdlc-sunset-smoke.out \
    && grep -Fq 'ORCH-42' /tmp/sdlc-sunset-smoke.out \
    && grep -Fq 'ledger:' /tmp/sdlc-sunset-smoke.out
  then
    ok "python -m sdlc_engine sunset --apply emits snapshot"
  else
    bad "engine output missing sunset snapshot"
  fi
  if [[ -f "${smoke_root}/.sdlc/staged/lessons.jsonl" ]] \
    && grep -Fq '"source": "sunset"' "${smoke_root}/.sdlc/staged/lessons.jsonl"
  then
    ok "sunset --apply staged a session record"
  else
    bad "sunset --apply did not stage a ledger record"
  fi
else
  bad "engine sunset unexpected failure: $(cat /tmp/sdlc-sunset-smoke.err)"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "sunset command regression tests FAILED." >&2
  exit 1
fi
echo "All sunset command regression tests passed."
