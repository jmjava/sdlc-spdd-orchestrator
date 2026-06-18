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
  analysis
  plan
  architect
  code
  api-test
  review
  prompt-update
  retro
  sync
)

failures=0

detect_roots() {
  if [[ -d "${TARGET}/templates/cursor" || -d "${TARGET}/templates/copilot/prompts" || -d "${TARGET}/templates/claude/commands" ]]; then
    CURSOR_ROOT="${TARGET}/templates/cursor"
    COPILOT_ROOT="${TARGET}/templates/copilot/prompts"
    CLAUDE_ROOT="${TARGET}/templates/claude/commands"
    MODE="orchestrator-templates"
  elif [[ -d "${TARGET}/.cursor/commands" || -d "${TARGET}/.github/prompts" || -d "${TARGET}/.claude/commands" ]]; then
    CURSOR_ROOT="${TARGET}/.cursor/commands"
    COPILOT_ROOT="${TARGET}/.github/prompts"
    CLAUDE_ROOT="${TARGET}/.claude/commands"
    MODE="installed-target"
  else
    echo "Could not find command packs in ${TARGET}." >&2
    echo "Need templates/ (orchestrator) or .cursor/.github/.claude command dirs (target)." >&2
    exit 1
  fi

  # Each adapter pack is validated only when present, so single-assistant
  # installs (e.g. Claude only) validate cleanly instead of erroring.
  HAS_CURSOR=0
  HAS_COPILOT=0
  HAS_CLAUDE=0
  if [[ -d "${CURSOR_ROOT}" ]]; then HAS_CURSOR=1; fi
  if [[ -d "${COPILOT_ROOT}" ]]; then HAS_COPILOT=1; fi
  if [[ -d "${CLAUDE_ROOT}" ]]; then HAS_CLAUDE=1; fi
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
present_packs=()
if [[ "${HAS_CURSOR}" -eq 1 ]]; then present_packs+=("Cursor"); fi
if [[ "${HAS_COPILOT}" -eq 1 ]]; then present_packs+=("Copilot"); fi
if [[ "${HAS_CLAUDE}" -eq 1 ]]; then present_packs+=("Claude"); fi
echo "Validating adapter command packs ($(IFS='+'; echo "${present_packs[*]}"))..."
echo "Mode: ${MODE}"
if [[ "${HAS_CURSOR}" -eq 1 ]]; then echo "Cursor root: ${CURSOR_ROOT}"; fi
if [[ "${HAS_COPILOT}" -eq 1 ]]; then echo "Copilot root: ${COPILOT_ROOT}"; fi
if [[ "${HAS_CLAUDE}" -eq 1 ]]; then echo "Claude root: ${CLAUDE_ROOT}"; fi

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

# Always-on grounding file for each assistant: the file an assistant loads on
# every interaction (not just when a command runs). This is what guarantees the
# whole-ecosystem norm — Planning + SPDD + SDLC — for all work, regardless of
# which command (if any) is invoked.
grounding_path_for() {
  local asst="$1"
  if [[ "${MODE}" == "orchestrator-templates" ]]; then
    case "${asst}" in
      cursor)  echo "${TARGET}/templates/cursor/rules/sdlc-spdd.mdc" ;;
      copilot) echo "${TARGET}/templates/copilot/copilot-instructions.md" ;;
      claude)  echo "${TARGET}/templates/claude/CLAUDE.md" ;;
    esac
  else
    case "${asst}" in
      cursor)  echo "${TARGET}/.cursor/rules/sdlc-spdd.mdc" ;;
      copilot) echo "${TARGET}/.github/copilot-instructions.md" ;;
      claude)  echo "${TARGET}/CLAUDE.md" ;;
    esac
  fi
}

# Shared anchors every grounding file must contain so all assistants understand
# the full ecosystem: the lifecycle, the operating model + work rules sections,
# and the Planning (roadmap/milestones/session-notes), SPDD (canvas), and SDLC
# (session briefs and memory) artifacts.
grounding_anchors=(
  "Initialize -> Analysis -> Plan -> Architect -> Code -> API Test -> Review -> Retro -> Sync"
  "## Operating Model"
  "## Work Rules"
  "ROADMAP.md"
  "milestone-*.md"
  "session-notes/"
  "spdd/analysis/"
  "spdd/canvas/"
  "agent-context/sessions/"
  "agent-context/memory/"
  "/sdlc-spdd-analysis"
)

check_grounding() {
  local asst="$1"
  local path="$2"
  require_file "${path}" || return 0
  local anchor
  for anchor in "${grounding_anchors[@]}"; do
    require_contains "${path}" "${anchor}" "${asst} grounding anchor '${anchor}'"
  done
}

for cmd in "${commands[@]}"; do
  # Build the list of present adapter packs for this command. Each pack is
  # required only when its root exists, and cross-pack parity is compared over
  # whichever packs are present (1, 2, or 3).
  pack_names=()
  pack_paths=()

  if [[ "${HAS_CURSOR}" -eq 1 ]]; then
    p="$(cursor_path_for "${cmd}")"
    require_file "${p}" || true
    if [[ -f "${p}" ]]; then pack_names+=("cursor"); pack_paths+=("${p}"); fi
  fi
  if [[ "${HAS_COPILOT}" -eq 1 ]]; then
    p="$(copilot_path_for "${cmd}")"
    require_file "${p}" || true
    if [[ -f "${p}" ]]; then pack_names+=("copilot"); pack_paths+=("${p}"); fi
  fi
  if [[ "${HAS_CLAUDE}" -eq 1 ]]; then
    p="$(claude_path_for "${cmd}")"
    require_file "${p}" || true
    if [[ -f "${p}" ]]; then pack_names+=("claude"); pack_paths+=("${p}"); fi
  fi

  (( ${#pack_paths[@]} > 0 )) || continue

  min_steps=-1
  max_steps=-1
  steps_summary=""
  for i in "${!pack_paths[@]}"; do
    path="${pack_paths[$i]}"
    name="${pack_names[$i]}"
    check_pack "${cmd}" "${path}"
    s="$(count_required_steps "${path}")"
    steps_summary+="${name}=${s} "
    if (( min_steps < 0 || s < min_steps )); then min_steps=${s}; fi
    if (( max_steps < 0 || s > max_steps )); then max_steps=${s}; fi
  done

  if (( max_steps - min_steps > 1 )); then
    echo "Required Behavior step count diverges for '${cmd}': ${steps_summary}" >&2
    failures=$((failures + 1))
  fi
done

echo "Validating always-on grounding files (whole-ecosystem norm)..."
if [[ "${HAS_CURSOR}" -eq 1 ]];  then check_grounding cursor  "$(grounding_path_for cursor)";  fi
if [[ "${HAS_COPILOT}" -eq 1 ]]; then check_grounding copilot "$(grounding_path_for copilot)"; fi
if [[ "${HAS_CLAUDE}" -eq 1 ]];  then check_grounding claude  "$(grounding_path_for claude)";  fi

if [[ "${failures}" -gt 0 ]]; then
  echo
  echo "Adapter validation failed with ${failures} issue(s)." >&2
  exit 1
fi

echo "Adapter validation passed."
