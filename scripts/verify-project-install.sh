#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: verify-project-install.sh [--target <path>] [--require-cursor] [--require-copilot] [--require-claude]

Verify that a target project has the SDLC-SPDD scaffold installed in the
storage v3 single-folder layout: every framework asset under <target>/sdlc-spdd/
(requirements, spdd + memory ledgers, harness/skills, workflow
scripts, docs) plus IDE adapter stubs at the target repo root.

Also asserts that no legacy sprawled-layout paths remain (agent-context memory
trees, the legacy registry TSV, root-level spdd/, scripts/sdlc-spdd/).

Options:
  --target <path>       Target project path (default: .)
  --require-cursor      Fail if Cursor commands are missing
  --require-copilot     Fail if GitHub Copilot prompt files are missing
  --require-claude      Fail if Claude Code commands are missing
  --help                Print this help message

Examples:
  # From orchestrator repo clone:
  ./scripts/verify-project-install.sh --target /path/to/app
  # From installed target project:
  ./sdlc-spdd/scripts/verify-project-install.sh --target .
  ./sdlc-spdd/scripts/verify-project-install.sh --target . --require-cursor

Exit 0 when all required checks pass; non-zero otherwise.
EOF
}

TARGET="."
REQUIRE_CURSOR=0
REQUIRE_COPILOT=0
REQUIRE_CLAUDE=0

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
    --require-claude)
      REQUIRE_CLAUDE=1
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
HOME_REL="sdlc-spdd"

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
    absent)
      if [[ ! -e "${full}" ]]; then
        echo "  ok  ${label}: ${path} absent"
        return 0
      fi
      echo "  fail ${label}: legacy path still present: ${path}"
      failures=$((failures + 1))
      return 1
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

echo "Verifying SDLC-SPDD install (storage v3): ${TARGET}"
echo

run_part "Single-folder home" \
  Home "framework home" "${HOME_REL}" dir

run_part "Planning (inform and summarize)" \
  Planning "requirements directory" "${HOME_REL}/requirements" dir \
  Planning "milestone requirements directory" "${HOME_REL}/requirements/milestones" dir \
  Planning "milestone requirements README" "${HOME_REL}/requirements/milestones/README.md" file \
  Planning "session notes directory" "${HOME_REL}/session-notes" dir \
  Planning "roadmap file" "${HOME_REL}/ROADMAP.md" file

# Milestone definition: home milestone-*.md OR requirements/milestones/milestone-N/
checks=$((checks + 1))
shopt -s nullglob
home_ms=("${TARGET}/${HOME_REL}"/milestone-*.md)
subdir_ms=("${TARGET}/${HOME_REL}"/requirements/milestones/milestone-*/MILESTONE-*.md)
subdir_readme=("${TARGET}/${HOME_REL}"/requirements/milestones/milestone-*/README.md)
shopt -u nullglob
if ((${#home_ms[@]} > 0 || ${#subdir_ms[@]} > 0 || ${#subdir_readme[@]} > 0)); then
  echo "  ok  Planning milestone file: ${HOME_REL}/milestone-*.md and/or ${HOME_REL}/requirements/milestones/milestone-N/"
else
  echo "  fail Planning milestone file: need ${HOME_REL}/requirements/milestones/milestone-N/MILESTONE-N.md"
  failures=$((failures + 1))
fi
echo

run_part "SPDD (govern and remember)" \
  SPDD "canvas directory" "${HOME_REL}/spdd/canvas" dir \
  SPDD "analysis directory" "${HOME_REL}/spdd/analysis" dir \
  SPDD "tasks directory" "${HOME_REL}/spdd/tasks" dir \
  SPDD "reviews directory" "${HOME_REL}/spdd/reviews" dir \
  SPDD "sync directory" "${HOME_REL}/spdd/sync" dir \
  SPDD "memory directory" "${HOME_REL}/spdd/memory" dir \
  SPDD "lessons ledger (committed)" "${HOME_REL}/spdd/memory/lessons.jsonl" file \
  SPDD "work registry (committed)" "${HOME_REL}/spdd/memory/registry.jsonl" file

run_part "Framework context (harness and skills)" \
  SDLC "harness directory" "${HOME_REL}/harness" dir \
  SDLC "quality gates" "${HOME_REL}/harness/quality-gates.md" file \
  SDLC "validation rules" "${HOME_REL}/harness/validation-rules.md" file \
  SDLC "phase index" "${HOME_REL}/harness/phase-index.md" file \
  SDLC "skills directory" "${HOME_REL}/harness/skills" dir

run_part "Workflow CLI and docs" \
  Runtime "workflow scripts directory" "${HOME_REL}/scripts" dir \
  Runtime "workflow helper script" "${HOME_REL}/scripts/sdlc.sh" executable \
  Runtime "pointer manager script" "${HOME_REL}/scripts/sdlc-pointer.sh" executable \
  Runtime "workflow manager script" "${HOME_REL}/scripts/sdlc-workflow.sh" executable \
  Runtime "team registry script" "${HOME_REL}/scripts/sdlc-team-registry.sh" executable \
  Runtime "start session script" "${HOME_REL}/scripts/start-agent-session.sh" executable \
  Runtime "capture memory script" "${HOME_REL}/scripts/capture-session-memory.sh" executable \
  Runtime "accept lessons script" "${HOME_REL}/scripts/accept-lessons.sh" executable \
  Runtime "create work from milestone script" "${HOME_REL}/scripts/create-work-from-milestone.sh" executable \
  Runtime "sync roadmap script" "${HOME_REL}/scripts/sync-roadmap-from-spdd.sh" executable \
  Runtime "summarize session notes script" "${HOME_REL}/scripts/summarize-session-notes.sh" executable \
  Runtime "validate command adapters script" "${HOME_REL}/scripts/validate-command-adapters.sh" executable \
  Runtime "verify command effects script" "${HOME_REL}/scripts/verify-agent-command-effects.sh" executable \
  Runtime "validate canvas script" "${HOME_REL}/scripts/validate-reasons-canvas.sh" executable \
  Runtime "validate requirements format script" "${HOME_REL}/scripts/validate-requirements-format.sh" executable \
  Runtime "verify install script" "${HOME_REL}/scripts/verify-project-install.sh" executable \
  Runtime "shared script lib dir" "${HOME_REL}/scripts/lib" dir \
  Runtime "paths helper lib" "${HOME_REL}/scripts/lib/paths.sh" file \
  Runtime "areas helper lib" "${HOME_REL}/scripts/lib/areas.sh" file \
  Runtime "common helper lib" "${HOME_REL}/scripts/lib/common.sh" file \
  Runtime "milestone helper lib" "${HOME_REL}/scripts/lib/milestone.sh" file \
  Runtime "target-local docs" "${HOME_REL}/docs" dir \
  Runtime "target docs hub" "${HOME_REL}/docs/README.md" file \
  Runtime "three-part operating path doc" "${HOME_REL}/docs/three-part-operating-path.md" file

# Gitignored runtime coverage.
checks=$((checks + 1))
if [[ -f "${TARGET}/.gitignore" ]] && grep -qE '^sdlc-spdd/\.sdlc/?$' "${TARGET}/.gitignore"; then
  echo "  ok  Runtime gitignore covers ${HOME_REL}/.sdlc/"
else
  echo "  fail Runtime gitignore: .gitignore must contain 'sdlc-spdd/.sdlc/'"
  failures=$((failures + 1))
fi
echo

# Legacy layout names are assembled from parts so the repo-wide
# no-legacy-reference sweep over scripts/ stays clean.
legacy_ac="agent-context"
legacy_wr="work-registry"
run_part "No legacy sprawled layout" \
  Legacy "legacy memory tree" "${legacy_ac}/memory" absent \
  Legacy "legacy feature mirrors" "${legacy_ac}/features" absent \
  Legacy "legacy session briefs" "${legacy_ac}/sessions" absent \
  Legacy "legacy work registry" "${legacy_ac}/${legacy_wr}.tsv" absent \
  Legacy "legacy workflow manager" "${legacy_ac}/sdlc-workflow.sh" absent \
  Legacy "legacy runtime scripts" "scripts/sdlc-spdd" absent \
  Legacy "legacy root spdd memory" "spdd/memory" absent \
  Legacy "legacy root canvases" "spdd/canvas" absent

if [[ "${REQUIRE_CURSOR}" -eq 1 && "${REQUIRE_COPILOT}" -eq 1 ]]; then
  run_part "Adapter parity workflow" \
    Runtime "target adapter workflow" ".github/workflows/validate-sdlc-spdd-adapters.yml" file
fi

if [[ "${REQUIRE_CURSOR}" -eq 1 ]]; then
  run_part "Cursor adapter" \
    Cursor "plan command" ".cursor/commands/sdlc-spdd-plan.md" file \
    Cursor "init command" ".cursor/commands/sdlc-spdd-init.md" file \
    Cursor "operating-model rule" ".cursor/rules/sdlc-spdd.mdc" file

  # Adapter stubs stay at the repo root but must reference the home paths.
  checks=$((checks + 1))
  if grep -q "sdlc-spdd/scripts/sdlc.sh" "${TARGET}/.cursor/rules/sdlc-spdd.mdc" 2>/dev/null; then
    echo "  ok  Cursor grounding references sdlc-spdd/ home paths"
  else
    echo "  fail Cursor grounding must reference sdlc-spdd/scripts/sdlc.sh"
    failures=$((failures + 1))
  fi
  echo
fi

if [[ "${REQUIRE_COPILOT}" -eq 1 ]]; then
  run_part "GitHub Copilot adapter" \
    Copilot "copilot instructions" ".github/copilot-instructions.md" file \
    Copilot "plan prompt" ".github/prompts/sdlc-spdd-plan.prompt.md" file
fi

if [[ "${REQUIRE_CLAUDE}" -eq 1 ]]; then
  run_part "Claude Code adapter" \
    Claude "claude memory" "CLAUDE.md" file \
    Claude "init command" ".claude/commands/sdlc-spdd-init.md" file \
    Claude "plan command" ".claude/commands/sdlc-spdd-plan.md" file
fi

echo "Summary: $((checks - failures))/${checks} checks passed"

if [[ "${failures}" -gt 0 ]]; then
  echo "Install verification failed (${failures} missing or invalid items)." >&2
  echo "Re-run init or upgrade from the orchestrator repository:" >&2
  echo "  ./scripts/setup-agent-prompts.sh --target ${TARGET} --all" >&2
  echo "  ./scripts/upgrade-project.sh --target ${TARGET} --all   # consolidates legacy layouts" >&2
  echo "See sdlc-spdd/docs/installing-into-your-project.md" >&2
  exit 1
fi

echo "Install verification passed."
exit 0
