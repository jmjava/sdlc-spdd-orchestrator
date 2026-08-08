#!/usr/bin/env bash
# FEAT-002 — generate Cursor/Copilot/Claude adapters from spec/commands/*.spec.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Overrides for tests / alternate trees (also via env):
#   SDLC_SPEC_DIR, SDLC_TEMPLATE_ROOT
SPEC_DIR="${SDLC_SPEC_DIR:-${REPO_ROOT}/spec/commands}"
TEMPLATE_ROOT="${SDLC_TEMPLATE_ROOT:-${REPO_ROOT}/templates}"

usage() {
  cat <<'EOF'
Usage: generate-command-adapters.sh [--check] [--spec-dir DIR] [--template-root DIR]

Generate templates/cursor, templates/copilot/prompts, and templates/claude/commands
from canonical specs under spec/commands/.

  --check            Exit 1 if generated output would differ from checked-in templates.
  --spec-dir DIR     Spec directory (default: <repo>/spec/commands; env SDLC_SPEC_DIR).
  --template-root DIR
                     Template root containing cursor/, copilot/prompts/, claude/commands/
                     (default: <repo>/templates; env SDLC_TEMPLATE_ROOT).
EOF
}

CHECK_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK_ONLY=1; shift ;;
    --spec-dir)
      SPEC_DIR="${2:-}"
      shift 2
      ;;
    --template-root)
      TEMPLATE_ROOT="${2:-}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "${SPEC_DIR}" || ! -d "${SPEC_DIR}" ]]; then
  echo "generate-command-adapters: spec dir missing or not a directory: ${SPEC_DIR}" >&2
  exit 1
fi
if [[ -z "${TEMPLATE_ROOT}" ]]; then
  echo "generate-command-adapters: template root is empty" >&2
  exit 1
fi
SPEC_DIR="$(cd "${SPEC_DIR}" && pwd)"
mkdir -p "${TEMPLATE_ROOT}"
TEMPLATE_ROOT="$(cd "${TEMPLATE_ROOT}" && pwd)"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

failures=0

spec_meta() {
  local spec="$1"
  local key="$2"
  awk -v key="${key}" '
    BEGIN { in_fm=0 }
    /^---$/ { in_fm = !in_fm; next }
    in_fm && $0 ~ "^" key ":" {
      sub("^" key ":[[:space:]]*", "")
      print
      exit
    }
  ' "${spec}"
}

read_block() {
  local spec="$1"
  local block_id="$2"
  awk -v id="${block_id}" '
    $0 == "---BLOCK:" id "---" { capture=1; next }
    capture && $0 == "---END---" { exit }
    capture { print }
  ' "${spec}" | sed -e :a -e '/^\s*$/N; s/\n$//' -e ta
}

block_or_shared() {
  local spec="$1"
  local adapter="$2"
  local section="$3"
  local body
  body="$(read_block "${spec}" "${adapter}:${section}")"
  if [[ -n "${body}" ]]; then
    printf '%s' "${body}"
    return 0
  fi
  read_block "${spec}" "shared:${section}"
}

adapter_paths() {
  local family="$1"
  local slug="$2"
  case "${family}" in
    lifecycle)
      CURSOR_OUT="${TEMPLATE_ROOT}/cursor/sdlc-spdd-${slug}.md"
      COPILOT_OUT="${TEMPLATE_ROOT}/copilot/prompts/sdlc-spdd-${slug}.prompt.md"
      CLAUDE_OUT="${TEMPLATE_ROOT}/claude/commands/sdlc-spdd-${slug}.md"
      ;;
    workflow)
      CURSOR_OUT="${TEMPLATE_ROOT}/cursor/sdlc-${slug}.md"
      COPILOT_OUT="${TEMPLATE_ROOT}/copilot/prompts/sdlc-${slug}.prompt.md"
      CLAUDE_OUT="${TEMPLATE_ROOT}/claude/commands/sdlc-${slug}.md"
      ;;
    *)
      echo "Unknown family: ${family}" >&2
      return 1
      ;;
  esac
}

write_optional_context_backend() {
  local spec="$1"
  local adapter="$2"
  local cb
  cb="$(block_or_shared "${spec}" "${adapter}" "Context Backend (runtime-resolved)")"
  if [[ -n "${cb}" ]]; then
    printf '## Context Backend (runtime-resolved)\n\n%s\n\n' "${cb}"
  fi
}

write_cursor() {
  local spec="$1"
  local out="$2"
  local title preamble rb out_body
  title="$(read_block "${spec}" "cursor:title")"
  preamble="$(read_block "${spec}" "cursor:preamble")"
  rb="$(block_or_shared "${spec}" cursor "Required Behavior")"
  out_body="$(block_or_shared "${spec}" cursor "Output")"
  {
    printf '# %s\n\n' "${title}"
    [[ -n "${preamble}" ]] && printf '%s\n\n' "${preamble}"
    printf '## Required Behavior\n\n%s\n\n' "${rb}"
    write_optional_context_backend "${spec}" cursor
    printf '## Output\n\n%s\n' "${out_body}"
  } > "${out}"
}

write_copilot() {
  local spec="$1"
  local out="$2"
  local desc mode title preamble rb out_body
  desc="$(spec_meta "${spec}" copilot_description)"
  mode="$(spec_meta "${spec}" copilot_mode)"
  title="$(read_block "${spec}" "copilot:title")"
  preamble="$(read_block "${spec}" "copilot:preamble")"
  rb="$(block_or_shared "${spec}" copilot "Required Behavior")"
  out_body="$(block_or_shared "${spec}" copilot "Output")"
  {
    echo "---"
    echo "description: ${desc}"
    [[ -n "${mode}" ]] && echo "mode: ${mode}"
    echo "---"
    echo
    printf '# %s\n\n' "${title}"
    [[ -n "${preamble}" ]] && printf '%s\n\n' "${preamble}"
    printf '## Required Behavior\n\n%s\n\n' "${rb}"
    write_optional_context_backend "${spec}" copilot
    printf '## Output\n\n%s\n' "${out_body}"
  } > "${out}"
}

write_claude() {
  local spec="$1"
  local out="$2"
  local desc hint title preamble rb out_body
  desc="$(spec_meta "${spec}" claude_description)"
  hint="$(spec_meta "${spec}" claude_argument_hint)"
  title="$(read_block "${spec}" "claude:title")"
  preamble="$(read_block "${spec}" "claude:preamble")"
  rb="$(block_or_shared "${spec}" claude "Required Behavior")"
  out_body="$(block_or_shared "${spec}" claude "Output")"
  {
    # Frontmatter only when the spec provides metadata; committed claude
    # adapters without descriptions have none.
    if [[ -n "${desc}" || -n "${hint}" ]]; then
      echo "---"
      [[ -n "${desc}" ]] && echo "description: ${desc}"
      [[ -n "${hint}" ]] && echo "argument-hint: ${hint}"
      echo "---"
      echo
    fi
    printf '# %s\n\n' "${title}"
    [[ -n "${preamble}" ]] && printf '%s\n\n' "${preamble}"
    printf '## Required Behavior\n\n%s\n\n' "${rb}"
    write_optional_context_backend "${spec}" claude
    printf '## Output\n\n%s\n' "${out_body}"
  } > "${out}"
}

compare_or_install() {
  local generated="$1"
  local target="$2"
  if [[ ! -f "${target}" ]]; then
    if (( CHECK_ONLY )); then
      echo "Missing target template: ${target}" >&2
      failures=$((failures + 1))
      return 0
    fi
    mkdir -p "$(dirname "${target}")"
    cp "${generated}" "${target}"
    echo "Created ${target#${TEMPLATE_ROOT}/}"
    return 0
  fi
  if ! diff -q "${generated}" "${target}" >/dev/null 2>&1; then
    if (( CHECK_ONLY )); then
      echo "Stale adapter: ${target#${TEMPLATE_ROOT}/}" >&2
      diff -u "${target}" "${generated}" | head -40 >&2 || true
      failures=$((failures + 1))
    else
      cp "${generated}" "${target}"
      echo "Updated ${target#${TEMPLATE_ROOT}/}"
    fi
  fi
}

# Fail early on incomplete specs so adapters never ship empty sections.
validate_spec() {
  local spec="$1"
  local family="$2"
  local slug="$3"
  local adapter rb out_body title ok=0

  if [[ -z "${family}" || -z "${slug}" ]]; then
    echo "Error: $(basename "${spec}") missing family and/or slug in front matter" >&2
    return 1
  fi
  if ! adapter_paths "${family}" "${slug}"; then
    return 1
  fi
  for adapter in cursor copilot claude; do
    title="$(read_block "${spec}" "${adapter}:title")"
    if [[ -z "${title}" ]]; then
      echo "Error: $(basename "${spec}") missing ---BLOCK:${adapter}:title---" >&2
      ok=1
    fi
  done
  rb="$(block_or_shared "${spec}" cursor "Required Behavior")"
  if [[ -z "${rb}" ]]; then
    echo "Error: $(basename "${spec}") missing Required Behavior block" >&2
    ok=1
  fi
  out_body="$(block_or_shared "${spec}" cursor "Output")"
  if [[ -z "${out_body}" ]]; then
    echo "Error: $(basename "${spec}") missing Output block" >&2
    ok=1
  fi
  return "${ok}"
}

shopt -s nullglob
specs=( "${SPEC_DIR}"/*.spec.md )
if ((${#specs[@]} == 0)); then
  echo "No specs found in ${SPEC_DIR}. Run ./scripts/extract-command-specs.sh first." >&2
  exit 1
fi

for spec in "${specs[@]}"; do
  family="$(spec_meta "${spec}" family)"
  slug="$(spec_meta "${spec}" slug)"
  if ! validate_spec "${spec}" "${family}" "${slug}"; then
    failures=$((failures + 1))
    continue
  fi
  adapter_paths "${family}" "${slug}"

  write_cursor "${spec}" "${WORK}/cursor.md"
  write_copilot "${spec}" "${WORK}/copilot.md"
  write_claude "${spec}" "${WORK}/claude.md"

  compare_or_install "${WORK}/cursor.md" "${CURSOR_OUT}"
  compare_or_install "${WORK}/copilot.md" "${COPILOT_OUT}"
  compare_or_install "${WORK}/claude.md" "${CLAUDE_OUT}"
done

if (( failures > 0 )); then
  echo "generate-command-adapters: ${failures} issue(s)." >&2
  exit 1
fi

if (( CHECK_ONLY )); then
  echo "generate-command-adapters --check: all adapters match specs."
else
  echo "generate-command-adapters: generation complete."
fi
