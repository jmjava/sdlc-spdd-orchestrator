#!/usr/bin/env bash
# Shared helpers for SDLC-SPDD runtime scripts (sourced, not executed).
# Installed copies live at sdlc-spdd/scripts/lib/ in target projects.

# Resolve --target to an absolute path (exits on failure).
sdlc_resolve_target() {
  local target="$1"
  cd "${target}" && pwd
}

# ISO-8601 UTC timestamp for index rows and display.
sdlc_timestamp_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Compact UTC timestamp safe for filenames.
sdlc_timestamp_file() {
  date -u +"%Y%m%dT%H%M%SZ"
}

# UTC calendar day (session notes).
sdlc_timestamp_day() {
  date -u +"%Y-%m-%d"
}

# Print usage and exit (message to stderr).
sdlc_die() {
  echo "$1" >&2
  exit "${2:-1}"
}

# Standard unknown-option handler: prints option, usage, exits 1.
sdlc_unknown_option() {
  local opt="$1"
  local usage_fn="${2:-usage}"
  echo "Unknown option: ${opt}" >&2
  "${usage_fn}" >&2
  exit 1
}

# mkdir -p respecting DRY_RUN (pass 1 as second arg when dry-run active).
sdlc_ensure_dir() {
  local path="$1"
  local dry="${2:-0}"
  if [[ "${dry}" -eq 1 ]]; then
    echo "[dry-run] would mkdir -p ${path}"
  else
    mkdir -p "${path}"
  fi
}

# Create a markdown file with a title when missing (respects dry-run).
sdlc_ensure_file() {
  local path="$1"
  local title="$2"
  local dry="${3:-0}"
  if [[ ! -f "${path}" ]]; then
    if [[ "${dry}" -eq 1 ]]; then
      echo "[dry-run] would create ${path}"
    else
      mkdir -p "$(dirname "${path}")"
      printf '# %s\n\n' "${title}" > "${path}"
    fi
  fi
}

# Collapse newlines/pipes and truncate for compact index cells.
sdlc_oneline() {
  local text="$1"
  local max="${2:-100}"
  text="$(printf '%s' "${text}" | tr '\n|' ' /' | tr -s ' ')"
  text="${text# }"
  text="${text% }"
  if (( ${#text} > max )); then
    text="${text:0:max}..."
  fi
  printf '%s' "${text}"
}
