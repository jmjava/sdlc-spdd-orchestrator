#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: upgrade-project.sh --target <path> [--cursor] [--copilot] [--all] [--dry-run] [--no-backup]

Upgrade SDLC-SPDD framework files in a target project that was initialized by
an earlier version of this scaffold.

The upgrade is framework-only:
  - updates SDLC-SPDD assistant prompts
  - updates SDLC-SPDD playbooks and harness files
  - updates target-local SDLC-SPDD documentation under docs/sdlc-spdd/
  - updates target-local SDLC-SPDD runtime scripts
  - creates missing ROADMAP.md, milestone-1.md, and session-notes/
  - creates missing session and memory files
  - does not touch application source files
  - does not overwrite requirements, canvases, feature workspaces, reviews,
    sync logs, or accumulated project memory

Options:
  --target <path>   Target project path (required)
  --cursor          Upgrade Cursor command prompts
  --copilot         Upgrade GitHub Copilot instructions and prompt files
  --all             Upgrade all supported assistant prompt adapters
  --dry-run         Show actions without writing files
  --no-backup       Do not back up overwritten framework files
  --help            Print this help message

If no assistant flag is provided, --all is assumed.
EOF
}

TARGET=""
UPGRADE_CURSOR=0
UPGRADE_COPILOT=0
DRY_RUN=0
BACKUP=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --cursor)
      UPGRADE_CURSOR=1
      shift
      ;;
    --copilot)
      UPGRADE_COPILOT=1
      shift
      ;;
    --all)
      UPGRADE_CURSOR=1
      UPGRADE_COPILOT=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-backup)
      BACKUP=0
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

if [[ "${UPGRADE_CURSOR}" -eq 0 && "${UPGRADE_COPILOT}" -eq 0 ]]; then
  UPGRADE_CURSOR=1
  UPGRADE_COPILOT=1
fi

TARGET="$(cd "${TARGET}" && pwd)"
timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
backup_root="${TARGET}/.sdlc-spdd-upgrade-backups/${timestamp}"

created=()
updated=()
unchanged=()
backed_up=()
preserved=()

ensure_dir() {
  local dir="$1"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would mkdir -p ${dir}"
  else
    mkdir -p "${dir}"
  fi
}

ensure_gitkeep() {
  local dir="$1"
  local file="${dir}/.gitkeep"
  ensure_dir "${dir}"
  if [[ -f "${file}" ]]; then
    unchanged+=("${file}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create ${file}"
  else
    : > "${file}"
  fi
  created+=("${file}")
}

backup_existing() {
  local dest="$1"
  local rel="${dest#${TARGET}/}"
  local backup_path="${backup_root}/${rel}"
  if [[ "${BACKUP}" -eq 0 ]]; then
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would back up ${dest} -> ${backup_path}"
  else
    mkdir -p "$(dirname "${backup_path}")"
    cp "${dest}" "${backup_path}"
  fi
  backed_up+=("${backup_path}")
}

copy_framework_file() {
  local src="$1"
  local dest="$2"
  if [[ ! -f "${src}" ]]; then
    echo "Framework source missing: ${src}" >&2
    exit 1
  fi
  ensure_dir "$(dirname "${dest}")"
  if [[ -f "${dest}" ]]; then
    if cmp -s "${src}" "${dest}"; then
      unchanged+=("${dest}")
      return
    fi
    backup_existing "${dest}"
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      echo "[dry-run] would update ${dest}"
    else
      cp "${src}" "${dest}"
    fi
    updated+=("${dest}")
  else
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      echo "[dry-run] would create ${dest}"
    else
      cp "${src}" "${dest}"
    fi
    created+=("${dest}")
  fi
}

copy_executable_framework_file() {
  local src="$1"
  local dest="$2"
  copy_framework_file "${src}" "${dest}"
  if [[ "${DRY_RUN}" -eq 0 && -f "${dest}" ]]; then
    chmod +x "${dest}"
  fi
}

create_missing_memory_file() {
  local src="$1"
  local dest="$2"
  ensure_dir "$(dirname "${dest}")"
  if [[ -f "${dest}" ]]; then
    preserved+=("${dest}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create missing memory file ${dest}"
  else
    cp "${src}" "${dest}"
  fi
  created+=("${dest}")
}

# Directories required by the current framework. Existing application files are
# not touched; only missing directories and .gitkeep files are created.
for dir in \
  requirements \
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
  ensure_gitkeep "${TARGET}/${dir}"
done

# Preserve project planning artifacts; create only if missing.
create_missing_project_doc() {
  local src="$1"
  local dest="$2"
  ensure_dir "$(dirname "${dest}")"
  if [[ -f "${dest}" ]]; then
    preserved+=("${dest}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create missing project planning doc ${dest}"
  else
    cp "${src}" "${dest}"
  fi
  created+=("${dest}")
}

create_missing_project_doc \
  "${REPO_ROOT}/templates/project-docs/ROADMAP.md" \
  "${TARGET}/ROADMAP.md"

shopt -s nullglob
milestone_files=("${TARGET}"/milestone-*.md)
shopt -u nullglob
if ((${#milestone_files[@]} == 0)); then
  create_missing_project_doc \
    "${REPO_ROOT}/templates/project-docs/milestone-1.md" \
    "${TARGET}/milestone-1.md"
else
  preserved+=("${TARGET}/milestone-*.md")
fi

# Preserve accumulated memory; create only missing memory files.
for file in \
  project-memory.md \
  architecture-decisions.md \
  known-pitfalls.md \
  reusable-patterns.md \
  session-history.md; do
  create_missing_memory_file \
    "${REPO_ROOT}/agent-context/memory/${file}" \
    "${TARGET}/agent-context/memory/${file}"
done

# Framework-owned playbooks and harness files are upgraded, with backups.
for file in "${REPO_ROOT}"/agent-context/playbooks/*.md; do
  copy_framework_file \
    "${file}" \
    "${TARGET}/agent-context/playbooks/$(basename "${file}")"
done

copy_framework_file \
  "${REPO_ROOT}/agent-context/README.md" \
  "${TARGET}/agent-context/README.md"

for file in \
  quality-gates.md \
  validation-rules.md; do
  copy_framework_file \
    "${REPO_ROOT}/agent-context/harness/${file}" \
    "${TARGET}/agent-context/harness/${file}"
done

# User-facing docs are framework-owned when installed under docs/sdlc-spdd.
for file in "${REPO_ROOT}"/docs/*.md; do
  copy_framework_file \
    "${file}" \
    "${TARGET}/docs/sdlc-spdd/$(basename "${file}")"
done

# Target-local runtime scripts are framework-owned and safe to upgrade.
for file in \
  start-agent-session.sh \
  resync-agent-session.sh \
  capture-session-memory.sh \
  create-work-from-milestone.sh \
  sync-roadmap-from-spdd.sh \
  summarize-session-notes.sh \
  sync-agent-context.sh \
  validate-reasons-canvas.sh; do
  copy_executable_framework_file \
    "${REPO_ROOT}/scripts/${file}" \
    "${TARGET}/scripts/sdlc-spdd/${file}"
done

if [[ "${UPGRADE_CURSOR}" -eq 1 ]]; then
  for src in "${REPO_ROOT}"/templates/cursor/*.md; do
    copy_framework_file \
      "${src}" \
      "${TARGET}/.cursor/commands/$(basename "${src}")"
  done
fi

if [[ "${UPGRADE_COPILOT}" -eq 1 ]]; then
  copy_framework_file \
    "${REPO_ROOT}/templates/copilot/copilot-instructions.md" \
    "${TARGET}/.github/copilot-instructions.md"

  for src in "${REPO_ROOT}"/templates/copilot/prompts/*.prompt.md; do
    copy_framework_file \
      "${src}" \
      "${TARGET}/.github/prompts/$(basename "${src}")"
  done
fi

echo "SDLC-SPDD framework upgrade complete for: ${TARGET}"
echo "Created (${#created[@]}):"
printf '  %s\n' "${created[@]:-none}"
echo "Updated framework files (${#updated[@]}):"
printf '  %s\n' "${updated[@]:-none}"
echo "Unchanged framework files (${#unchanged[@]}):"
printf '  %s\n' "${unchanged[@]:-none}"
echo "Preserved existing memory files (${#preserved[@]}):"
printf '  %s\n' "${preserved[@]:-none}"
if [[ "${BACKUP}" -eq 1 ]]; then
  echo "Backups (${#backed_up[@]}):"
  printf '  %s\n' "${backed_up[@]:-none}"
fi
echo "Not touched: application source, requirements, canvases, feature workspaces, reviews, sync logs, existing roadmap/milestones, existing memory content, or application docs outside docs/sdlc-spdd."
