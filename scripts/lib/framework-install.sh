#!/usr/bin/env bash
# Orchestrator-only helpers for init-project.sh and upgrade-project.sh.
# Not shipped to target projects.

framework_ensure_dir() {
  local dir="$1"
  local dry_run="$2"
  if [[ "${dry_run}" -eq 1 ]]; then
    echo "[dry-run] would mkdir -p ${dir}"
  else
    mkdir -p "${dir}"
  fi
}

# Rewrite framework paths inside an installed IDE adapter file so stubs at the
# target repo root (.cursor/, .github/, .claude/, CLAUDE.md) reference the
# single-folder home <target>/sdlc-spdd/ (storage v3). Templates keep the
# orchestrator-relative paths; the rewrite happens only at install time.
framework_rewrite_adapter_paths() {
  local file="$1"
  [[ -f "${file}" ]] || return 0
  sed -E -i \
    -e 's#(\./)?scripts/sdlc-spdd/#\1sdlc-spdd/scripts/#g' \
    -e 's#\./scripts/sdlc\.sh#./sdlc-spdd/scripts/sdlc.sh#g' \
    -e 's#docs/sdlc-spdd/#sdlc-spdd/docs/#g' \
    -e 's#agent-context/harness/#sdlc-spdd/harness/#g' \
    -e 's#agent-context/harness/skills/#sdlc-spdd/harness/skills/#g' \
    -e 's#(^|[^/[:alnum:]-])spdd/#\1sdlc-spdd/spdd/#g' \
    -e 's#(^|[^/[:alnum:]])\.sdlc/#\1sdlc-spdd/.sdlc/#g' \
    -e 's#(^|[^/[:alnum:]-])requirements/#\1sdlc-spdd/requirements/#g' \
    -e 's#(^|[^/[:alnum:]-])session-notes/#\1sdlc-spdd/session-notes/#g' \
    -e 's#(^|[^/[:alnum:]-])ROADMAP\.md#\1sdlc-spdd/ROADMAP.md#g' \
    "${file}"
}

# Ensure the target .gitignore covers the gitignored runtime under the home.
framework_ensure_gitignore_runtime() {
  local target="$1"
  local dry_run="${2:-0}"
  local gitignore="${target}/.gitignore"
  if [[ -f "${gitignore}" ]] && grep -qE '^sdlc-spdd/\.sdlc/?$' "${gitignore}"; then
    return 0
  fi
  if [[ "${dry_run}" -eq 1 ]]; then
    echo "[dry-run] would append sdlc-spdd/.sdlc/ to ${gitignore}"
    return 0
  fi
  {
    if [[ -s "${gitignore}" ]]; then
      tail -c 1 "${gitignore}" | read -r _ || echo
    fi
    echo "# SDLC-SPDD gitignored runtime (sessions, staged lessons, sqlite cache)"
    echo "sdlc-spdd/.sdlc/"
  } >> "${gitignore}"
}

# Merge children from src_dir into dest_dir (dest wins on file conflicts).
# Removes src_dir when empty. Used by upgrade-project consolidation (storage v3).
framework_merge_dir_into() {
  local src_dir="$1"
  local dest_dir="$2"
  local dry_run="$3"
  local child name

  [[ -d "${src_dir}" ]] || return 0
  if [[ "${dry_run}" -eq 1 ]]; then
    echo "[dry-run] would mkdir -p ${dest_dir}" >&2
  else
    mkdir -p "${dest_dir}"
  fi

  shopt -s nullglob
  for child in "${src_dir}"/* "${src_dir}"/.[!.]* "${src_dir}"/..?*; do
    [[ -e "${child}" ]] || continue
    name="$(basename "${child}")"
    [[ "${name}" == "." || "${name}" == ".." ]] && continue
    framework_consolidate_path "${child}" "${dest_dir}/${name}" "${dry_run}"
  done
  shopt -u nullglob

  if [[ "${dry_run}" -eq 0 ]]; then
    find "${src_dir}" -depth -type d -empty -delete 2>/dev/null || true
    rmdir "${src_dir}" 2>/dev/null || true
  fi
}

# Move or merge src into dest under the v3 home. Idempotent; dest wins conflicts.
# Emits one line: move|merge|keep|skip followed by relative description (for logging).
framework_consolidate_path() {
  local src="$1"
  local dest="$2"
  local dry_run="$3"
  local target="${4:-}"
  local rel_src rel_dest

  [[ -e "${src}" ]] || return 0

  if [[ -n "${target}" ]]; then
    rel_src="${src#"${target}/"}"
    rel_dest="${dest#"${target}/"}"
  else
    rel_src="${src}"
    rel_dest="${dest}"
  fi

  if [[ "${src}" -ef "${dest}" ]]; then
    return 0
  fi

  if [[ ! -e "${dest}" ]]; then
    if [[ "${dry_run}" -eq 1 ]]; then
      echo "[dry-run] would move ${rel_src} -> ${rel_dest}" >&2
    else
      mkdir -p "$(dirname "${dest}")"
      mv "${src}" "${dest}"
    fi
    echo "move ${rel_src} -> ${rel_dest}"
    return 0
  fi

  if [[ -d "${src}" && -d "${dest}" ]]; then
    framework_merge_dir_into "${src}" "${dest}" "${dry_run}"
    echo "merge ${rel_src} -> ${rel_dest}"
    return 0
  fi

  if [[ -f "${src}" && -f "${dest}" ]]; then
    if [[ "${dry_run}" -eq 1 ]]; then
      echo "[dry-run] would keep ${rel_dest} (drop duplicate ${rel_src})" >&2
    else
      rm -f "${src}"
    fi
    echo "keep ${rel_dest}"
    return 0
  fi

  echo "skip type mismatch: ${rel_src} vs ${rel_dest}" >&2
  echo "skip ${rel_src}"
  return 0
}

# Drop empty legacy shells at repo root once the home copy exists.
framework_prune_legacy_layout_shells() {
  local target="$1"
  local home="$2"
  local dry_run="$3"
  local rel path

  for rel in requirements spdd session-notes harness scripts/sdlc-spdd docs/sdlc-spdd agent-context; do
    path="${target}/${rel}"
    [[ -e "${path}" ]] || continue
    case "${rel}" in
      requirements|spdd|session-notes|harness)
        [[ -d "${home}/${rel}" ]] || continue
        ;;
      scripts/sdlc-spdd)
        [[ -d "${home}/scripts" ]] || continue
        ;;
      docs/sdlc-spdd)
        [[ -d "${home}/docs" ]] || continue
        ;;
      agent-context)
        ;;
    esac
    if [[ "${dry_run}" -eq 1 ]]; then
      echo "[dry-run] would prune empty legacy dir ${rel}" >&2
    else
      find "${path}" -depth -type d -empty -delete 2>/dev/null || true
      rmdir "${path}" 2>/dev/null || true
    fi
  done

  if [[ "${dry_run}" -eq 0 ]]; then
    rm -f "${target}/scripts/.gitkeep" 2>/dev/null || true
    rmdir "${target}/scripts" 2>/dev/null || true
    rmdir "${target}/docs" 2>/dev/null || true
  fi
}
