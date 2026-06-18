#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: init-project.sh --target <path> [--cursor] [--copilot] [--claude] [--force] [--dry-run]

Initialize a target project with SDLC-SPDD scaffold files.

Options:
  --target <path>   Target project path (required)
  --cursor          Install Cursor command templates
  --copilot         Install GitHub Copilot instructions and prompt files
  --claude          Install Claude Code commands and CLAUDE.md
  --force           Overwrite existing generated files
  --dry-run         Show actions without writing files
  --help            Print this help message
EOF
}

TARGET=""
INSTALL_CURSOR=0
INSTALL_COPILOT=0
INSTALL_CLAUDE=0
FORCE=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --cursor)
      INSTALL_CURSOR=1
      shift
      ;;
    --copilot)
      INSTALL_COPILOT=1
      shift
      ;;
    --claude)
      INSTALL_CLAUDE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
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

if [[ -z "${TARGET}" ]]; then
  echo "Error: --target is required" >&2
  usage >&2
  exit 1
fi

TARGET="$(cd "${TARGET}" && pwd)"

created=()
skipped=()

copy_if_missing() {
  local src="$1"
  local dest="$2"
  if [[ -f "${dest}" && "${FORCE}" -eq 0 ]]; then
    skipped+=("${dest}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would copy ${src} -> ${dest}"
    created+=("${dest}")
    return
  fi
  mkdir -p "$(dirname "${dest}")"
  cp "${src}" "${dest}"
  created+=("${dest}")
}

ensure_dir() {
  local dir="$1"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would mkdir -p ${dir}"
    return
  fi
  mkdir -p "${dir}"
}

ensure_gitkeep() {
  local dir="$1"
  local file="${dir}/.gitkeep"
  if [[ -f "${file}" && "${FORCE}" -eq 0 ]]; then
    skipped+=("${file}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create ${file}"
    created+=("${file}")
    return
  fi
  mkdir -p "${dir}"
  : > "${file}"
  created+=("${file}")
}

# Create folder structure
for dir in \
  requirements \
  requirements/milestones \
  spdd/canvas \
  spdd/tasks \
  spdd/reviews \
  spdd/sync \
  session-notes \
  agent-context/memory \
  agent-context/playbooks \
  agent-context/features \
  agent-context/sessions \
  agent-context/harness \
  docs/sdlc-spdd \
  scripts/sdlc-spdd; do
  ensure_dir "${TARGET}/${dir}"
  ensure_gitkeep "${TARGET}/${dir}"
done

# Create optional project planning artifacts without overwriting existing plans.
copy_if_missing \
  "${REPO_ROOT}/templates/project-docs/ROADMAP.md" \
  "${TARGET}/ROADMAP.md"

shopt -s nullglob
milestone_files=("${TARGET}"/milestone-*.md)
shopt -u nullglob
if ((${#milestone_files[@]} == 0)); then
  copy_if_missing \
    "${REPO_ROOT}/templates/project-docs/milestone-1.md" \
    "${TARGET}/milestone-1.md"
else
  skipped+=("${TARGET}/milestone-*.md")
fi

copy_if_missing \
  "${REPO_ROOT}/templates/requirements/milestones/README.md" \
  "${TARGET}/requirements/milestones/README.md"

# Copy memory and harness templates
for file in \
  project-memory.md \
  architecture-decisions.md \
  known-pitfalls.md \
  reusable-patterns.md \
  session-history.md \
  phase-index.md; do
  copy_if_missing \
    "${REPO_ROOT}/agent-context/memory/${file}" \
    "${TARGET}/agent-context/memory/${file}"
done

# Copy playbooks for SDLC Agents-style handoffs and repeatable workflows
for file in "${REPO_ROOT}"/agent-context/playbooks/*.md; do
  copy_if_missing \
    "${file}" \
    "${TARGET}/agent-context/playbooks/$(basename "${file}")"
done

copy_if_missing \
  "${REPO_ROOT}/agent-context/harness/quality-gates.md" \
  "${TARGET}/agent-context/harness/quality-gates.md"

copy_if_missing \
  "${REPO_ROOT}/agent-context/harness/validation-rules.md" \
  "${TARGET}/agent-context/harness/validation-rules.md"

# Copy user-facing SDLC-SPDD docs into the target project.
# Skip docs/README.md — orchestrator hub only; targets get a lean README template.
for file in "${REPO_ROOT}"/docs/*.md; do
  [[ "$(basename "${file}")" == "README.md" ]] && continue
  copy_if_missing \
    "${file}" \
    "${TARGET}/docs/sdlc-spdd/$(basename "${file}")"
done

copy_if_missing \
  "${REPO_ROOT}/templates/project-docs/docs-sdlc-spdd-README.md" \
  "${TARGET}/docs/sdlc-spdd/README.md"

if [[ "${INSTALL_CURSOR}" -eq 1 && "${INSTALL_COPILOT}" -eq 1 ]]; then
  copy_if_missing \
    "${REPO_ROOT}/templates/project-github-workflows/validate-sdlc-spdd-adapters.yml" \
    "${TARGET}/.github/workflows/validate-sdlc-spdd-adapters.yml"
fi

# Copy runtime session scripts into the target project for cross-session handoffs
for file in \
  start-agent-session.sh \
  resync-agent-session.sh \
  capture-session-memory.sh \
  create-work-from-milestone.sh \
  sync-roadmap-from-spdd.sh \
  summarize-session-notes.sh \
  sync-agent-context.sh \
  validate-command-adapters.sh \
  verify-agent-command-effects.sh \
  validate-reasons-canvas.sh \
  verify-project-install.sh; do
  copy_if_missing \
    "${REPO_ROOT}/scripts/${file}" \
    "${TARGET}/scripts/sdlc-spdd/${file}"
  if [[ "${DRY_RUN}" -eq 0 && -f "${TARGET}/scripts/sdlc-spdd/${file}" ]]; then
    chmod +x "${TARGET}/scripts/sdlc-spdd/${file}"
  fi
done

if [[ "${INSTALL_CURSOR}" -eq 1 ]]; then
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would install Cursor commands via install-cursor-commands.sh"
  else
    "${SCRIPT_DIR}/install-cursor-commands.sh" --target "${TARGET}" $([[ "${FORCE}" -eq 1 ]] && echo --force)
  fi
fi

if [[ "${INSTALL_COPILOT}" -eq 1 ]]; then
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would install Copilot prompts via install-copilot-prompts.sh"
  else
    "${SCRIPT_DIR}/install-copilot-prompts.sh" --target "${TARGET}" $([[ "${FORCE}" -eq 1 ]] && echo --force)
  fi
fi

if [[ "${INSTALL_CLAUDE}" -eq 1 ]]; then
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would install Claude Code commands via install-claude-commands.sh"
  else
    "${SCRIPT_DIR}/install-claude-commands.sh" --target "${TARGET}" $([[ "${FORCE}" -eq 1 ]] && echo --force)
  fi
fi

if [[ "${DRY_RUN}" -eq 0 ]]; then
  "${SCRIPT_DIR}/detect-stack.sh" --target "${TARGET}" || true
fi

echo "SDLC-SPDD initialization complete for: ${TARGET}"
echo "Created or updated (${#created[@]}):"
printf '  %s\n' "${created[@]:-none}"
echo "Skipped existing (${#skipped[@]}):"
printf '  %s\n' "${skipped[@]:-none}"
echo "Recommended next step: run /sdlc-spdd-init in Cursor, Copilot Chat, or Claude Code, then /sdlc-spdd-plan"
echo "Local SDLC-SPDD docs installed under: ${TARGET}/docs/sdlc-spdd (start at README.md)"
echo "Session scripts installed under: ${TARGET}/scripts/sdlc-spdd"

verify_args=(--target "${TARGET}")
if [[ "${INSTALL_CURSOR}" -eq 1 ]]; then
  verify_args+=(--require-cursor)
fi
if [[ "${INSTALL_COPILOT}" -eq 1 ]]; then
  verify_args+=(--require-copilot)
fi
if [[ "${INSTALL_CLAUDE}" -eq 1 ]]; then
  verify_args+=(--require-claude)
fi
if [[ "${DRY_RUN}" -eq 0 ]]; then
  echo "Running install verification..."
  "${SCRIPT_DIR}/verify-project-install.sh" "${verify_args[@]}"
fi
