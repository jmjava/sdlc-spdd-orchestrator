#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: verify-project-install.sh [--target <path>] [--require-cursor] [--require-copilot]

Verify that a target project has the SDLC-SPDD three-part scaffold installed.

Checks Planning artifacts (roadmap, milestones, requirements/milestones/, session
notes), SPDD folders, SDLC memory/session/playbooks, runtime scripts, and docs.

Options:
  --target <path>       Target project path (default: .)
  --require-cursor      Fail if Cursor commands are missing
  --require-copilot     Fail if GitHub Copilot prompt files are missing
  --help                Print this help message

Examples:
  ./scripts/verify-project-install.sh --target /path/to/app
  ./scripts/sdlc-spdd/verify-project-install.sh --target . --require-cursor

Exit 0 when all required checks pass; non-zero otherwise.
EOF
}

TARGET="."
REQUIRE_CURSOR=0
REQUIRE_COPILOT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --require-cursor)
      REQUIRE_CURSOR=1
      shift
      ;;
    --require-copilot)
      REQUIRE_COPILOT=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

TARGET="$(cd "${TARGET}" && pwd)"

failures=0
checks=0

check_path() {
  local part="$1"
  local label="$2"
  local path="$3"
  local kind="${4:-any}"

  checks=$((checks + 1))
  local full="${TARGET}/${path}"

  case "${kind}" in
    dir)
      if [[ -d "${full}" ]]; then
        echo "  ok  ${label}: ${path}/"
        return 0
      fi
      ;;
    file)
      if [[ -f "${full}" ]]; then
        echo "  ok  ${label}: ${path}"
        return 0
      fi
      ;;
    executable)
      if [[ -f "${full}" && -x "${full}" ]]; then
        echo "  ok  ${label}: ${path}"
        return 0
      fi
      if [[ -f "${full}" ]]; then
        echo "  fail ${label}: ${path} (exists but not executable)"
        failures=$((failures + 1))
        return 1
      fi
      ;;
    glob)
      shopt -s nullglob
      local matches=("${TARGET}"/${path})
      shopt -u nullglob
      if ((${#matches[@]} > 0)); then
        echo "  ok  ${label}: ${path}"
        return 0
      fi
      ;;
  esac

  echo "  fail ${label}: ${path}"
  failures=$((failures + 1))
  return 1
}

run_part() {
  local title="$1"
  shift
  echo "${title}"
  while [[ $# -ge 4 ]]; do
    check_path "$1" "$2" "$3" "$4"
    shift 4
  done
  echo
}

echo "Verifying SDLC-SPDD install: ${TARGET}"
echo

run_part "Planning (inform and summarize)" \
  Planning "requirements directory" "requirements" dir \
  Planning "milestone requirements directory" "requirements/milestones" dir \
  Planning "milestone requirements README" "requirements/milestones/README.md" file \
  Planning "session notes directory" "session-notes" dir \
  Planning "roadmap file" "ROADMAP.md" file \
  Planning "milestone file" "milestone-*.md" glob

run_part "SPDD (govern and remember)" \
  SPDD "canvas directory" "spdd/canvas" dir \
  SPDD "tasks directory" "spdd/tasks" dir \
  SPDD "reviews directory" "spdd/reviews" dir \
  SPDD "sync directory" "spdd/sync" dir

run_part "SDLC (sessions, memory, playbooks)" \
  SDLC "memory directory" "agent-context/memory" dir \
  SDLC "sessions directory" "agent-context/sessions" dir \
  SDLC "playbooks directory" "agent-context/playbooks" dir \
  SDLC "features directory" "agent-context/features" dir \
  SDLC "harness directory" "agent-context/harness" dir \
  SDLC "project memory file" "agent-context/memory/project-memory.md" file \
  SDLC "session handoff playbook" "agent-context/playbooks/session-handoff-playbook.md" file \
  SDLC "quality gates" "agent-context/harness/quality-gates.md" file

run_part "Runtime scripts and docs" \
  Runtime "runtime scripts directory" "scripts/sdlc-spdd" dir \
  Runtime "target-local docs" "docs/sdlc-spdd" dir \
  Runtime "target docs hub" "docs/sdlc-spdd/README.md" file \
  Runtime "three-part operating path doc" "docs/sdlc-spdd/three-part-operating-path.md" file \
  Runtime "start session script" "scripts/sdlc-spdd/start-agent-session.sh" executable \
  Runtime "capture memory script" "scripts/sdlc-spdd/capture-session-memory.sh" executable \
  Runtime "create work from milestone script" "scripts/sdlc-spdd/create-work-from-milestone.sh" executable \
  Runtime "sync roadmap script" "scripts/sdlc-spdd/sync-roadmap-from-spdd.sh" executable \
  Runtime "summarize session notes script" "scripts/sdlc-spdd/summarize-session-notes.sh" executable \
  Runtime "validate canvas script" "scripts/sdlc-spdd/validate-reasons-canvas.sh" executable \
  Runtime "verify install script" "scripts/sdlc-spdd/verify-project-install.sh" executable

if [[ "${REQUIRE_CURSOR}" -eq 1 ]]; then
  run_part "Cursor adapter" \
    Cursor "plan command" ".cursor/commands/sdlc-spdd-plan.md" file \
    Cursor "init command" ".cursor/commands/sdlc-spdd-init.md" file
fi

if [[ "${REQUIRE_COPILOT}" -eq 1 ]]; then
  run_part "GitHub Copilot adapter" \
    Copilot "copilot instructions" ".github/copilot-instructions.md" file \
    Copilot "plan prompt" ".github/prompts/sdlc-spdd-plan.prompt.md" file
fi

echo "Summary: $((checks - failures))/${checks} checks passed"

if [[ "${failures}" -gt 0 ]]; then
  echo "Install verification failed (${failures} missing or invalid items)." >&2
  echo "Re-run init or upgrade from the orchestrator repository:" >&2
  echo "  ./scripts/setup-agent-prompts.sh --target ${TARGET} --all" >&2
  echo "See docs/sdlc-spdd/installing-into-your-project.md" >&2
  exit 1
fi

echo "Install verification passed."
exit 0
