#!/usr/bin/env bash
# Leftover #10 proving test: after Cloud Agent install, non-interactive
# shells that source ~/.bashrc must have sdlc-engine on PATH.
# Ubuntu ~/.bashrc returns before the end when $- lacks i; ~/.profile is login.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SH="${REPO_ROOT}/.cursor/install.sh"

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

write_ubuntu_rcs() {
  local home="$1"
  cat > "${home}/.bashrc" << 'EOF'
# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac
echo "interactive-only tail reached" >&2
EOF
  cat > "${home}/.profile" << 'EOF'
# ~/.profile: executed by the command interpreter for login shells.
if [ -n "$BASH_VERSION" ]; then
  if [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
  fi
fi
EOF
}

# Cloud Agent / SSH-style: non-interactive bash that still sources bashrc.
noninteractive_which() {
  local home="$1"
  env -i HOME="${home}" PATH="/usr/bin:/bin" USER=test \
    bash --noprofile --norc -c 'source "$HOME/.bashrc"; command -v sdlc-engine' 2>/dev/null || true
}

echo "== leftover #10: non-interactive sdlc-engine on PATH =="

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
fake_home="${scratch}/home"
fake_repo="${scratch}/repo"
mkdir -p "${fake_home}" "${fake_repo}/.venv/bin"
printf '%s\n' '#!/bin/sh' 'echo sdlc-engine-ok' > "${fake_repo}/.venv/bin/sdlc-engine"
chmod +x "${fake_repo}/.venv/bin/sdlc-engine"
path_line="export PATH=\"${fake_repo}/.venv/bin:\$PATH\""

write_ubuntu_rcs "${fake_home}"
printf '%s\n' "${path_line}" >> "${fake_home}/.bashrc"
found="$(noninteractive_which "${fake_home}")"
if [[ -z "${found}" ]]; then
  ok "append-after-return misses non-interactive sdlc-engine (bug lock)"
else
  bad "append-after-return unexpectedly found ${found}"
fi

write_ubuntu_rcs "${fake_home}"
HOME="${fake_home}" SDLC_INSTALL_ROOT="${fake_repo}" \
  bash "${INSTALL_SH}" --path-only

found="$(noninteractive_which "${fake_home}")"
if [[ "${found}" == "${fake_repo}/.venv/bin/sdlc-engine" ]]; then
  ok "non-interactive sourced bashrc finds sdlc-engine"
else
  bad "non-interactive sourced bashrc missing sdlc-engine (got '${found}')"
fi

bashrc_path_line="$(grep -n -F -x "${path_line}" "${fake_home}/.bashrc" | head -1 | cut -d: -f1)"
bashrc_return_line="$(grep -n 'return' "${fake_home}/.bashrc" | head -1 | cut -d: -f1)"
if [[ -n "${bashrc_path_line}" && -n "${bashrc_return_line}" && "${bashrc_path_line}" -lt "${bashrc_return_line}" ]]; then
  ok "PATH line precedes interactive-only return in bashrc"
else
  bad "PATH line does not precede interactive-only return (path=${bashrc_path_line} return=${bashrc_return_line})"
fi

login_found="$(
  env -i HOME="${fake_home}" PATH="/usr/bin:/bin" USER=test \
    bash --noprofile --norc -c 'source "$HOME/.profile"; command -v sdlc-engine' 2>/dev/null || true
)"
if [[ "${login_found}" == "${fake_repo}/.venv/bin/sdlc-engine" ]]; then
  ok "login profile finds sdlc-engine"
else
  bad "login profile missing sdlc-engine (got '${login_found}')"
fi

HOME="${fake_home}" SDLC_INSTALL_ROOT="${fake_repo}" \
  bash "${INSTALL_SH}" --path-only
count="$(grep -Fcx "${path_line}" "${fake_home}/.bashrc" || true)"
if [[ "${count}" == "1" ]]; then
  ok "PATH persist is idempotent"
else
  bad "PATH line count in bashrc is ${count}, want 1"
fi

write_ubuntu_rcs "${fake_home}"
printf '%s\n' "${path_line}" >> "${fake_home}/.bashrc"
HOME="${fake_home}" SDLC_INSTALL_ROOT="${fake_repo}" \
  bash "${INSTALL_SH}" --path-only
found="$(noninteractive_which "${fake_home}")"
if [[ "${found}" == "${fake_repo}/.venv/bin/sdlc-engine" ]]; then
  ok "relocates leftover append so non-interactive shells see sdlc-engine"
else
  bad "did not relocate leftover append (got '${found}')"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Non-interactive install PATH contract FAILED." >&2
  exit 1
fi
echo "Non-interactive install PATH contract passed."
