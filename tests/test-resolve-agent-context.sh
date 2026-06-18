#!/usr/bin/env bash
# Regression harness for resolve-agent-context.sh (SDLC Agents skill + extension loader).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOLVE="${REPO_ROOT}/scripts/resolve-agent-context.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok() { echo "  OK: $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $1" >&2; fail=$((fail + 1)); }

assert_contains() {
  if grep -Fq "$2" <<< "$1"; then ok "$3"; else bad "$3 (missing: $2)"; fi
}

mkdir -p "${WORK}/agent-context/extensions/_all-agents" \
  "${WORK}/agent-context/extensions/coding-agent" \
  "${WORK}/agent-context/extensions/skills" \
  "${WORK}/agent-context/playbooks" \
  "${WORK}/agent-context/memory" \
  "${WORK}/agent-context/harness"

cat > "${WORK}/agent-context/extensions/_all-agents/team-norms.md" <<'EOF'
# Team norms
Always run tests before review.
EOF

cat > "${WORK}/agent-context/extensions/coding-agent/style.md" <<'EOF'
# Coding style
Match surrounding module conventions.
EOF

cat > "${WORK}/agent-context/extensions/skills/TDD.md" <<'EOF'
# TDD
Write failing test first.
EOF

cp "${REPO_ROOT}/agent-context/playbooks/bugfix-playbook.md" "${WORK}/agent-context/playbooks/"
cp "${REPO_ROOT}/agent-context/playbooks/pr-review-playbook.md" "${WORK}/agent-context/playbooks/"
cp "${REPO_ROOT}/agent-context/memory/known-pitfalls.md" "${WORK}/agent-context/memory/" 2>/dev/null || \
  printf '# Known Pitfalls\n\n' > "${WORK}/agent-context/memory/known-pitfalls.md"
cp "${REPO_ROOT}/agent-context/harness/quality-gates.md" "${WORK}/agent-context/harness/" 2>/dev/null || \
  printf '# Quality Gates\n\n' > "${WORK}/agent-context/harness/quality-gates.md"

echo "== Test 1: phase extensions + static playbooks for code =="
out="$("${RESOLVE}" --target "${WORK}" --phase code --format paths)"
assert_contains "${out}" "agent-context/extensions/_all-agents/team-norms.md" "all-agents extension"
assert_contains "${out}" "agent-context/extensions/coding-agent/style.md" "coding-agent extension"
assert_contains "${out}" "agent-context/playbooks/bugfix-playbook.md" "code phase playbook"

echo "== Test 2: #SkillName resolves extension skill =="
out="$("${RESOLVE}" --target "${WORK}" --text "Implement retry #TDD" --format paths)"
assert_contains "${out}" "agent-context/extensions/skills/TDD.md" "TDD skill file"

echo "== Test 3: !SkillName excludes included skill =="
out="$("${RESOLVE}" --target "${WORK}" --text "#TDD !TDD" --format paths)"
if grep -Fq "agent-context/extensions/skills/TDD.md" <<< "${out}"; then
  bad "excluded skill should not resolve"
else
  ok "excluded skill not resolved"
fi

echo "== Test 4: #java resolves playbook suffix =="
out="$("${RESOLVE}" --target "${WORK}" --text "#bugfix" --format paths)"
assert_contains "${out}" "agent-context/playbooks/bugfix-playbook.md" "bugfix playbook via #bugfix"

echo "== Test 5: --list-skills discovers skills and playbooks =="
list="$("${RESOLVE}" --target "${WORK}" --list-skills)"
assert_contains "${list}" "TDD" "lists TDD skill"
assert_contains "${list}" "bugfix" "lists bugfix playbook skill name"

echo "== Test 6: review phase uses codereview-agent folder =="
mkdir -p "${WORK}/agent-context/extensions/codereview-agent"
echo "# Review checklist" > "${WORK}/agent-context/extensions/codereview-agent/checklist.md"
out="$("${RESOLVE}" --target "${WORK}" --phase review --format paths)"
assert_contains "${out}" "agent-context/extensions/codereview-agent/checklist.md" "codereview-agent extension"
assert_contains "${out}" "agent-context/playbooks/pr-review-playbook.md" "review playbook"

echo "== Test 7: json format includes paths array =="
json="$("${RESOLVE}" --target "${WORK}" --phase code --format json)"
assert_contains "${json}" '"paths":[' "json paths key"
assert_contains "${json}" 'team-norms.md' "json contains resolved path"

echo "== Test 8: start-agent-session embeds Resolved Context =="
START="${REPO_ROOT}/scripts/start-agent-session.sh"
"${START}" --target "${WORK}" --work-id FEAT-099-test --phase code >/dev/null
if grep -Fq "## Resolved Context" "${WORK}/agent-context/sessions/current-session.md" && \
   grep -Fq "team-norms.md" "${WORK}/agent-context/sessions/current-session.md"; then
  ok "session brief includes resolved context"
else
  bad "session brief missing Resolved Context"
fi

echo "== Test 9: --work-id + context-index area filter =="
mkdir -p "${WORK}/spdd/analysis" "${WORK}/spdd/canvas" "${WORK}/agent-context/memory/sessions"
cat > "${WORK}/spdd/analysis/FEAT-050-billing-analysis.md" <<'AN'
# Analysis Context: FEAT-050-billing

## Code Areas

- src/billing
AN
cat > "${WORK}/spdd/canvas/FEAT-050-billing.md" <<'CV'
# Canvas
CV
cat > "${WORK}/agent-context/memory/context-index.md" <<'CTX'
# Context Index

| Area | Kind | Work ID | Phase | Timestamp | Source | Entry |
|------|------|---------|-------|-----------|--------|-------|
| src/billing | session | BUG-001 | code | 2026-01-01T00:00:00Z | spdd/canvas/BUG-001.md | agent-context/memory/sessions/20260101-code-BUG-001.md |
| src/payments | session | FEAT-002 | code | 2026-01-02T00:00:00Z | spdd/canvas/FEAT-002.md | agent-context/memory/sessions/20260102-code-FEAT-002.md |
CTX
echo "session detail" > "${WORK}/agent-context/memory/sessions/20260101-code-BUG-001.md"
out="$("${RESOLVE}" --target "${WORK}" --phase code --work-id FEAT-050-billing --format paths)"
assert_contains "${out}" "spdd/canvas/FEAT-050-billing.md" "work-id canvas artifact"
assert_contains "${out}" "agent-context/memory/sessions/20260101-code-BUG-001.md" "billing area session entry"
if grep -Fq "agent-context/memory/sessions/20260102-code-FEAT-002.md" <<< "${out}"; then
  bad "unrelated payments area should not resolve"
else
  ok "payments area excluded"
fi
md="$("${RESOLVE}" --target "${WORK}" --phase code --work-id FEAT-050-billing --format markdown)"
assert_contains "${md}" "Indexed context" "markdown index section"
if grep -Fq "known-pitfalls.md" <<< "${out}"; then
  bad "whole known-pitfalls should not load when area-scoped"
else
  ok "area-scoped skips whole pitfalls file"
fi

echo
if (( fail > 0 )); then
  echo "${fail} failed, ${pass} passed" >&2
  exit 1
fi
echo "All ${pass} resolve-agent-context tests passed."
