#!/usr/bin/env bash
# U2 contract: committed .cursor/environment.json installs sdlc-engine and
# keeps Cursor Builds enabled. No secrets. Never writes .git/hooks.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_JSON="${REPO_ROOT}/.cursor/environment.json"
INSTALL_SH="${REPO_ROOT}/.cursor/install.sh"

pass=0
fail=0

ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

assert_file() {
  if [[ -f "$1" ]]; then ok "exists $2"; else bad "missing $2 ($1)"; fi
}

assert_contains() {
  local hay="$1" needle="$2" label="$3"
  if grep -Fq -- "${needle}" "${hay}"; then ok "${label}"; else bad "${label} (missing '${needle}' in ${hay})"; fi
}

assert_absent() {
  local hay="$1" needle="$2" label="$3"
  if grep -Fq -- "${needle}" "${hay}"; then bad "${label} (found '${needle}' in ${hay})"; else ok "${label}"; fi
}

echo "== U2 Cloud Environment contract =="

assert_file "${ENV_JSON}" ".cursor/environment.json"
assert_file "${INSTALL_SH}" ".cursor/install.sh"

if python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "${ENV_JSON}"; then
  ok "environment.json is valid JSON"
else
  bad "environment.json is not valid JSON"
fi

if git -C "${REPO_ROOT}" ls-files --error-unmatch .cursor/environment.json >/dev/null 2>&1; then
  ok "environment.json is tracked"
else
  bad "environment.json is not tracked"
fi

if git -C "${REPO_ROOT}" check-ignore -q .cursor/environment.json; then
  bad "environment.json is gitignored"
else
  ok "environment.json is not gitignored"
fi

eval "$(python3 - "${ENV_JSON}" << 'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
def emit(name, value):
    print(f'{name}={json.dumps(value)}')
emit("ENV_NAME", data.get("name", ""))
emit("ENV_INSTALL", data.get("install", ""))
emit("ENV_SNAPSHOT", data.get("snapshot", ""))
emit("ENV_BUILDS", data.get("agentCanUpdateSnapshot", False))
emit("ENV_HAS_BUILD", bool(data.get("build")))
emit("ENV_HAS_IMAGE", bool(data.get("image")))
keys = " ".join(sorted(data.keys()))
print(f'ENV_KEYS={json.dumps(keys)}')
blob = json.dumps(data)
print(f'ENV_BLOB={json.dumps(blob)}')
PY
)"

if [[ "${ENV_NAME}" == "sdlc-spdd-orchestrator" ]]; then
  ok "name is sdlc-spdd-orchestrator"
else
  bad "name is '${ENV_NAME}'"
fi

if [[ "${ENV_INSTALL}" == *"sdlc-engine"* ]] || [[ "${ENV_INSTALL}" == *".cursor/install.sh"* ]] || [[ "${ENV_INSTALL}" == *"setup-engine-venv.sh"* ]]; then
  ok "install mentions sdlc-engine bootstrap"
else
  bad "install does not mention sdlc-engine / install.sh / setup-engine-venv.sh"
fi

if [[ "${ENV_BUILDS}" == "true" || "${ENV_BUILDS}" == "True" ]]; then
  ok "agentCanUpdateSnapshot is true (Builds enabled)"
else
  bad "agentCanUpdateSnapshot must be true (Builds enabled); got '${ENV_BUILDS}'"
fi

if [[ -z "${ENV_SNAPSHOT}" ]]; then
  ok "no committed snapshot id"
else
  bad "do not commit a dashboard snapshot id"
fi

if [[ "${ENV_HAS_BUILD}" == "True" ]]; then
  bad "dockerfile build base disables snapshot updates"
else
  ok "no dockerfile build base"
fi

if [[ "${ENV_HAS_IMAGE}" == "True" ]]; then
  bad "image base disables snapshot updates"
else
  ok "no registry image base"
fi

secret_re='(API_KEY|ACCESS_TOKEN|REFRESH_TOKEN|PRIVATE_KEY|BEGIN [A-Z ]*PRIVATE KEY|password=|secret=)'
if grep -Ei -- "${secret_re}" "${ENV_JSON}" "${INSTALL_SH}"; then
  bad "secret-looking material in environment files"
else
  ok "no secret-looking material in environment files"
fi

assert_contains "${INSTALL_SH}" "setup-engine-venv.sh" "install.sh calls setup-engine-venv.sh"
assert_contains "${INSTALL_SH}" "sdlc-engine" "install.sh verifies sdlc-engine"
assert_contains "${INSTALL_SH}" "Never writes .git/hooks" "install.sh documents no git hooks"
assert_absent "${INSTALL_SH}" ".git/hooks/" "install.sh does not write .git/hooks"

if bash -n "${INSTALL_SH}"; then
  ok "install.sh bash -n"
else
  bad "install.sh bash -n failed"
fi

assert_contains "${REPO_ROOT}/docs/research/uberorchbot-via-sdlc-spdd.md" \
  "this orchestrator (done)" "U2 marked done in research"
assert_contains "${REPO_ROOT}/docs/maintaining-your-project.md" \
  ".cursor/install.sh" "maintaining-your-project documents install.sh"
assert_contains "${REPO_ROOT}/sdlc-spdd/docs/maintaining-your-project.md" \
  ".cursor/install.sh" "sdlc-spdd copy documents install.sh"
assert_contains "${REPO_ROOT}/docs/maintaining-your-project.md" \
  "agentCanUpdateSnapshot" "maintaining-your-project documents Builds"
assert_contains "${REPO_ROOT}/docs/blog/cloud-agents-as-the-sdlc-platform.md" \
  "U2" "blog still names U2"
assert_contains "${REPO_ROOT}/docs/research/kasana-agent-harness-2-0.md" \
  "#268" "kasana leftover notes I3 copy-lock merged"

echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Cloud environment contract FAILED." >&2
  exit 1
fi
echo "Cloud environment contract passed."
