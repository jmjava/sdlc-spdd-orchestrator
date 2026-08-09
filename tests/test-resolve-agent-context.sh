#!/usr/bin/env bash
# Regression harness for resolve-agent-context.sh (harness/skills loader).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOLVE="${REPO_ROOT}/scripts/resolve-agent-context.sh"
# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/skills.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok() { echo "  OK: $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $1" >&2; fail=$((fail + 1)); }

assert_contains() {
  if grep -Fq "$2" <<< "$1"; then ok "$3"; else bad "$3 (missing: $2)"; fi
}

mkdir -p "${WORK}/harness/skills"

cat > "${WORK}/harness/skills/team-norms.md" <<'EOF'
---
skill: team-norms
aliases: _
phases: *
---
# Team norms
Always run tests before review.
EOF

cat > "${WORK}/harness/skills/coding-style.md" <<'EOF'
---
skill: coding-style
aliases: _
phases: code, api-test
---
# Coding style
Match surrounding module conventions.
EOF

cat > "${WORK}/harness/skills/TDD.md" <<'EOF'
---
skill: TDD
aliases: _
phases: code
---
# TDD
Write failing test first.
EOF

cp "${REPO_ROOT}/templates/agent-context/harness/skills/bugfix.md" \
  "${WORK}/harness/skills/"
cp "${REPO_ROOT}/templates/agent-context/harness/skills/pr-review.md" \
  "${WORK}/harness/skills/"
cp "${REPO_ROOT}/templates/agent-context/harness/phase-index.md" \
  "${WORK}/harness/phase-index.md"
cp "${REPO_ROOT}/agent-context/harness/quality-gates.md" "${WORK}/harness/" 2>/dev/null || \
  printf '# Quality Gates\n\n' > "${WORK}/harness/quality-gates.md"
# Tab-delimited skill metadata requires a non-empty aliases field when phases are present.
for skill in bugfix pr-review; do
  if ! grep -q '^aliases:' "${WORK}/harness/skills/${skill}.md"; then
    sed -i "/^skill: ${skill}/a aliases: ${skill}" "${WORK}/harness/skills/${skill}.md"
  fi
done

echo "== Test 1: phase skills for code =="
out="$("${RESOLVE}" --target "${WORK}" --phase code --format paths)"
assert_contains "${out}" "harness/skills/team-norms.md" "universal skill"
assert_contains "${out}" "harness/skills/coding-style.md" "coding skill"
assert_contains "${out}" "harness/skills/bugfix.md" "code phase bugfix skill"

echo "== Test 2: #SkillName resolves skill file =="
out="$("${RESOLVE}" --target "${WORK}" --text "Implement retry #TDD" --format paths)"
assert_contains "${out}" "harness/skills/TDD.md" "TDD skill file"

echo "== Test 3: !SkillName excludes included skill =="
out="$("${RESOLVE}" --target "${WORK}" --text "#TDD !TDD" --format paths)"
if grep -Fq "harness/skills/TDD.md" <<< "${out}"; then
  bad "excluded skill should not resolve"
else
  ok "excluded skill not resolved"
fi

echo "== Test 4: #bugfix resolves skill by name =="
out="$("${RESOLVE}" --target "${WORK}" --text "#bugfix" --format paths)"
assert_contains "${out}" "harness/skills/bugfix.md" "bugfix skill via #bugfix"

echo "== Test 5: --list-skills discovers skills =="
list="$("${RESOLVE}" --target "${WORK}" --list-skills)"
assert_contains "${list}" "TDD" "lists TDD skill"
assert_contains "${list}" "bugfix" "lists bugfix skill"

echo "== Test 6: review phase loads review skills only =="
mkdir -p "${WORK}/harness/skills"
cat > "${WORK}/harness/skills/review-checklist.md" <<'EOF'
---
skill: review-checklist
aliases: _
phases: review
---
# Review checklist
EOF
out="$("${RESOLVE}" --target "${WORK}" --phase review --format paths)"
assert_contains "${out}" "harness/skills/review-checklist.md" "review-checklist skill"
assert_contains "${out}" "harness/skills/pr-review.md" "pr-review skill"
if grep -Fq "coding-style.md" <<< "${out}"; then
  bad "review phase should not load coding-style"
else
  ok "coding-style excluded from review"
fi

echo "== Test 7: json format includes paths array =="
json="$("${RESOLVE}" --target "${WORK}" --phase code --format json)"
assert_contains "${json}" '"paths":[' "json paths key"
assert_contains "${json}" 'team-norms.md' "json contains resolved path"

echo "== Test 8: start-agent-session embeds Resolved Context =="
START="${REPO_ROOT}/scripts/start-agent-session.sh"
"${START}" --target "${WORK}" --work-id FEAT-099-test --phase code >/dev/null
if grep -Fq "## Resolved Context" "${WORK}/.sdlc/sessions/current-session.md" && \
   grep -Fq "team-norms.md" "${WORK}/.sdlc/sessions/current-session.md"; then
  ok "session brief includes resolved context"
else
  bad "session brief missing Resolved Context"
fi

echo "== Test 9: --work-id loads canvas and analysis =="
mkdir -p "${WORK}/spdd/analysis" "${WORK}/spdd/canvas"
cat > "${WORK}/spdd/analysis/FEAT-050-billing-analysis.md" <<'AN'
# Analysis Context: FEAT-050-billing

## Code Areas

- src/billing
AN
cat > "${WORK}/spdd/canvas/FEAT-050-billing.md" <<'CV'
# Canvas
CV
out="$("${RESOLVE}" --target "${WORK}" --phase code --work-id FEAT-050-billing --format paths)"
assert_contains "${out}" "spdd/canvas/FEAT-050-billing.md" "work-id canvas artifact"
assert_contains "${out}" "spdd/analysis/FEAT-050-billing-analysis.md" "work-id analysis artifact"

echo "== Test 10: api-test resolves tasks from phase-index =="
mkdir -p "${WORK}/spdd/tasks"
echo "# API tasks" > "${WORK}/spdd/tasks/FEAT-050-billing-api-test.md"
out="$("${RESOLVE}" --target "${WORK}" --phase api-test --work-id FEAT-050-billing --format paths)"
assert_contains "${out}" "spdd/tasks/FEAT-050-billing-api-test.md" "work-id api-test task"
assert_contains "${out}" "harness/quality-gates.md" "api-test quality gates from phase-index"

echo "== Test 11: resume prompt omits canvas when already resolved =="
"${START}" --target "${WORK}" --work-id FEAT-050-billing --phase code >/dev/null
if grep -Fq "Also read @spdd/canvas/FEAT-050-billing.md" "${WORK}/.sdlc/sessions/current-session.md"; then
  bad "resume prompt should not duplicate canvas already in Resolved Context"
else
  ok "resume prompt skips redundant canvas mention"
fi

echo "== Test 12: ledger progress excerpt resolves for work-id =="
mkdir -p "${WORK}/spdd/memory" "${WORK}/.sdlc/staged"
printf '%s\n' \
  '{"id":"progress:FEAT-050-billing:(none):capture","kind":"progress","work_id":"FEAT-050-billing","title":"T01 complete","ts":"2026-08-08T00:00:00Z"}' \
  > "${WORK}/spdd/memory/lessons.jsonl"
out="$("${RESOLVE}" --target "${WORK}" --phase code --work-id FEAT-050-billing --format paths)"
assert_contains "${out}" ".sdlc/resolved/progress-FEAT-050-billing.md" "scoped progress excerpt"
excerpt="${WORK}/.sdlc/resolved/progress-FEAT-050-billing.md"
if [[ -f "${excerpt}" ]]; then
  ok "scoped excerpt file exists"
  assert_contains "$(cat "${excerpt}")" "T01 complete" "excerpt includes this work"
else
  bad "scoped excerpt file missing"
fi

echo "== Test 13: legacy playbooks/extensions migrate idempotently =="
mkdir -p "${WORK}/agent-context/playbooks" "${WORK}/agent-context/extensions/_all-agents" \
  "${WORK}/agent-context/extensions/coding-agent" "${WORK}/agent-context/extensions/skills"
echo "# Legacy bug playbook" > "${WORK}/agent-context/playbooks/legacy-widget-playbook.md"
echo "# Legacy norm" > "${WORK}/agent-context/extensions/_all-agents/legacy-norm.md"
echo "# Legacy style" > "${WORK}/agent-context/extensions/coding-agent/legacy-style.md"
echo "# Legacy TDD" > "${WORK}/agent-context/extensions/skills/legacy-tdd.md"
rm -f "${WORK}/harness/skills/legacy-widget.md" \
  "${WORK}/harness/skills/legacy-norm.md" \
  "${WORK}/harness/skills/legacy-style.md" \
  "${WORK}/harness/skills/legacy-tdd.md"
migrate_playbooks_extensions_to_skills "${WORK}" 0
if [[ -f "${WORK}/harness/skills/legacy-widget.md" ]] && \
   [[ -f "${WORK}/harness/skills/legacy-norm.md" ]] && \
   [[ ! -d "${WORK}/agent-context/playbooks" ]] && \
   [[ ! -d "${WORK}/agent-context/extensions" ]]; then
  ok "legacy trees migrated and removed"
else
  bad "legacy migration failed"
fi
migrate_playbooks_extensions_to_skills "${WORK}" 0
if [[ -f "${WORK}/harness/skills/legacy-widget.md" ]]; then
  ok "second migrate is idempotent"
else
  bad "idempotent migrate broke skills"
fi

echo "== Test 14: session-handoff playbook is not migrated =="
mkdir -p "${WORK}/agent-context/playbooks"
echo "# Session handoff" > "${WORK}/agent-context/playbooks/session-handoff-playbook.md"
migrate_playbooks_extensions_to_skills "${WORK}" 0
if [[ ! -f "${WORK}/harness/skills/session-handoff.md" ]]; then
  ok "session-handoff skipped"
else
  bad "session-handoff should not migrate"
fi

echo
if (( fail > 0 )); then
  echo "${fail} failed, ${pass} passed" >&2
  exit 1
fi
echo "All ${pass} resolve-agent-context tests passed."
