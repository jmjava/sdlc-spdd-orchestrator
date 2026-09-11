#!/usr/bin/env bash
# Leftover #11 proving test: U2 must execute .cursor/install.sh, not only
# bash -n + greps. Dry-runs the PATH write and the sdlc-engine verify path
# with a stub setup-engine-venv.sh. Leftover #10 --path-only persist stays.
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

write_stub_setup() {
  local repo="$1"
  local mode="${2:-ok}"
  mkdir -p "${repo}/scripts"
  if [[ "${mode}" == "ok" ]]; then
    cat > "${repo}/scripts/setup-engine-venv.sh" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${ROOT}/.venv/bin"
printf '%s\n' '#!/bin/sh' 'echo sdlc-engine-help' > "${ROOT}/.venv/bin/sdlc-engine"
chmod +x "${ROOT}/.venv/bin/sdlc-engine"
printf '%s\n' "stub-setup-ran" > "${ROOT}/.venv/setup-ran"
EOF
  else
    cat > "${repo}/scripts/setup-engine-venv.sh" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${ROOT}/.venv"
printf '%s\n' "stub-setup-ran-no-engine" > "${ROOT}/.venv/setup-ran"
EOF
  fi
  chmod +x "${repo}/scripts/setup-engine-venv.sh"
}

run_install() {
  local home="$1" repo="$2"
  env -i \
    HOME="${home}" \
    PATH="/usr/bin:/bin" \
    USER=test \
    SDLC_INSTALL_ROOT="${repo}" \
    SDLC_INSTALL_SKIP_SYSTEM_DEPS=1 \
    bash "${INSTALL_SH}"
}

noninteractive_which() {
  local home="$1"
  env -i HOME="${home}" PATH="/usr/bin:/bin" USER=test \
    bash --noprofile --norc -c 'source "$HOME/.bashrc"; command -v sdlc-engine' 2>/dev/null || true
}

echo "== leftover #11: U2 runs install.sh =="

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
fake_home="${scratch}/home"
fake_repo="${scratch}/repo"
mkdir -p "${fake_home}" "${fake_repo}"

write_ubuntu_rcs "${fake_home}"
write_stub_setup "${fake_repo}" ok
if run_install "${fake_home}" "${fake_repo}"; then
  ok "install.sh runs (not bash -n / grep only)"
else
  bad "install.sh exited non-zero against a stub venv"
fi

if [[ -f "${fake_repo}/.venv/setup-ran" ]]; then
  ok "install.sh invoked setup-engine-venv.sh"
else
  bad "install.sh never invoked setup-engine-venv.sh"
fi

if [[ -x "${fake_repo}/.venv/bin/sdlc-engine" ]]; then
  ok "install.sh left an executable sdlc-engine"
else
  bad "install.sh did not verify/create sdlc-engine"
fi

found="$(noninteractive_which "${fake_home}")"
if [[ "${found}" == "${fake_repo}/.venv/bin/sdlc-engine" ]]; then
  ok "full install.sh PATH write is visible to non-interactive bashrc"
else
  bad "full install.sh PATH write missed non-interactive bashrc (got '${found}')"
fi

if [[ ! -e "${fake_home}/.git/hooks" && ! -e "${fake_repo}/.git/hooks" ]]; then
  ok "install.sh did not write .git/hooks"
else
  bad "install.sh wrote .git/hooks"
fi

missing_home="${scratch}/missing-home"
missing_repo="${scratch}/missing-repo"
mkdir -p "${missing_home}" "${missing_repo}"
write_ubuntu_rcs "${missing_home}"
write_stub_setup "${missing_repo}" missing
if run_install "${missing_home}" "${missing_repo}" >/dev/null 2>&1; then
  bad "install.sh succeeded without sdlc-engine"
else
  ok "install.sh refuses when sdlc-engine is missing"
fi

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "install.sh execution contract FAILED." >&2
  exit 1
fi
echo "install.sh execution contract passed."
