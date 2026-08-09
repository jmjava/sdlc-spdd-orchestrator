# Shared helpers for the live consumer matrix.
# shellcheck shell=bash

LIVE_CONSUMER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${LIVE_CONSUMER_DIR}/../.." && pwd)"
SEED_DIR="${LIVE_CONSUMER_DIR}/seed"
WORK_ID="${LIVE_WORK_ID:-FEAT-001-hello-live}"
DONE_WORK_ID="${LIVE_DONE_WORK_ID:-FEAT-002-done-live}"
SDLC_USER="${SDLC_USER:-live-matrix}"

# Default: ephemeral mktemp. For Cursor UI reopen, set:
#   LIVE_CONSUMER_ROOT=/tmp/sdlc-spdd-live LIVE_CONSUMER_KEEP=1
LIVE_CONSUMER_ROOT="${LIVE_CONSUMER_ROOT:-}"
LIVE_CONSUMER_KEEP="${LIVE_CONSUMER_KEEP:-0}"

# Preserve counters when scenarios re-source this file.
pass=${pass:-0}
fail=${fail:-0}
skip=${skip:-0}

ok() {
  echo "  ok   $1"
  pass=$((pass + 1))
}

bad() {
  echo "  FAIL $1" >&2
  fail=$((fail + 1))
}

skipped() {
  echo "  skip $1"
  skip=$((skip + 1))
}

live_resolve_root() {
  if [[ -n "${LIVE_CONSUMER_ROOT}" ]]; then
    mkdir -p "$(dirname "${LIVE_CONSUMER_ROOT}")"
    printf '%s\n' "${LIVE_CONSUMER_ROOT}"
    return
  fi
  if [[ "${LIVE_CONSUMER_KEEP}" == "1" ]]; then
    printf '%s\n' "/tmp/sdlc-spdd-live"
    return
  fi
  mktemp -d /tmp/sdlc-spdd-live.XXXXXX
}

live_home() {
  local root="$1"
  if [[ -d "${root}/sdlc-spdd" ]]; then
    printf '%s/sdlc-spdd\n' "${root}"
  else
    printf '%s\n' "${root}"
  fi
}

live_runtime() {
  printf '%s/.sdlc\n' "$(live_home "$1")"
}

live_flush() {
  local root="$1"
  if [[ -e "${root}" ]]; then
    rm -rf "${root}"
  fi
}

live_seed_app() {
  local root="$1"
  mkdir -p "${root}"
  # Copy seed tree (app + pre-staged milestone/canvas).
  cp -a "${SEED_DIR}/." "${root}/"
  # Tiny git repo so commit-message / branch notes behave realistically.
  git -C "${root}" init -q -b main
  git -C "${root}" config user.email "live-matrix@example.com"
  git -C "${root}" config user.name "Live Matrix"
  # Ignore local SDLC state that must not be treated as product code.
  cat >"${root}/.gitignore" <<'EOF'
.sdlc/
__pycache__/
*.pyc
.venv/
EOF
  git -C "${root}" add -A
  git -C "${root}" commit -q -m "seed: live consumer fixture"
}

live_install_cursor() {
  local root="$1"
  "${REPO_ROOT}/scripts/setup-agent-prompts.sh" --target "${root}" --cursor --force
}

live_sdlc() {
  local root="$1"
  shift
  local cli="${root}/sdlc-spdd/scripts/sdlc.sh"
  if [[ ! -x "${cli}" ]]; then
    cli="${root}/scripts/sdlc-spdd/sdlc.sh"
  fi
  SDLC_USER="${SDLC_USER}" SDLC_ROOT="${root}" "${cli}" "$@"
}

live_summary() {
  echo
  echo "Results: ${pass} passed, ${fail} failed, ${skip} skipped"
  if [[ "${fail}" -gt 0 ]]; then
    return 1
  fi
  return 0
}
