#!/usr/bin/env bash
# Deploy docs/ + locally generated recordings to GitHub Pages (gh-pages branch).
# MP4s stay gitignored on main; this script copies them from your working tree only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: deploy-docs-pages-local.sh [--dry-run]

Build a Pages tree from docs/ plus local docs/demos/recordings/*.mp4 (gitignored on
main) and force-push to the gh-pages branch.

Requires: git, rsync, push access to origin.

One-time repo setup: Settings → Pages → Deploy from branch → gh-pages / root.

Options:
  --dry-run   Show actions without pushing
  --help      Print this help message
EOF
}

DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

STAGING="$(mktemp -d)"
cleanup() { rm -rf "${STAGING}"; }
trap cleanup EXIT

rsync -a \
  --exclude 'demos/audio/' \
  --exclude 'demos/animations/media/' \
  --exclude 'demos/animations/timing.json' \
  --exclude 'demos/animations/__pycache__/' \
  "${ROOT}/docs/" "${STAGING}/"

RECORDINGS="${ROOT}/docs/demos/recordings"
mkdir -p "${STAGING}/demos/recordings"
shopt -s nullglob
mp4s=("${RECORDINGS}"/*.mp4)
shopt -u nullglob
if ((${#mp4s[@]} == 0)); then
  echo "warning: no local MP4s in docs/demos/recordings/ — Pages videos will be missing" >&2
else
  cp "${mp4s[@]}" "${STAGING}/demos/recordings/"
  echo "Including ${#mp4s[@]} recording(s) from local tree (not committed on main)."
fi

REMOTE="$(git -C "${ROOT}" remote get-url origin)"
echo "Staging site at ${STAGING} ($(find "${STAGING}" -type f | wc -l) files)"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "[dry-run] would push ${STAGING} → origin gh-pages (${REMOTE})"
  exit 0
fi

pushd "${STAGING}" >/dev/null
git init -q
git checkout -q -b gh-pages
git add -A
git commit -q -m "Deploy docs and local demo recordings ($(date -u +%Y-%m-%dT%H:%MZ))"
git push -f "${REMOTE}" HEAD:gh-pages
popd >/dev/null

echo "OK: pushed gh-pages. Enable branch deploy in repo Pages settings if not already."
