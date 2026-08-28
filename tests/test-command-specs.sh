#!/usr/bin/env bash
# Edge / contract tests for slash-command specs + generated adapters (FEAT-002).
#
# Complements validate-command-adapters.sh (parity/guardrails) and
# generate-command-adapters.sh --check (staleness) with:
#   - spec inventory ↔ template inventory
#   - shared-block semantic contracts in specs
#   - generator --check negative (stale template)
#   - validator negative when a semantic contract is stripped
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC_DIR="${REPO_ROOT}/spec/commands"
GEN="${REPO_ROOT}/scripts/generate-command-adapters.sh"
VALIDATE="${REPO_ROOT}/scripts/validate-command-adapters.sh"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

assert_file() {
  if [[ -f "$1" ]]; then ok "exists: ${1#${REPO_ROOT}/}"; else bad "missing: ${1#${REPO_ROOT}/}"; fi
}

assert_contains() {
  local file="$1" needle="$2" label="$3"
  if [[ -f "${file}" ]] && grep -Fq -- "${needle}" "${file}"; then
    ok "${label}"
  else
    bad "${label} (missing in ${file#${REPO_ROOT}/})"
  fi
}

expect_pass() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then ok "passes: ${label}"; else bad "expected pass: ${label}"; fi
}

expect_fail() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then bad "expected FAIL but passed: ${label}"; else ok "correctly fails: ${label}"; fi
}

# ---------------------------------------------------------------------------
echo "== Spec inventory and required front matter =="
shopt -s nullglob
specs=( "${SPEC_DIR}"/*.spec.md )
shopt -u nullglob
if ((${#specs[@]} >= 16)); then
  ok "spec count >= 16 (${#specs[@]})"
else
  bad "expected >=16 specs, got ${#specs[@]}"
fi

for spec in "${specs[@]}"; do
  base="$(basename "${spec}")"
  family="$(awk '/^family:/{sub(/^family:[[:space:]]*/,""); print; exit}' "${spec}")"
  slug="$(awk '/^slug:/{sub(/^slug:[[:space:]]*/,""); print; exit}' "${spec}")"
  if [[ -z "${family}" || -z "${slug}" ]]; then
    bad "${base}: missing family/slug"
    continue
  fi
  if [[ "${base}" != "${family}-${slug}.spec.md" ]]; then
    bad "${base}: name should be ${family}-${slug}.spec.md"
  else
    ok "${base} matches family/slug"
  fi
  # Must have titles for all three adapters + Required Behavior + Output somewhere
  for block in cursor:title copilot:title claude:title; do
    if grep -Fq -- "---BLOCK:${block}---" "${spec}"; then
      ok "${base} has ${block}"
    else
      bad "${base} missing ${block}"
    fi
  done
  if grep -Eq -- '---BLOCK:(shared|cursor|copilot|claude):Required Behavior---' "${spec}"; then
    ok "${base} has Required Behavior block"
  else
    bad "${base} missing Required Behavior block"
  fi
  if grep -Eq -- '---BLOCK:(shared|cursor|copilot|claude):Output---' "${spec}"; then
    ok "${base} has Output block"
  else
    bad "${base} missing Output block"
  fi

  case "${family}" in
    lifecycle)
      assert_file "${REPO_ROOT}/templates/cursor/sdlc-spdd-${slug}.md"
      assert_file "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-${slug}.prompt.md"
      assert_file "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-${slug}.md"
      ;;
    workflow)
      assert_file "${REPO_ROOT}/templates/cursor/sdlc-${slug}.md"
      assert_file "${REPO_ROOT}/templates/copilot/prompts/sdlc-${slug}.prompt.md"
      assert_file "${REPO_ROOT}/templates/claude/commands/sdlc-${slug}.md"
      ;;
    *)
      bad "${base}: unknown family '${family}'"
      ;;
  esac
done

# ---------------------------------------------------------------------------
echo "== Shared semantic contracts in specs =="
for spec in \
  "${SPEC_DIR}/lifecycle-whereami.spec.md" \
  "${SPEC_DIR}/workflow-next.spec.md"; do
  assert_contains "${spec}" 'Jira as `missing` or `draft`' \
    "$(basename "${spec}") encodes jira ask"
  assert_contains "${spec}" "claim --jira" \
    "$(basename "${spec}") encodes claim --jira"
done
assert_contains "${SPEC_DIR}/lifecycle-code.spec.md" "Ready For Coding" \
  "lifecycle-code encodes readiness gate"
assert_contains "${SPEC_DIR}/lifecycle-architect.spec.md" "Optional DIF check" \
  "lifecycle-architect encodes optional DIF gate"
assert_contains "${SPEC_DIR}/lifecycle-code.spec.md" "Optional DIF check" \
  "lifecycle-code encodes optional DIF gate"
assert_contains "${SPEC_DIR}/workflow-next.spec.md" "Optional DIF check" \
  "workflow-next encodes optional DIF gate"
assert_contains "${SPEC_DIR}/workflow-advance.spec.md" "Ready For Coding" \
  "workflow-advance encodes readiness gate"
assert_contains "${SPEC_DIR}/workflow-claim.spec.md" "--jira" \
  "workflow-claim encodes --jira"

# ---------------------------------------------------------------------------
echo "== Generated adapters carry contracts on all three packs =="
for adapter_file in \
  "${REPO_ROOT}/templates/cursor/sdlc-spdd-whereami.md" \
  "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-whereami.prompt.md" \
  "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-whereami.md" \
  "${REPO_ROOT}/templates/cursor/sdlc-next.md" \
  "${REPO_ROOT}/templates/copilot/prompts/sdlc-next.prompt.md" \
  "${REPO_ROOT}/templates/claude/commands/sdlc-next.md"; do
  assert_contains "${adapter_file}" 'Jira as `missing` or `draft`' \
    "jira ask in ${adapter_file#${REPO_ROOT}/templates/}"
done

for adapter_file in \
  "${REPO_ROOT}/templates/cursor/sdlc-spdd-code.md" \
  "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-code.prompt.md" \
  "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-code.md"; do
  assert_contains "${adapter_file}" "Ready For Coding" \
    "readiness in ${adapter_file#${REPO_ROOT}/templates/}"
  assert_contains "${adapter_file}" "Optional DIF check" \
    "optional DIF in ${adapter_file#${REPO_ROOT}/templates/}"
done

for adapter_file in \
  "${REPO_ROOT}/templates/cursor/sdlc-spdd-architect.md" \
  "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-architect.prompt.md" \
  "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-architect.md"; do
  assert_contains "${adapter_file}" "Optional DIF check" \
    "optional DIF in ${adapter_file#${REPO_ROOT}/templates/}"
done

# ---------------------------------------------------------------------------
echo "== Generator staleness check =="
expect_pass "generate --check clean tree" "${GEN}" --check

stale="${REPO_ROOT}/templates/cursor/sdlc-next.md"
bak="$(mktemp)"
cp "${stale}" "${bak}"
restore_stale() { cp "${bak}" "${stale}"; rm -f "${bak}"; }
trap 'restore_stale' EXIT
printf '\n# stale marker\n' >> "${stale}"
expect_fail "generate --check detects stale adapter" "${GEN}" --check
restore_stale
trap - EXIT

expect_pass "generate --check after restore" "${GEN}" --check
expect_pass "validate-command-adapters clean" "${VALIDATE}"

# ---------------------------------------------------------------------------
echo "== Validator catches stripped semantic contracts =="
victim="${REPO_ROOT}/templates/cursor/sdlc-spdd-whereami.md"
bak="$(mktemp)"
cp "${victim}" "${bak}"
restore_victim() { cp "${bak}" "${victim}"; rm -f "${bak}"; }
trap 'restore_victim' EXIT
# Remove the jira-ask step while keeping file otherwise valid enough to parse.
grep -Fv -- 'Jira as `missing` or `draft`' "${bak}" > "${victim}"
expect_fail "validate fails when whereami jira ask stripped" "${VALIDATE}"
restore_victim
trap - EXIT
expect_pass "validate after restore" "${VALIDATE}"

victim="${REPO_ROOT}/templates/cursor/sdlc-spdd-code.md"
bak="$(mktemp)"
cp "${victim}" "${bak}"
restore_victim() { cp "${bak}" "${victim}"; rm -f "${bak}"; }
trap 'restore_victim' EXIT
grep -Fv -- 'Ready For Coding' "${bak}" > "${victim}"
expect_fail "validate fails when code readiness stripped" "${VALIDATE}"
restore_victim
trap - EXIT
expect_pass "validate after code restore" "${VALIDATE}"

# ---------------------------------------------------------------------------
echo "== whereami / next Required Behavior step-count parity =="
# Shared blocks must expand to the same numbered step count across adapters.
count_rb() {
  awk '
    /^## Required Behavior[[:space:]]*$/ { in_section=1; next }
    /^## / { in_section=0 }
    in_section && /^[0-9]+\./ { count++ }
    END { print count+0 }
  ' "$1"
}
w_c="$(count_rb "${REPO_ROOT}/templates/cursor/sdlc-spdd-whereami.md")"
w_p="$(count_rb "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-whereami.prompt.md")"
w_l="$(count_rb "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-whereami.md")"
if [[ "${w_c}" -eq "${w_p}" && "${w_c}" -eq "${w_l}" && "${w_c}" -ge 10 ]]; then
  ok "whereami RB step-count parity (${w_c})"
else
  bad "whereami RB step-count mismatch cursor=${w_c} copilot=${w_p} claude=${w_l}"
fi
n_c="$(count_rb "${REPO_ROOT}/templates/cursor/sdlc-next.md")"
n_p="$(count_rb "${REPO_ROOT}/templates/copilot/prompts/sdlc-next.prompt.md")"
n_l="$(count_rb "${REPO_ROOT}/templates/claude/commands/sdlc-next.md")"
if [[ "${n_c}" -eq "${n_p}" && "${n_c}" -eq "${n_l}" && "${n_c}" -ge 10 ]]; then
  ok "next RB step-count parity (${n_c})"
else
  bad "next RB step-count mismatch cursor=${n_c} copilot=${n_p} claude=${n_l}"
fi
if [[ "${w_c}" -eq "${n_c}" ]]; then
  ok "whereami and next share same RB step count (${w_c})"
else
  bad "whereami (${w_c}) vs next (${n_c}) RB step count drift"
fi

# ---------------------------------------------------------------------------
echo "== Outcome enum lock (prompt-update + retro) =="
OUTCOME_ENUM='`improved` / `neutral` / `worse` / `unknown`'
for adapter_file in \
  "${REPO_ROOT}/templates/cursor/sdlc-spdd-prompt-update.md" \
  "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-prompt-update.prompt.md" \
  "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-prompt-update.md" \
  "${REPO_ROOT}/templates/cursor/sdlc-spdd-retro.md" \
  "${REPO_ROOT}/templates/copilot/prompts/sdlc-spdd-retro.prompt.md" \
  "${REPO_ROOT}/templates/claude/commands/sdlc-spdd-retro.md"; do
  assert_contains "${adapter_file}" "${OUTCOME_ENUM}" \
    "Outcome enum in ${adapter_file#${REPO_ROOT}/templates/}"
done
assert_contains "${SPEC_DIR}/lifecycle-prompt-update.spec.md" "${OUTCOME_ENUM}" \
  "prompt-update spec locks Outcome enum"
assert_contains "${SPEC_DIR}/lifecycle-retro.spec.md" "${OUTCOME_ENUM}" \
  "retro spec locks Outcome enum (single line)"

# ---------------------------------------------------------------------------
echo "== Per-command semantic contracts across packs =="
assert_contains "${REPO_ROOT}/templates/cursor/sdlc-spdd-analysis.md" "index-spdd-analysis.sh" \
  "analysis index script"
assert_contains "${REPO_ROOT}/templates/cursor/sdlc-spdd-plan.md" "Needs Analysis" \
  "plan Needs Analysis readiness"
assert_contains "${REPO_ROOT}/templates/cursor/sdlc-spdd-architect.md" "needs-analysis" \
  "architect canonical token"
assert_contains "${REPO_ROOT}/templates/cursor/sdlc-spdd-api-test.md" "spdd/tasks/" \
  "api-test task path"
assert_contains "${REPO_ROOT}/templates/cursor/sdlc-shelf.md" "shelf --reason" \
  "shelf reason flag"
assert_contains "${REPO_ROOT}/templates/cursor/sdlc-team.md" '[STALE>Nd]' \
  "team stale marker"

# ---------------------------------------------------------------------------
echo "== Generator edge cases (SPEC_DIR / TEMPLATE_ROOT overrides) =="
EDGE="$(mktemp -d)"
trap 'rm -rf "${EDGE}"' EXIT

# Empty spec dir
mkdir -p "${EDGE}/empty-specs" "${EDGE}/tpl"
expect_fail "generate fails on empty spec dir" \
  env SDLC_SPEC_DIR="${EDGE}/empty-specs" SDLC_TEMPLATE_ROOT="${EDGE}/tpl" \
  "${GEN}"

# Missing spec dir path
expect_fail "generate fails on missing --spec-dir" \
  "${GEN}" --spec-dir "${EDGE}/no-such-specs" --template-root "${EDGE}/tpl"

write_min_spec() {
  local path="$1"
  local family="${2:-lifecycle}"
  local slug="${3:-edge}"
  cat > "${path}" <<EOF
---
family: ${family}
slug: ${slug}
copilot_description: edge
copilot_mode: agent
claude_description: edge
---

---BLOCK:cursor:title---
/sdlc-spdd-${slug}
---END---
---BLOCK:copilot:title---
Edge ${slug}
---END---
---BLOCK:claude:title---
/sdlc-spdd-${slug}
---END---
---BLOCK:shared:Required Behavior---

1. Do the edge thing.
---END---
---BLOCK:shared:Output---

- edge output
---END---
EOF
}

# Unknown family
mkdir -p "${EDGE}/bad-family"
write_min_spec "${EDGE}/bad-family/bogus-edge.spec.md" "bogus" "edge"
expect_fail "generate fails on unknown family" \
  "${GEN}" --spec-dir "${EDGE}/bad-family" --template-root "${EDGE}/tpl-bad-family"

# Missing Required Behavior
mkdir -p "${EDGE}/no-rb"
cat > "${EDGE}/no-rb/lifecycle-norb.spec.md" <<'EOF'
---
family: lifecycle
slug: norb
copilot_description: edge
claude_description: edge
---
---BLOCK:cursor:title---
/sdlc-spdd-norb
---END---
---BLOCK:copilot:title---
No RB
---END---
---BLOCK:claude:title---
/sdlc-spdd-norb
---END---
---BLOCK:shared:Output---
- out
---END---
EOF
expect_fail "generate fails when Required Behavior missing" \
  "${GEN}" --spec-dir "${EDGE}/no-rb" --template-root "${EDGE}/tpl-norb"

# Missing title block
mkdir -p "${EDGE}/no-title"
cat > "${EDGE}/no-title/lifecycle-notitle.spec.md" <<'EOF'
---
family: lifecycle
slug: notitle
copilot_description: edge
claude_description: edge
---
---BLOCK:cursor:title---
/sdlc-spdd-notitle
---END---
---BLOCK:copilot:title---
No Title Claude missing
---END---
---BLOCK:shared:Required Behavior---
1. x
---END---
---BLOCK:shared:Output---
- out
---END---
EOF
expect_fail "generate fails when claude:title missing" \
  "${GEN}" --spec-dir "${EDGE}/no-title" --template-root "${EDGE}/tpl-notitle"

# Missing family/slug
mkdir -p "${EDGE}/no-meta"
cat > "${EDGE}/no-meta/lifecycle-nometa.spec.md" <<'EOF'
---
copilot_description: edge
claude_description: edge
---
---BLOCK:cursor:title---
/x
---END---
---BLOCK:copilot:title---
x
---END---
---BLOCK:claude:title---
/x
---END---
---BLOCK:shared:Required Behavior---
1. x
---END---
---BLOCK:shared:Output---
- out
---END---
EOF
expect_fail "generate fails when family/slug missing" \
  "${GEN}" --spec-dir "${EDGE}/no-meta" --template-root "${EDGE}/tpl-nometa"

# Happy path: valid minimal spec creates adapters under template root
mkdir -p "${EDGE}/ok-specs" "${EDGE}/ok-tpl"
write_min_spec "${EDGE}/ok-specs/lifecycle-edgeok.spec.md" "lifecycle" "edgeok"
expect_pass "generate creates adapters for valid minimal spec" \
  "${GEN}" --spec-dir "${EDGE}/ok-specs" --template-root "${EDGE}/ok-tpl"
assert_file "${EDGE}/ok-tpl/cursor/sdlc-spdd-edgeok.md"
assert_file "${EDGE}/ok-tpl/copilot/prompts/sdlc-spdd-edgeok.prompt.md"
assert_file "${EDGE}/ok-tpl/claude/commands/sdlc-spdd-edgeok.md"
assert_contains "${EDGE}/ok-tpl/cursor/sdlc-spdd-edgeok.md" "Do the edge thing." \
  "generated cursor RB body"
expect_pass "generate --check clean for temp tree" \
  "${GEN}" --check --spec-dir "${EDGE}/ok-specs" --template-root "${EDGE}/ok-tpl"
printf '\nstale\n' >> "${EDGE}/ok-tpl/cursor/sdlc-spdd-edgeok.md"
expect_fail "generate --check detects stale in temp tree" \
  "${GEN}" --check --spec-dir "${EDGE}/ok-specs" --template-root "${EDGE}/ok-tpl"

# Env override parity with flags
mkdir -p "${EDGE}/env-specs" "${EDGE}/env-tpl"
write_min_spec "${EDGE}/env-specs/workflow-envok.spec.md" "workflow" "envok"
expect_pass "generate via SDLC_* env overrides" \
  env SDLC_SPEC_DIR="${EDGE}/env-specs" SDLC_TEMPLATE_ROOT="${EDGE}/env-tpl" "${GEN}"
assert_file "${EDGE}/env-tpl/cursor/sdlc-envok.md"

rm -rf "${EDGE}"
trap - EXIT

# ---------------------------------------------------------------------------
echo
echo "Summary: ${pass} passed, ${fail} failed"
if (( fail > 0 )); then exit 1; fi
echo "All command-spec edge tests passed."
