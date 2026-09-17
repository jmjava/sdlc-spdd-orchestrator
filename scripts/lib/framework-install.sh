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

# Placeholder that shields an orchestrator-only path from the install rewrite.
# Kept in one place so the rewrite and its collision guard cannot drift apart.
FRAMEWORK_ORCH_SDLC_SENTINEL='@@FRAMEWORK_ORCH_SDLC_SH@@'

# Rewrite framework paths inside an installed IDE adapter file so stubs at the
# target repo root (.cursor/, .github/, .claude/, CLAUDE.md) reference the
# single-folder home <target>/sdlc-spdd/ (storage v3). Templates keep the
# orchestrator-relative paths; the rewrite happens only at install time.
framework_rewrite_adapter_paths() {
  local file="$1"
  local tmp
  [[ -f "${file}" ]] || return 0
  # Write to a temp file. GNU `sed -i` and BSD/macOS `sed -i ''` disagree;
  # `sed -E -i -e ...` on macOS treats `-e` as the backup suffix and errors
  # with `sed: -e: No such file or directory`.
  tmp="$(mktemp)"
  if grep -Fq "${FRAMEWORK_ORCH_SDLC_SENTINEL}" "${file}"; then
    echo "framework_rewrite_adapter_paths: ${file} already contains ${FRAMEWORK_ORCH_SDLC_SENTINEL}" >&2
    rm -f "${tmp}"
    return 1
  fi
  # Two prose shapes name the orchestrator checkout's own `./scripts/sdlc.sh`
  # as the *alternative* branch beside the installed path:
  #   (in the orchestrator repo: `./scripts/sdlc.sh gate ...`; installed projects: `...`)
  #   ... (or `./scripts/sdlc.sh team` in the orchestrator repo)
  # Rewriting those alongside the primary path leaves both branches spelling the
  # same string, so the sentence claims the two contexts share one entry point.
  # Park the alternative branch behind a sentinel across the rewrite.
  if ! sed -E \
    -e "s#(orchestrator repo: \`)\./scripts/sdlc\.sh#\1${FRAMEWORK_ORCH_SDLC_SENTINEL}#g" \
    -e "s#(\(or \`)\./scripts/sdlc\.sh#\1${FRAMEWORK_ORCH_SDLC_SENTINEL}#g" \
    -e 's#(\./)?scripts/sdlc-spdd/#\1sdlc-spdd/scripts/#g' \
    -e 's#\./scripts/sdlc\.sh#./sdlc-spdd/scripts/sdlc.sh#g' \
    -e "s#${FRAMEWORK_ORCH_SDLC_SENTINEL}#./scripts/sdlc.sh#g" \
    -e 's#docs/sdlc-spdd/#sdlc-spdd/docs/#g' \
    -e 's#agent-context/harness/#sdlc-spdd/harness/#g' \
    -e 's#agent-context/harness/skills/#sdlc-spdd/harness/skills/#g' \
    -e 's#(^|[^/[:alnum:]-])spdd/#\1sdlc-spdd/spdd/#g' \
    -e 's#(^|[^/[:alnum:]])\.sdlc/#\1sdlc-spdd/.sdlc/#g' \
    -e 's#(^|[^/[:alnum:]-])requirements/#\1sdlc-spdd/requirements/#g' \
    -e 's#(^|[^/[:alnum:]-])session-notes/#\1sdlc-spdd/session-notes/#g' \
    -e 's#(^|[^/[:alnum:]-])ROADMAP\.md#\1sdlc-spdd/ROADMAP.md#g' \
    "${file}" > "${tmp}"; then
    rm -f "${tmp}"
    return 1
  fi
  mv "${tmp}" "${file}"
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

# True when target is this orchestrator repo (framework source lives at root).
framework_is_orchestrator_root() {
  local target="$1"
  [[ -f "${target}/scripts/init-project.sh" \
    && -f "${target}/scripts/upgrade-project.sh" \
    && -d "${target}/templates" \
    && -d "${target}/engine" ]]
}
