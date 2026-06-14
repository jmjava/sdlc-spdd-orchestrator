#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: validate-command-adapters.sh [--target <path>]

Validate Cursor + Copilot + Claude command-pack parity.

The Claude pack is validated when present (always in the orchestrator repo, and
in installed targets that opted into Claude Code).

Works in two contexts:
  1) Orchestrator repo (default): compares templates under templates/
  2) Installed target app: compares .cursor/commands, .github/prompts, and
     .claude/commands

Examples:
  ./scripts/validate-command-adapters.sh
  ./scripts/validate-command-adapters.sh --target /path/to/app
  ./scripts/sdlc-spdd/validate-command-adapters.sh --target .
EOF
}

TARGET="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
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

commands=(
  init
  plan
  architect
  code
  review
  prompt-update
  retro
  sync
)

failures=0

detect_roots() {
  if [[ -d "${TARGET}/templates/cursor" && -d "${TARGET}/templates/copilot/prompts" ]]; then
    CURSOR_ROOT="${TARGET}/templates/cursor"
    COPILOT_ROOT="${TARGET}/templates/copilot/prompts"
    CLAUDE_ROOT="${TARGET}/templates/claude/commands"
    MODE="orchestrator-templates"
  elif [[ -d "${TARGET}/.cursor/commands" && -d "${TARGET}/.github/prompts" ]]; then
    CURSOR_ROOT="${TARGET}/.cursor/commands"
    COPILOT_ROOT="${TARGET}/.github/prompts"
    CLAUDE_ROOT="${TARGET}/.claude/commands"
    MODE="installed-target"
  else
    echo "Could not find command packs in ${TARGET}." >&2
    echo "Need either templates/ (orchestrator) or .cursor/.github prompt dirs (target)." >&2
    exit 1
  fi

  # The Claude pack is optional in installed targets; validate it only when present.
  HAS_CLAUDE=0
  if [[ -d "${CLAUDE_ROOT}" ]]; then
    HAS_CLAUDE=1
  fi
}

cursor_path_for() {
  local cmd="$1"
  echo "${CURSOR_ROOT}/sdlc-spdd-${cmd}.md"
}

copilot_path_for() {
  local cmd="$1"
  echo "${COPILOT_ROOT}/sdlc-spdd-${cmd}.prompt.md"
}

claude_path_for() {
  local cmd="$1"
  echo "${CLAUDE_ROOT}/sdlc-spdd-${cmd}.md"
}

require_file() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    echo "Missing file: ${path}" >&2
    failures=$((failures + 1))
    return 1
  fi
  return 0
}

require_contains() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  if ! grep -Fq "${pattern}" "${path}"; then
    echo "Missing '${label}' in ${path}" >&2
    failures=$((failures + 1))
  fi
}

count_required_steps() {
  # Count numbered list items only within the "## Required Behavior" section,
  # stopping at the next "## " heading. Counting the whole file would let
  # numbered lists elsewhere (e.g. "## Output") inflate or mask divergence.
  local path="$1"
  awk '
    /^## Required Behavior[[:space:]]*$/ { in_section = 1; next }
    /^## / { in_section = 0 }
    in_section && /^[0-9]+\./ { count++ }
    END { print count + 0 }
  ' "${path}"
}

detect_roots
if [[ "${HAS_CLAUDE}" -eq 1 ]]; then
  echo "Validating adapter command packs (Cursor + Copilot + Claude)..."
else
  echo "Validating adapter command packs (Cursor + Copilot)..."
fi
echo "Mode: ${MODE}"
echo "Cursor root: ${CURSOR_ROOT}"
echo "Copilot root: ${COPILOT_ROOT}"
if [[ "${HAS_CLAUDE}" -eq 1 ]]; then
  echo "Claude root: ${CLAUDE_ROOT}"
fi

check_pack() {
  # Verify required sections and the per-command guardrail in one pack file.
  local cmd="$1"
  local path="$2"

  require_contains "${path}" "## Required Behavior" "Required Behavior section"
  require_contains "${path}" "## Output" "Output section"

  if [[ "${cmd}" == "init" || "${cmd}" == "prompt-update" ]]; then
    require_contains "${path}" "Do not modify application source code." "source-code guardrail"
  elif [[ "${cmd}" == "code" ]]; then
    require_contains "${path}" "Implement only that task." "single-operation scope guardrail"
  elif [[ "${cmd}" == "review" ]]; then
    require_contains "${path}" "Do not make code changes unless explicitly asked." "review guardrail"
  elif [[ "${cmd}" == "sync" ]]; then
    require_contains "${path}" "Do not implement code unless explicitly asked." "sync guardrail"
  else
    require_contains "${path}" "Do not implement code" "no-code guardrail"
  fi
}

for cmd in "${commands[@]}"; do
  cursor="$(cursor_path_for "${cmd}")"
  copilot="$(copilot_path_for "${cmd}")"
  claude="$(claude_path_for "${cmd}")"

  require_file "${cursor}" || true
  require_file "${copilot}" || true
  if [[ "${HAS_CLAUDE}" -eq 1 ]]; then
    require_file "${claude}" || true
  fi

  [[ -f "${cursor}" ]] || continue
  [[ -f "${copilot}" ]] || continue

  check_pack "${cmd}" "${cursor}"
  check_pack "${cmd}" "${copilot}"

  c_steps="$(count_required_steps "${cursor}")"
  p_steps="$(count_required_steps "${copilot}")"
  diff=$(( c_steps > p_steps ? c_steps - p_steps : p_steps - c_steps ))
  if (( diff > 1 )); then
    echo "Required Behavior step count diverges for '${cmd}': cursor=${c_steps}, copilot=${p_steps}" >&2
    failures=$((failures + 1))
  fi

  if [[ "${HAS_CLAUDE}" -eq 1 && -f "${claude}" ]]; then
    check_pack "${cmd}" "${claude}"
    cl_steps="$(count_required_steps "${claude}")"
    diff_cl=$(( c_steps > cl_steps ? c_steps - cl_steps : cl_steps - c_steps ))
    if (( diff_cl > 1 )); then
      echo "Required Behavior step count diverges for '${cmd}': cursor=${c_steps}, claude=${cl_steps}" >&2
      failures=$((failures + 1))
    fi
  fi
done

if [[ "${failures}" -gt 0 ]]; then
  echo
  echo "Adapter validation failed with ${failures} issue(s)." >&2
  exit 1
fi

echo "Adapter validation passed."
