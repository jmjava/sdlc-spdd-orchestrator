#!/usr/bin/env bash
# Proving test: a new CCN-12 function fails; an unchanged hotspot does not.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK="${SCRIPT_DIR}/check-complexity.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git -C "$TMP" init -q
git -C "$TMP" config user.email "sa@example.test"
git -C "$TMP" config user.name "SA"
cat > "$TMP/hotspot.py" <<'PY'
def hotspot(x):
    if x == 1: return 1
    if x == 2: return 2
    if x == 3: return 3
    if x == 4: return 4
    if x == 5: return 5
    if x == 6: return 6
    if x == 7: return 7
    if x == 8: return 8
    if x == 9: return 9
    if x == 10: return 10
    if x == 11: return 11
    return 0
PY
git -C "$TMP" add hotspot.py
git -C "$TMP" commit -qm base
# Unchanged hotspot must PASS
if ! python3 "$CHECK" --repo "$TMP" --base HEAD --paths .; then
  echo "expected PASS on identical HEAD vs HEAD" >&2
  exit 1
fi
cat > "$TMP/new_messy.py" <<'PY'
def messy(x):
    if x == 1: return 1
    if x == 2: return 2
    if x == 3: return 3
    if x == 4: return 4
    if x == 5: return 5
    if x == 6: return 6
    if x == 7: return 7
    if x == 8: return 8
    if x == 9: return 9
    if x == 10: return 10
    if x == 11: return 11
    return 0
PY
git -C "$TMP" add new_messy.py
git -C "$TMP" commit -qm worse
if python3 "$CHECK" --repo "$TMP" --base HEAD~1 --paths .; then
  echo "expected FAIL on new CCN-12 function" >&2
  exit 1
fi
echo "test-check-complexity: PASS"
