#!/usr/bin/env bash
# Push jmjava/guide tip + pin tags into standalone jmjava/orch-guide.
# Requires: empty repo https://github.com/jmjava/orch-guide (NOT a GitHub fork).
set -euo pipefail

ORCH_URL="${ORCH_GUIDE_GIT_URL:-https://github.com/jmjava/orch-guide.git}"
GUIDE_HOME="${GUIDE_HOME:-}"
REMOTE_NAME="${ORCH_GUIDE_REMOTE:-orch}"

if [[ -z "${GUIDE_HOME}" ]]; then
  if [[ -d "${HOME}/github/jmjava/guide/.git" ]]; then
    GUIDE_HOME="${HOME}/github/jmjava/guide"
  elif [[ -d "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/guide/.git" ]]; then
    GUIDE_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/guide"
  elif [[ -d /agent/repos/guide/.git ]]; then
    GUIDE_HOME=/agent/repos/guide
  else
    echo "FAIL: set GUIDE_HOME to a jmjava/guide checkout" >&2
    exit 1
  fi
fi

cd "${GUIDE_HOME}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "FAIL: ${GUIDE_HOME} is not a git repo" >&2
  exit 1
fi

# Refuse if destination looks like embabel/guide
if [[ "${ORCH_URL}" =~ embabel/guide ]]; then
  echo "FAIL: refusing to push to embabel/guide URL: ${ORCH_URL}" >&2
  exit 1
fi

echo "== bootstrap orch-guide =="
echo "  GUIDE_HOME: ${GUIDE_HOME}"
echo "  ORCH_URL:   ${ORCH_URL}"
echo "  HEAD:       $(git rev-parse --short HEAD) ($(git rev-parse --abbrev-ref HEAD))"

if ! git ls-remote "${ORCH_URL}" HEAD >/dev/null 2>&1; then
  echo "FAIL: cannot reach ${ORCH_URL} — create empty jmjava/orch-guide first" >&2
  exit 1
fi

# Empty repo should have no HEAD yet; warn if already populated
if git ls-remote --exit-code "${ORCH_URL}" HEAD >/dev/null 2>&1; then
  echo "WARN: ${ORCH_URL} already has commits; push may need --force (not used by default)"
fi

if git remote get-url "${REMOTE_NAME}" >/dev/null 2>&1; then
  git remote set-url "${REMOTE_NAME}" "${ORCH_URL}"
else
  git remote add "${REMOTE_NAME}" "${ORCH_URL}"
fi
# Never configure push toward embabel via this remote name confusion
git remote set-url --push "${REMOTE_NAME}" "${ORCH_URL}"

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${branch}" != "main" ]]; then
  echo "WARN: not on main (on ${branch}); pushing this branch tip as main"
fi

echo "== pushing main =="
git push -u "${REMOTE_NAME}" HEAD:main

echo "== pushing pin tags =="
for tag in sdlc-spdd-projection-v1 sdlc-spdd-projection-v2; do
  if git rev-parse "${tag}" >/dev/null 2>&1; then
    git push "${REMOTE_NAME}" "refs/tags/${tag}"
  else
    echo "WARN: missing local tag ${tag}"
  fi
done

echo "OK: orch-guide bootstrap push complete"
echo "Next: retarget orchestrator GUIDE_GIT_URL → ${ORCH_URL}"
echo "Then (later): hard-reset jmjava/guide to embabel/guide — see docs/orch-guide-cutover.md"
