#!/usr/bin/env bash
# Verify relative Markdown links to docs/*.md (and repo-root *.md) resolve.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

fail=0
checked=0

check_link() {
  local from="$1" target="$2"
  local resolved="${from%/*}/${target}"
  resolved="$(python3 -c 'import os,sys; print(os.path.normpath(sys.argv[1]))' "${resolved}")"
  checked=$((checked + 1))
  if [[ ! -e "${resolved}" ]]; then
    echo "BROKEN: ${from} -> ${target} (resolved ${resolved})" >&2
    fail=$((fail + 1))
  fi
}

while IFS= read -r -d '' file; do
  while IFS= read -r link; do
    [[ -z "${link}" ]] && continue
    # skip URLs, anchors-only, mailto
    [[ "${link}" == http:* || "${link}" == https:* || "${link}" == mailto:* ]] && continue
    [[ "${link}" == \#* ]] && continue
    local_target="${link%%#*}"
    [[ -z "${local_target}" ]] && continue
    # skip template placeholders
    [[ "${local_target}" == *"<"* || "${local_target}" == *"..."* ]] && continue
    check_link "${file}" "${local_target}"
  done < <(python3 - "${file}" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
for m in re.finditer(r'\]\(([^)]+)\)', text):
    print(m.group(1).strip())
PY
)
done < <(find . \( -path './.git' -o -path './.venv' -o -path './node_modules' \) -prune -o \
  -type f -name '*.md' -print0)

if (( fail > 0 )); then
  echo "doc link check: ${fail} broken / ${checked} checked" >&2
  exit 1
fi
echo "doc link check: ok (${checked} links)"
