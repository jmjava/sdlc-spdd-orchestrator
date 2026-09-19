#!/usr/bin/env bash
# Proving test: an allowlisted unused name stays green; a new unused function fails.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK="${SCRIPT_DIR}/check-vulture.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/known_dead.py" <<'PY'
def known_dead():
    return 1
PY
cat > "$TMP/whitelist.py" <<'PY'
known_dead  # unused function (vulture whitelist)
PY
if ! VULTURE_WHITELIST="$TMP/whitelist.py" bash "$CHECK" "$TMP/known_dead.py"; then
  echo "expected PASS on allowlisted unused name" >&2
  exit 1
fi
cat > "$TMP/new_dead.py" <<'PY'
def brand_new_unused():
    return 2
PY
if VULTURE_WHITELIST="$TMP/whitelist.py" bash "$CHECK" "$TMP/known_dead.py" "$TMP/new_dead.py"; then
  echo "expected FAIL on a new unused function" >&2
  exit 1
fi
echo "test-check-vulture: PASS"
