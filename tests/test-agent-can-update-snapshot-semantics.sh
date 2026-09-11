#!/usr/bin/env bash
# Leftover #12 proving test: agentCanUpdateSnapshot is Cursor schema
# ("Whether the agent can update the snapshot"), not a Builds on/off pin.
# Public Setup/Builds docs do not say this flag enables Builds.
# U2 must not hard-fail when the key is omitted or false.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="${REPO_ROOT}/tests/lib/agent_can_update_snapshot.py"
U2="${REPO_ROOT}/tests/test-cloud-environment.sh"
DOCS=(
  "${REPO_ROOT}/docs/maintaining-your-project.md"
  "${REPO_ROOT}/sdlc-spdd/docs/maintaining-your-project.md"
  "${REPO_ROOT}/docs/research/uberorchbot-via-sdlc-spdd.md"
)

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

classify() {
  python3 "${HELPER}" "$1"
}

write_env() {
  local path="$1"
  cat > "${path}"
}

echo "== leftover #12: agentCanUpdateSnapshot schema meaning =="

if [[ -f "${HELPER}" ]]; then
  ok "exists tests/lib/agent_can_update_snapshot.py"
else
  bad "missing ${HELPER}"
fi

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

echo "== test_omitted_flag_is_not_builds_failure =="
write_env "${scratch}/omitted.json" << 'EOF'
{"name": "fixture", "install": "bash .cursor/install.sh"}
EOF
if out="$(classify "${scratch}/omitted.json")"; then
  if grep -q '^status=omitted$' <<< "${out}"; then
    ok "omitted agentCanUpdateSnapshot is valid schema (not a Builds failure)"
  else
    bad "omitted classify output: ${out}"
  fi
else
  bad "omitted flag must not hard-fail"
fi

echo "== test_false_flag_is_not_builds_failure =="
write_env "${scratch}/false.json" << 'EOF'
{"name": "fixture", "install": "bash .cursor/install.sh", "agentCanUpdateSnapshot": false}
EOF
if out="$(classify "${scratch}/false.json")"; then
  if grep -q '^status=false$' <<< "${out}"; then
    ok "false agentCanUpdateSnapshot is valid schema (not Builds off)"
  else
    bad "false classify output: ${out}"
  fi
else
  bad "false flag must not hard-fail as Builds off"
fi

echo "== test_true_flag_is_schema_boolean =="
write_env "${scratch}/true.json" << 'EOF'
{"name": "fixture", "install": "bash .cursor/install.sh", "agentCanUpdateSnapshot": true}
EOF
if out="$(classify "${scratch}/true.json")"; then
  if grep -q '^status=true$' <<< "${out}"; then
    ok "true is a schema boolean, not a Builds-on pin"
  else
    bad "true classify output: ${out}"
  fi
else
  bad "true flag classify failed"
fi

echo "== test_non_boolean_flag_is_rejected =="
write_env "${scratch}/string.json" << 'EOF'
{"name": "fixture", "agentCanUpdateSnapshot": "true"}
EOF
if classify "${scratch}/string.json" >/dev/null 2>&1; then
  bad "string agentCanUpdateSnapshot must be rejected"
else
  ok "non-boolean agentCanUpdateSnapshot is rejected"
fi

echo "== test_docs_state_schema_meaning =="
schema_needle="Whether the agent can update the snapshot"
for doc in "${DOCS[@]}"; do
  if grep -Fq -- "${schema_needle}" "${doc}"; then
    ok "$(basename "${doc}") states schema meaning"
  else
    bad "$(basename "${doc}") missing schema meaning '${schema_needle}'"
  fi
done

echo "== test_u2_does_not_pin_builds_on =="
builds_pins=(
  "Builds enabled"
  "Builds stay enabled"
  "Builds on"
  "Cursor Builds can refresh"
  "documents Builds"
  "builds enabled"
  "must be true (Builds"
)
pin_files=(
  "${U2}"
  "${DOCS[@]}"
)
pin_hit=0
for pin in "${builds_pins[@]}"; do
  for f in "${pin_files[@]}"; do
    if grep -Fq -- "${pin}" "${f}"; then
      bad "pinned '${pin}' in ${f}"
      pin_hit=1
    fi
  done
done
if [[ "${pin_hit}" -eq 0 ]]; then
  ok "docs and U2 test do not pin agentCanUpdateSnapshot as Builds on"
fi

if grep -Eq 'agentCanUpdateSnapshot must be true|ENV_BUILDS' "${U2}"; then
  bad "U2 still hard-fails unless agentCanUpdateSnapshot is true"
else
  ok "U2 does not hard-fail when agentCanUpdateSnapshot is not true"
fi

if grep -Fq 'agent_can_update_snapshot.py' "${U2}"; then
  ok "U2 uses schema classifier"
else
  bad "U2 must classify the flag via tests/lib/agent_can_update_snapshot.py"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Leftover #12 snapshot-flag semantics FAILED." >&2
  exit 1
fi
echo "Leftover #12 snapshot-flag semantics passed."
