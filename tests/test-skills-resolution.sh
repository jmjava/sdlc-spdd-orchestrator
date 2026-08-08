#!/usr/bin/env bash
# harness/skills resolution: phase affinity, #SkillName, legacy migration.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESOLVE="${REPO_ROOT}/scripts/resolve-agent-context.sh"
# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/paths.sh"
# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/skills.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok() { echo "  OK: $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL: $1" >&2; fail=$((fail + 1)); }

setup_skills_fixture() {
  mkdir -p "${WORK}/agent-context/harness/skills" \
    "${WORK}/agent-context/harness"
  cp "${REPO_ROOT}/templates/agent-context/harness/phase-index.md" \
    "${WORK}/agent-context/harness/phase-index.md"
  cp "${REPO_ROOT}/templates/agent-context/harness/skills/bugfix.md" \
    "${WORK}/agent-context/harness/skills/"
  cp "${REPO_ROOT}/templates/agent-context/harness/skills/TDD.md" \
    "${WORK}/agent-context/harness/skills/"
  cp "${REPO_ROOT}/templates/agent-context/harness/skills/pr-review.md" \
    "${WORK}/agent-context/harness/skills/"
  cp "${REPO_ROOT}/agent-context/harness/quality-gates.md" "${WORK}/agent-context/harness/" 2>/dev/null || \
    printf '# Quality Gates\n\n' > "${WORK}/agent-context/harness/quality-gates.md"
  cat > "${WORK}/agent-context/harness/skills/team-norms.md" <<'EOF'
---
skill: team-norms
phases: *
---
# Team norms
Always run tests before review.
EOF
  cat > "${WORK}/agent-context/harness/skills/coding-style.md" <<'EOF'
---
skill: coding-style
phases: code, api-test
---
# Coding style
Match surrounding module conventions.
EOF
}

echo "== Test 1: phase loads core harness index + matching skills =="
setup_skills_fixture
out="$("${RESOLVE}" --target "${WORK}" --phase code --format paths)"
if grep -Fq "team-norms.md" <<< "${out}" && \
   grep -Fq "coding-style.md" <<< "${out}" && \
   grep -Fq "bugfix.md" <<< "${out}"; then
  ok "code phase resolves universal + coding skills"
else
  bad "code phase skills missing"
fi

echo "== Test 2: #SkillName resolves on-demand skill =="
out="$("${RESOLVE}" --target "${WORK}" --text "Implement retry #TDD" --format paths)"
if grep -Fq "agent-context/harness/skills/TDD.md" <<< "${out}"; then
  ok "TDD skill file resolved"
else
  bad "TDD skill missing"
fi

echo "== Test 3: !SkillName excludes included skill =="
out="$("${RESOLVE}" --target "${WORK}" --text "#TDD !TDD" --format paths)"
if grep -Fq "TDD.md" <<< "${out}"; then
  bad "excluded skill should not resolve"
else
  ok "excluded skill not resolved"
fi

echo "== Test 4: #bugfix resolves by skill name =="
out="$("${RESOLVE}" --target "${WORK}" --text "#bugfix" --format paths)"
if grep -Fq "bugfix.md" <<< "${out}"; then
  ok "bugfix skill via #bugfix"
else
  bad "bugfix skill missing"
fi

echo "== Test 5: --list-skills discovers names and aliases =="
list="$("${RESOLVE}" --target "${WORK}" --list-skills)"
if grep -Fq "TDD" <<< "${list}" && grep -Fq "bugfix" <<< "${list}" && grep -Fq "review" <<< "${list}"; then
  ok "lists skill names"
else
  bad "list-skills incomplete"
fi

echo "== Test 6: review phase loads pr-review skill only =="
cat > "${WORK}/agent-context/harness/skills/review-checklist.md" <<'EOF'
---
skill: review-checklist
phases: review
---
# Review checklist
EOF
out="$("${RESOLVE}" --target "${WORK}" --phase review --format paths)"
if grep -Fq "pr-review.md" <<< "${out}" && grep -Fq "review-checklist.md" <<< "${out}"; then
  ok "review phase skills"
else
  bad "review phase skills missing"
fi
if grep -Fq "coding-style.md" <<< "${out}"; then
  bad "review phase should not load coding-style"
else
  ok "review excludes coding skills"
fi

echo "== Test 7: legacy playbooks/extensions migrate idempotently =="
mkdir -p "${WORK}/agent-context/playbooks" "${WORK}/agent-context/extensions/_all-agents" \
  "${WORK}/agent-context/extensions/coding-agent" "${WORK}/agent-context/extensions/skills"
echo "# Legacy bug playbook" > "${WORK}/agent-context/playbooks/legacy-widget-playbook.md"
echo "# Legacy norm" > "${WORK}/agent-context/extensions/_all-agents/legacy-norm.md"
echo "# Legacy style" > "${WORK}/agent-context/extensions/coding-agent/legacy-style.md"
echo "# Legacy TDD" > "${WORK}/agent-context/extensions/skills/legacy-tdd.md"
rm -f "${WORK}/agent-context/harness/skills/legacy-widget.md" \
  "${WORK}/agent-context/harness/skills/legacy-norm.md" \
  "${WORK}/agent-context/harness/skills/legacy-style.md" \
  "${WORK}/agent-context/harness/skills/legacy-tdd.md"
migrate_playbooks_extensions_to_skills "${WORK}" 0
if [[ -f "${WORK}/agent-context/harness/skills/legacy-widget.md" ]] && \
   [[ -f "${WORK}/agent-context/harness/skills/legacy-norm.md" ]] && \
   [[ ! -d "${WORK}/agent-context/playbooks" ]] && \
   [[ ! -d "${WORK}/agent-context/extensions" ]]; then
  ok "legacy trees migrated and removed"
else
  bad "legacy migration failed"
fi
migrate_playbooks_extensions_to_skills "${WORK}" 0
if [[ -f "${WORK}/agent-context/harness/skills/legacy-widget.md" ]]; then
  ok "second migrate is idempotent"
else
  bad "idempotent migrate broke skills"
fi

echo "== Test 8: session-handoff playbook is not migrated =="
mkdir -p "${WORK}/agent-context/playbooks"
echo "# Session handoff" > "${WORK}/agent-context/playbooks/session-handoff-playbook.md"
migrate_playbooks_extensions_to_skills "${WORK}" 0
if [[ ! -f "${WORK}/agent-context/harness/skills/session-handoff.md" ]]; then
  ok "session-handoff skipped"
else
  bad "session-handoff should not migrate"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if (( fail > 0 )); then exit 1; fi
echo "All skills resolution tests passed."
