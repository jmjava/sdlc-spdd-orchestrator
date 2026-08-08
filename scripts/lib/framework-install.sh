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
    -e 's#agent-context/playbooks/#sdlc-spdd/playbooks/#g' \
    -e 's#agent-context/extensions/#sdlc-spdd/extensions/#g' \
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
