#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/framework-install.sh"

usage() {
  cat <<'EOF'
Usage: init-project.sh --target <path> [--cursor] [--copilot] [--claude] [--with-guide] [--force] [--dry-run]

Initialize a target project with the SDLC-SPDD scaffold (storage v3).

Everything the framework owns is installed under a single folder — the home:

  <target>/sdlc-spdd/
    requirements/      milestones + requirements
    spdd/              canvas/ analysis/ tasks/ reviews/ sync/ memory/
    spdd/memory/       lessons.jsonl (committed ledger) + registry.jsonl
    harness/ playbooks/ extensions/
    scripts/           installed workflow CLI (sdlc.sh + runtime scripts)
    docs/              target-local SDLC-SPDD docs
    .sdlc/             gitignored runtime (sessions, staged lessons, sqlite)

IDE adapter stubs (.cursor/, .github/, .claude/, CLAUDE.md) stay at the target
repo root because the IDEs require that, but reference paths under sdlc-spdd/.

Options:
  --target <path>   Target project path (required)
  --cursor          Install Cursor command templates
  --copilot         Install GitHub Copilot instructions and prompt files
  --claude          Install Claude Code commands and CLAUDE.md
  --with-guide      Opt this install into the optional Guide DICE context
                    backend (writes sdlc-spdd/harness/guide-dice.md;
                    backend availability is still resolved at runtime)
  --force           Overwrite existing generated files
  --dry-run         Show actions without writing files
  --help            Print this help message
EOF
}

TARGET=""
INSTALL_CURSOR=0
INSTALL_COPILOT=0
INSTALL_CLAUDE=0
WITH_GUIDE=0
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
    --with-guide)
      WITH_GUIDE=1
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
HOME_DIR="${TARGET}/sdlc-spdd"

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
  framework_ensure_dir "$1" "${DRY_RUN}"
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

# Seed an empty file (memory ledgers) when missing; never truncate existing data.
ensure_empty_file() {
  local file="$1"
  if [[ -f "${file}" ]]; then
    skipped+=("${file}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create empty ${file}"
    created+=("${file}")
    return
  fi
  mkdir -p "$(dirname "${file}")"
  : > "${file}"
  created+=("${file}")
}

# Single-folder home structure.
for dir in \
  requirements \
  requirements/milestones \
  spdd/canvas \
  spdd/analysis \
  spdd/tasks \
  spdd/reviews \
  spdd/sync \
  session-notes \
  playbooks \
  extensions \
  extensions/_all-agents \
  extensions/initializer-agent \
  extensions/planning-agent \
  extensions/architect-agent \
  extensions/coding-agent \
  extensions/codereview-agent \
  extensions/retro-agent \
  extensions/curator-agent \
  extensions/skills \
  harness \
  docs \
  scripts \
  scripts/lib; do
  ensure_dir "${HOME_DIR}/${dir}"
  ensure_gitkeep "${HOME_DIR}/${dir}"
done
ensure_dir "${HOME_DIR}/spdd/memory"

# Storage v3 memory model: one committed lessons ledger + append-only registry.
# Captures stage to the gitignored <home>/.sdlc/staged/lessons.jsonl and are
# promoted by `sdlc.sh accept`. No script ever git-commits or pushes.
ensure_empty_file "${HOME_DIR}/spdd/memory/lessons.jsonl"
ensure_empty_file "${HOME_DIR}/spdd/memory/registry.jsonl"

# Gitignore the runtime folder.
if [[ "${DRY_RUN}" -eq 1 ]]; then
  framework_ensure_gitignore_runtime "${TARGET}" 1
else
  framework_ensure_gitignore_runtime "${TARGET}" 0
fi

# Create optional project planning artifacts without overwriting existing plans.
copy_if_missing \
  "${REPO_ROOT}/templates/project-docs/ROADMAP.md" \
  "${HOME_DIR}/ROADMAP.md"

# Prefer subdirectory milestone layout for new projects; keep existing
# milestone definitions (home or legacy root) if already present.
shopt -s nullglob
root_milestones=("${TARGET}"/milestone-*.md "${HOME_DIR}"/milestone-*.md)
subdir_milestones=("${HOME_DIR}"/requirements/milestones/milestone-*/MILESTONE-*.md)
shopt -u nullglob
if ((${#root_milestones[@]} == 0 && ${#subdir_milestones[@]} == 0)); then
  ensure_dir "${HOME_DIR}/requirements/milestones/milestone-1"
  copy_if_missing \
    "${REPO_ROOT}/templates/requirements/milestones/milestone-definition.md" \
    "${HOME_DIR}/requirements/milestones/milestone-1/MILESTONE-1.md"
  copy_if_missing \
    "${REPO_ROOT}/templates/requirements/milestones/milestone-template.yml" \
    "${HOME_DIR}/requirements/milestones/milestone-1/_milestone.yml"
else
  skipped+=("existing milestone definitions")
fi

copy_if_missing \
  "${REPO_ROOT}/templates/requirements/milestones/README.md" \
  "${HOME_DIR}/requirements/milestones/README.md"

# Playbooks for SDLC Agents-style handoffs and repeatable workflows.
for file in "${REPO_ROOT}"/agent-context/playbooks/*.md; do
  copy_if_missing \
    "${file}" \
    "${HOME_DIR}/playbooks/$(basename "${file}")"
done

copy_if_missing \
  "${REPO_ROOT}/templates/agent-context/extensions/README.md" \
  "${HOME_DIR}/extensions/README.md"

copy_if_missing \
  "${REPO_ROOT}/templates/agent-context/extensions/manifest.md" \
  "${HOME_DIR}/extensions/manifest.md"

copy_if_missing \
  "${REPO_ROOT}/templates/agent-context/extensions/_all-agents/example-manifest-extension.md" \
  "${HOME_DIR}/extensions/_all-agents/example-manifest-extension.md"

for file in "${REPO_ROOT}"/templates/agent-context/extensions/skills/*.md; do
  [[ -f "${file}" ]] || continue
  copy_if_missing \
    "${file}" \
    "${HOME_DIR}/extensions/skills/$(basename "${file}")"
done

copy_if_missing \
  "${REPO_ROOT}/agent-context/harness/quality-gates.md" \
  "${HOME_DIR}/harness/quality-gates.md"

copy_if_missing \
  "${REPO_ROOT}/agent-context/harness/validation-rules.md" \
  "${HOME_DIR}/harness/validation-rules.md"

# Optional Guide DICE backend opt-in. The marker only enables runtime probing
# (resolve-context-backend.sh); commands still fall back to file-based context
# whenever Guide is unreachable.
if [[ "${WITH_GUIDE}" -eq 1 ]]; then
  copy_if_missing \
    "${REPO_ROOT}/templates/agent-context/harness/guide-dice.md" \
    "${HOME_DIR}/harness/guide-dice.md"
fi

# Copy user-facing SDLC-SPDD docs into the target project home.
# Skip orchestrator-internal docs (see scripts/lib/shipped-docs-boundary.sh).
# shellcheck source=lib/shipped-docs-boundary.sh
source "${SCRIPT_DIR}/lib/shipped-docs-boundary.sh"
for file in "${REPO_ROOT}"/docs/*.md; do
  is_orchestrator_only_doc "${file}" && continue
  copy_if_missing \
    "${file}" \
    "${HOME_DIR}/docs/$(basename "${file}")"
done

copy_if_missing \
  "${REPO_ROOT}/templates/project-docs/docs-sdlc-spdd-README.md" \
  "${HOME_DIR}/docs/README.md"

if [[ "${INSTALL_CURSOR}" -eq 1 && "${INSTALL_COPILOT}" -eq 1 ]]; then
  copy_if_missing \
    "${REPO_ROOT}/templates/project-github-workflows/validate-sdlc-spdd-adapters.yml" \
    "${TARGET}/.github/workflows/validate-sdlc-spdd-adapters.yml"
fi

# Workflow CLI: sdlc.sh + pointer/workflow/team-registry managers live together
# under <home>/scripts/.
for file in \
  sdlc-pointer.sh \
  sdlc-workflow.sh \
  sdlc-team-registry.sh; do
  copy_if_missing \
    "${REPO_ROOT}/agent-context/${file}" \
    "${HOME_DIR}/scripts/${file}"
  if [[ "${DRY_RUN}" -eq 0 && -f "${HOME_DIR}/scripts/${file}" ]]; then
    chmod +x "${HOME_DIR}/scripts/${file}"
  fi
done

copy_if_missing \
  "${REPO_ROOT}/templates/agent-context/hooks/notify-team-registry.example.sh" \
  "${HOME_DIR}/scripts/hooks/notify-team-registry.example.sh"

# Runtime session scripts for cross-session handoffs.
for file in \
  start-agent-session.sh \
  resync-agent-session.sh \
  capture-session-memory.sh \
  accept-lessons.sh \
  index-spdd-analysis.sh \
  resolve-agent-context.sh \
  resolve-context-backend.sh \
  create-work-from-milestone.sh \
  sync-roadmap-from-spdd.sh \
  summarize-session-notes.sh \
  sync-agent-context.sh \
  detect-stack.sh \
  validate-command-adapters.sh \
  verify-agent-command-effects.sh \
  validate-reasons-canvas.sh \
  validate-requirements-format.sh \
  verify-project-install.sh \
  sdlc.sh; do
  copy_if_missing \
    "${REPO_ROOT}/scripts/${file}" \
    "${HOME_DIR}/scripts/${file}"
  if [[ "${DRY_RUN}" -eq 0 && -f "${HOME_DIR}/scripts/${file}" ]]; then
    chmod +x "${HOME_DIR}/scripts/${file}"
  fi
done

# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/paths.sh"
for lib in "${SDLC_SHIPPED_LIB_FILES[@]}"; do
  copy_if_missing \
    "${REPO_ROOT}/scripts/lib/${lib}" \
    "${HOME_DIR}/scripts/lib/${lib}"
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
echo "Framework home: ${HOME_DIR} (docs at sdlc-spdd/docs/, start at README.md)"
echo "Workflow CLI installed under: ${HOME_DIR}/scripts (daily entry point: ./sdlc-spdd/scripts/sdlc.sh)"

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
