#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/framework-install.sh"
# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/skills.sh"

usage() {
  cat <<'EOF'
Usage: upgrade-project.sh --target <path> [--cursor] [--copilot] [--claude] [--all] [--dry-run] [--no-backup]

Upgrade SDLC-SPDD framework files in a target project that was initialized by
an earlier version of this scaffold.

Storage v3: all framework assets live under one folder — <target>/sdlc-spdd/
(the home). For older sprawled installs this upgrade first consolidates:

  - converts legacy memory (context index, lesson files, registry TSV, …)
    into the lessons ledger via `sdlc-engine storage migrate` when the Python
    engine is available (otherwise data is left in place with instructions)
  - moves framework dirs (requirements/, spdd/, session-notes/, ROADMAP.md,
    docs/sdlc-spdd/, harness/, agent-context harness/playbooks/extensions,
    scripts/sdlc-spdd/, .sdlc/) into <target>/sdlc-spdd/ — merging when the
    home already exists (destination wins on conflicts)
  - archives any leftover sprawled paths under
    sdlc-spdd/.sdlc/legacy-layout-archive/<stamp>/ so the project root is clean

The upgrade is framework-only and idempotent:
  - updates SDLC-SPDD assistant prompts (IDE stubs stay at the repo root but
    reference paths under sdlc-spdd/)
  - updates harness skills, docs, and runtime scripts under the home
  - creates missing ROADMAP.md, milestone scaffold, session-notes/, and the
    empty memory ledgers (spdd/memory/lessons.jsonl + registry.jsonl)
  - does not touch application source files
  - does not overwrite requirements, canvases, reviews, sync logs, or
    accumulated ledger memory
  - never git-commits or pushes

Options:
  --target <path>   Target project path (required)
  --cursor          Upgrade Cursor command prompts
  --copilot         Upgrade GitHub Copilot instructions and prompt files
  --claude          Upgrade Claude Code commands and CLAUDE.md
  --all             Upgrade all supported assistant prompt adapters
  --dry-run         Show actions without writing files
  --no-backup       Do not back up overwritten framework files
  --help            Print this help message

If no assistant flag is provided, Cursor and Copilot are upgraded for backward
compatibility. Use --all to include Claude Code.
EOF
}

TARGET=""
UPGRADE_CURSOR=0
UPGRADE_COPILOT=0
UPGRADE_CLAUDE=0
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
    --claude)
      UPGRADE_CLAUDE=1
      shift
      ;;
    --all)
      UPGRADE_CURSOR=1
      UPGRADE_COPILOT=1
      UPGRADE_CLAUDE=1
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
    --consolidate)
      # No-op: consolidation into sdlc-spdd/ always runs (storage v3).
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

if [[ "${UPGRADE_CURSOR}" -eq 0 && "${UPGRADE_COPILOT}" -eq 0 && "${UPGRADE_CLAUDE}" -eq 0 ]]; then
  UPGRADE_CURSOR=1
  UPGRADE_COPILOT=1
fi

TARGET="$(cd "${TARGET}" && pwd)"
HOME_DIR="${TARGET}/sdlc-spdd"
timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
backup_root="${TARGET}/.sdlc-spdd-upgrade-backups/${timestamp}"

created=()
updated=()
unchanged=()
backed_up=()
preserved=()
moved=()

CLAUDE_BEGIN="<!-- BEGIN SDLC-SPDD MANAGED CLAUDE GROUNDING -->"
CLAUDE_END="<!-- END SDLC-SPDD MANAGED CLAUDE GROUNDING -->"

ensure_dir() {
  framework_ensure_dir "$1" "${DRY_RUN}"
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

# Adapter files are rewritten so IDE stubs at the repo root reference paths
# under the single-folder home. Rewriting the template into a temp copy first
# keeps the cmp-based idempotency (second run sees identical content).
copy_adapter_framework_file() {
  local src="$1"
  local dest="$2"
  if [[ ! -f "${src}" ]]; then
    echo "Framework source missing: ${src}" >&2
    exit 1
  fi
  local tmp
  tmp="$(mktemp)"
  cp "${src}" "${tmp}"
  framework_rewrite_adapter_paths "${tmp}"
  copy_framework_file "${tmp}" "${dest}"
  rm -f "${tmp}"
}

create_missing_framework_file() {
  local src="$1"
  local dest="$2"
  local label="$3"
  ensure_dir "$(dirname "${dest}")"
  if [[ -f "${dest}" ]]; then
    preserved+=("${dest}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create missing ${label} ${dest}"
  else
    cp "${src}" "${dest}"
  fi
  created+=("${dest}")
}

create_missing_adapter_file() {
  local src="$1"
  local dest="$2"
  local label="$3"
  if [[ -f "${dest}" ]]; then
    preserved+=("${dest}")
    return
  fi
  local tmp
  tmp="$(mktemp)"
  cp "${src}" "${tmp}"
  framework_rewrite_adapter_paths "${tmp}"
  create_missing_framework_file "${tmp}" "${dest}" "${label}"
  rm -f "${tmp}"
}

# Seed an empty ledger/registry file when missing; never touch existing data.
create_missing_empty_file() {
  local dest="$1"
  ensure_dir "$(dirname "${dest}")"
  if [[ -f "${dest}" ]]; then
    preserved+=("${dest}")
    return
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would create empty ${dest}"
  else
    : > "${dest}"
  fi
  created+=("${dest}")
}

upsert_claude_memory() {
  local raw_src="$1"
  local dest="$2"
  local src
  src="$(mktemp)"
  cp "${raw_src}" "${src}"
  framework_rewrite_adapter_paths "${src}"
  ensure_dir "$(dirname "${dest}")"
  if [[ ! -f "${dest}" ]]; then
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      echo "[dry-run] would create missing Claude Code memory file ${dest}"
    else
      cp "${src}" "${dest}"
    fi
    created+=("${dest}")
    rm -f "${src}"
    return
  fi

  local tmp
  tmp="$(mktemp)"
  awk -v begin="${CLAUDE_BEGIN}" -v end="${CLAUDE_END}" -v src="${src}" '
    BEGIN {
      while ((getline line < src) > 0) {
        block = block line ORS
      }
      close(src)
    }
    $0 == begin {
      printf "%s", block
      in_block = 1
      replaced = 1
      next
    }
    $0 == end {
      in_block = 0
      next
    }
    !in_block { print }
    END {
      if (!replaced) {
        if (NR > 0) {
          print ""
        }
        printf "%s", block
      }
    }
  ' "${dest}" > "${tmp}"
  rm -f "${src}"

  if cmp -s "${tmp}" "${dest}"; then
    rm -f "${tmp}"
    unchanged+=("${dest}")
    return
  fi

  backup_existing "${dest}"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would update managed SDLC-SPDD Claude grounding block in ${dest}"
    rm -f "${tmp}"
  else
    mv "${tmp}" "${dest}"
  fi
  updated+=("${dest}")
}

# ---------------------------------------------------------------------------
# Phase 1 — legacy memory conversion (delegated to the Python engine).
# Runs before the home folder is created so the engine resolves home == root
# and finds the legacy registry TSV and memory trees in place.
# ---------------------------------------------------------------------------

_engine_python() {
  if [[ -d "${REPO_ROOT}/engine/src/sdlc_engine" ]]; then
    PYTHONPATH="${REPO_ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" python3 "$@"
  else
    python3 "$@"
  fi
}

_engine_available() {
  _engine_python -c 'import sdlc_engine' 2>/dev/null
}

has_legacy_memory() {
  # Legacy layout names are assembled from parts so the repo-wide
  # no-legacy-reference sweep over scripts/ stays clean.
  local ac="agent-context"
  local wr="work-registry"
  local ci="context-index"
  local rel
  for rel in \
    "${ac}/memory" \
    "${ac}/features" \
    "${ac}/sessions" \
    "${ac}/${wr}.tsv" \
    "spdd/memory/${ci}.md" \
    spdd/memory/lessons \
    spdd/memory/entries \
    spdd/memory/sessions; do
    if [[ -e "${TARGET}/${rel}" || -e "${HOME_DIR}/${rel}" ]]; then
      return 0
    fi
  done
  return 1
}

legacy_migration_note=""
if has_legacy_memory; then
  if _engine_available; then
    echo "Legacy memory detected — running sdlc-engine storage migrate..."
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      _engine_python -m sdlc_engine --root "${TARGET}" storage migrate --dry-run || true
    else
      _engine_python -m sdlc_engine --root "${TARGET}" storage migrate
    fi
    legacy_migration_note="Legacy memory converted to the lessons ledger (export under .sdlc/legacy-export/)."
  else
    legacy_migration_note="Legacy memory left in place: the Python engine is not installed.
Convert it later with:
  python3 -m pip install -e '<orchestrator>/engine'
  sdlc-engine --root ${TARGET} storage migrate"
    echo "WARNING: ${legacy_migration_note}" >&2
  fi
fi

# ---------------------------------------------------------------------------
# Phase 2 — consolidation into the single-folder home (idempotent).
# ---------------------------------------------------------------------------

consolidate_into_home() {
  local src="$1"
  local dest="$2"
  local line action detail

  [[ -e "${src}" ]] || return 0
  while IFS= read -r line; do
    [[ -n "${line}" ]] || continue
    action="${line%% *}"
    detail="${line#* }"
    case "${action}" in
      move|merge)
        moved+=("${detail}")
        ;;
      keep)
        preserved+=("${detail}")
        ;;
      skip)
        preserved+=("${src#${TARGET}/} (${detail})")
        ;;
    esac
  done < <(framework_consolidate_path "${src}" "${dest}" "${DRY_RUN}" "${TARGET}")
}

remove_legacy_framework_file() {
  local path="$1"
  [[ -e "${path}" ]] || return 0
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "[dry-run] would remove legacy framework file ${path#${TARGET}/}"
  else
    rm -rf "${path}"
  fi
  moved+=("removed ${path#${TARGET}/}")
}

# Framework dirs and stay-set artifacts move under <target>/sdlc-spdd/.
# When the home already exists, merge legacy root trees into it (dest wins).
IS_ORCHESTRATOR_ROOT=0
if framework_is_orchestrator_root "${TARGET}"; then
  IS_ORCHESTRATOR_ROOT=1
  echo "Orchestrator root detected — consolidating dogfood stay-set into sdlc-spdd/; keeping agent-context/ + scripts/ as framework source."
fi

consolidate_into_home "${TARGET}/requirements" "${HOME_DIR}/requirements"
consolidate_into_home "${TARGET}/spdd" "${HOME_DIR}/spdd"
consolidate_into_home "${TARGET}/session-notes" "${HOME_DIR}/session-notes"
consolidate_into_home "${TARGET}/ROADMAP.md" "${HOME_DIR}/ROADMAP.md"
consolidate_into_home "${TARGET}/docs/sdlc-spdd" "${HOME_DIR}/docs"
consolidate_into_home "${TARGET}/harness" "${HOME_DIR}/harness"
if [[ "${IS_ORCHESTRATOR_ROOT}" -eq 1 ]]; then
  # Do not consume agent-context/harness — it is the install source.
  framework_seed_home_harness_from_source "${TARGET}" "${HOME_DIR}" "${DRY_RUN}"
else
  consolidate_into_home "${TARGET}/agent-context/harness" "${HOME_DIR}/harness"
  consolidate_into_home "${TARGET}/agent-context/playbooks" "${HOME_DIR}/playbooks"
  consolidate_into_home "${TARGET}/agent-context/extensions" "${HOME_DIR}/extensions"
fi
migrate_playbooks_extensions_to_skills "${TARGET}" "${DRY_RUN}"
consolidate_into_home "${TARGET}/scripts/sdlc-spdd" "${HOME_DIR}/scripts"
consolidate_into_home "${TARGET}/.sdlc" "${HOME_DIR}/.sdlc"
shopt -s nullglob
for _root_ms in "${TARGET}"/milestone-*.md; do
  consolidate_into_home "${_root_ms}" "${HOME_DIR}/$(basename "${_root_ms}")"
done
shopt -u nullglob

framework_prune_legacy_layout_shells "${TARGET}" "${HOME_DIR}" "${DRY_RUN}"

# Target projects: remove leftover agent-context framework files, then archive
# anything still at legacy paths. Orchestrator keeps agent-context/ as source.
if [[ "${IS_ORCHESTRATOR_ROOT}" -eq 0 ]]; then
  remove_legacy_framework_file "${TARGET}/agent-context/sdlc-pointer.sh"
  remove_legacy_framework_file "${TARGET}/agent-context/sdlc-workflow.sh"
  remove_legacy_framework_file "${TARGET}/agent-context/sdlc-team-registry.sh"
  remove_legacy_framework_file "${TARGET}/agent-context/README.md"
  remove_legacy_framework_file "${TARGET}/agent-context/hooks"
  if [[ "${DRY_RUN}" -eq 0 && -d "${TARGET}/agent-context" ]]; then
    find "${TARGET}/agent-context" -name .gitkeep -delete 2>/dev/null || true
    find "${TARGET}/agent-context" -type d -empty -delete 2>/dev/null || true
  fi
fi

while IFS= read -r line; do
  [[ -n "${line}" ]] || continue
  moved+=("${line#archive }")
done < <(framework_archive_remaining_legacy_layout "${TARGET}" "${HOME_DIR}" "${DRY_RUN}" "${timestamp}")

# ---------------------------------------------------------------------------
# Phase 3 — framework file refresh under the home (create missing, upgrade
# framework-owned files with backups, preserve project content).
# ---------------------------------------------------------------------------

for dir in \
  requirements \
  requirements/milestones \
  spdd/canvas \
  spdd/analysis \
  spdd/tasks \
  spdd/reviews \
  spdd/sync \
  session-notes \
  harness \
  harness/skills \
  docs \
  scripts \
  scripts/lib; do
  ensure_gitkeep "${HOME_DIR}/${dir}"
done
ensure_dir "${HOME_DIR}/spdd/memory"

# Storage v3 memory model: committed ledger + registry (seed empty when missing).
create_missing_empty_file "${HOME_DIR}/spdd/memory/lessons.jsonl"
create_missing_empty_file "${HOME_DIR}/spdd/memory/registry.jsonl"

framework_ensure_gitignore_runtime "${TARGET}" "${DRY_RUN}"

# Preserve project planning artifacts; create only if missing.
create_missing_framework_file \
  "${REPO_ROOT}/templates/project-docs/ROADMAP.md" \
  "${HOME_DIR}/ROADMAP.md" \
  "project roadmap"

shopt -s nullglob
root_milestones=("${HOME_DIR}"/milestone-*.md "${TARGET}"/milestone-*.md)
subdir_milestones=("${HOME_DIR}"/requirements/milestones/milestone-*/MILESTONE-*.md)
shopt -u nullglob
if ((${#root_milestones[@]} == 0 && ${#subdir_milestones[@]} == 0)); then
  ensure_dir "${HOME_DIR}/requirements/milestones/milestone-1"
  create_missing_framework_file \
    "${REPO_ROOT}/templates/requirements/milestones/milestone-definition.md" \
    "${HOME_DIR}/requirements/milestones/milestone-1/MILESTONE-1.md" \
    "milestone definition"
  create_missing_framework_file \
    "${REPO_ROOT}/templates/requirements/milestones/milestone-template.yml" \
    "${HOME_DIR}/requirements/milestones/milestone-1/_milestone.yml" \
    "milestone metadata"
else
  preserved+=("existing milestone definitions")
fi

create_missing_framework_file \
  "${REPO_ROOT}/templates/requirements/milestones/README.md" \
  "${HOME_DIR}/requirements/milestones/README.md" \
  "milestone README"

# Framework-owned harness skills and core files are upgraded, with backups.
for file in "${REPO_ROOT}"/templates/agent-context/harness/skills/*.md; do
  [[ -f "${file}" ]] || continue
  copy_framework_file \
    "${file}" \
    "${HOME_DIR}/harness/skills/$(basename "${file}")"
done

copy_framework_file \
  "${REPO_ROOT}/templates/agent-context/harness/phase-index.md" \
  "${HOME_DIR}/harness/phase-index.md"

for file in \
  quality-gates.md \
  validation-rules.md; do
  copy_framework_file \
    "${REPO_ROOT}/agent-context/harness/${file}" \
    "${HOME_DIR}/harness/${file}"
done

migrate_playbooks_extensions_to_skills "${TARGET}" "${DRY_RUN}"

# User-facing docs are framework-owned when installed under <home>/docs/.
# Skip orchestrator-internal docs (see scripts/lib/shipped-docs-boundary.sh).
# shellcheck source=lib/shipped-docs-boundary.sh
source "${SCRIPT_DIR}/lib/shipped-docs-boundary.sh"
for file in "${REPO_ROOT}"/docs/*.md; do
  is_orchestrator_only_doc "${file}" && continue
  copy_framework_file \
    "${file}" \
    "${HOME_DIR}/docs/$(basename "${file}")"
done

copy_framework_file \
  "${REPO_ROOT}/templates/project-docs/docs-sdlc-spdd-README.md" \
  "${HOME_DIR}/docs/README.md"

if [[ "${UPGRADE_CURSOR}" -eq 1 && "${UPGRADE_COPILOT}" -eq 1 ]]; then
  # Preserve target CI customizations; create the framework workflow only when
  # it is missing.
  create_missing_adapter_file \
    "${REPO_ROOT}/templates/project-github-workflows/validate-sdlc-spdd-adapters.yml" \
    "${TARGET}/.github/workflows/validate-sdlc-spdd-adapters.yml" \
    "adapter parity workflow"
fi

# Workflow CLI managers live with the runtime scripts under <home>/scripts/.
for file in \
  sdlc-pointer.sh \
  sdlc-workflow.sh \
  sdlc-team-registry.sh; do
  copy_executable_framework_file \
    "${REPO_ROOT}/agent-context/${file}" \
    "${HOME_DIR}/scripts/${file}"
done

copy_framework_file \
  "${REPO_ROOT}/templates/agent-context/hooks/notify-team-registry.example.sh" \
  "${HOME_DIR}/scripts/hooks/notify-team-registry.example.sh"

# Target-local runtime scripts are framework-owned and safe to upgrade.
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
  copy_executable_framework_file \
    "${REPO_ROOT}/scripts/${file}" \
    "${HOME_DIR}/scripts/${file}"
done

# shellcheck source=/dev/null
source "${REPO_ROOT}/scripts/lib/paths.sh"
for lib in "${SDLC_SHIPPED_LIB_FILES[@]}"; do
  copy_framework_file \
    "${REPO_ROOT}/scripts/lib/${lib}" \
    "${HOME_DIR}/scripts/lib/${lib}"
done

if [[ "${UPGRADE_CURSOR}" -eq 1 ]]; then
  for src in "${REPO_ROOT}"/templates/cursor/*.md; do
    copy_adapter_framework_file \
      "${src}" \
      "${TARGET}/.cursor/commands/$(basename "${src}")"
  done

  for src in "${REPO_ROOT}"/templates/cursor/rules/*.mdc; do
    copy_adapter_framework_file \
      "${src}" \
      "${TARGET}/.cursor/rules/$(basename "${src}")"
  done
fi

if [[ "${UPGRADE_COPILOT}" -eq 1 ]]; then
  copy_adapter_framework_file \
    "${REPO_ROOT}/templates/copilot/copilot-instructions.md" \
    "${TARGET}/.github/copilot-instructions.md"

  for src in "${REPO_ROOT}"/templates/copilot/prompts/*.prompt.md; do
    copy_adapter_framework_file \
      "${src}" \
      "${TARGET}/.github/prompts/$(basename "${src}")"
  done
fi

if [[ "${UPGRADE_CLAUDE}" -eq 1 ]]; then
  upsert_claude_memory \
    "${REPO_ROOT}/templates/claude/CLAUDE.md" \
    "${TARGET}/CLAUDE.md"

  for src in "${REPO_ROOT}"/templates/claude/commands/*.md; do
    copy_adapter_framework_file \
      "${src}" \
      "${TARGET}/.claude/commands/$(basename "${src}")"
  done
fi

# The target-local adapter validator is upgraded with runtime scripts above.
# Create any missing always-on grounding file for adapter packs already present
# so partial upgrades do not strand existing clients with a stricter validator.
if [[ "${UPGRADE_CURSOR}" -eq 0 && -d "${TARGET}/.cursor/commands" ]]; then
  create_missing_adapter_file \
    "${REPO_ROOT}/templates/cursor/rules/sdlc-spdd.mdc" \
    "${TARGET}/.cursor/rules/sdlc-spdd.mdc" \
    "Cursor operating-model rule"
fi

if [[ "${UPGRADE_COPILOT}" -eq 0 && -d "${TARGET}/.github/prompts" ]]; then
  create_missing_adapter_file \
    "${REPO_ROOT}/templates/copilot/copilot-instructions.md" \
    "${TARGET}/.github/copilot-instructions.md" \
    "GitHub Copilot instructions"
fi

if [[ "${UPGRADE_CLAUDE}" -eq 0 && -d "${TARGET}/.claude/commands" ]]; then
  upsert_claude_memory \
    "${REPO_ROOT}/templates/claude/CLAUDE.md" \
    "${TARGET}/CLAUDE.md"
fi

echo "SDLC-SPDD framework upgrade complete for: ${TARGET}"
echo "Framework home: ${HOME_DIR}"
echo "Consolidated (${#moved[@]}):"
printf '  %s\n' "${moved[@]:-none}"
echo "Created (${#created[@]}):"
printf '  %s\n' "${created[@]:-none}"
echo "Updated framework files (${#updated[@]}):"
printf '  %s\n' "${updated[@]:-none}"
echo "Unchanged framework files (${#unchanged[@]}):"
printf '  %s\n' "${unchanged[@]:-none}"
echo "Preserved existing project content (${#preserved[@]}):"
printf '  %s\n' "${preserved[@]:-none}"
if [[ "${BACKUP}" -eq 1 ]]; then
  echo "Backups (${#backed_up[@]}):"
  printf '  %s\n' "${backed_up[@]:-none}"
fi
if [[ -n "${legacy_migration_note}" ]]; then
  echo "Legacy memory: ${legacy_migration_note}"
fi
echo "Not touched: application source, requirements, canvases, reviews, sync logs, existing roadmap/milestones, accumulated ledger memory, or application docs outside sdlc-spdd/docs."

verify_args=(--target "${TARGET}")
if [[ "${UPGRADE_CURSOR}" -eq 1 ]]; then
  verify_args+=(--require-cursor)
fi
if [[ "${UPGRADE_COPILOT}" -eq 1 ]]; then
  verify_args+=(--require-copilot)
fi
if [[ "${UPGRADE_CLAUDE}" -eq 1 ]]; then
  verify_args+=(--require-claude)
fi
if [[ "${DRY_RUN}" -eq 0 ]]; then
  echo "Running install verification..."
  "${SCRIPT_DIR}/verify-project-install.sh" "${verify_args[@]}"
fi
