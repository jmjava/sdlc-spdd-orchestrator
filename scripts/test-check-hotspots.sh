#!/usr/bin/env bash
# Proving test: fail only when a changed Python file is both complex and high-churn.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK="${SCRIPT_DIR}/check-hotspots.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git_commit() {
  git -C "$TMP" -c user.email="sa@example.test" -c user.name="SA" commit -qm "$1"
}

write_complex() {
  cat > "$1" <<'PY'
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
}

git -C "$TMP" init -q
for i in 1 2 3 4 5 6 7 8 9 10; do
  printf 'def filler_%s():\n    return %s\n' "$i" "$i" > "$TMP/filler_${i}.py"
done
git -C "$TMP" add filler_1.py filler_2.py filler_3.py filler_4.py filler_5.py \
  filler_6.py filler_7.py filler_8.py filler_9.py filler_10.py
git_commit "fillers"

write_complex "$TMP/hot_complex.py"
git -C "$TMP" add hot_complex.py
git_commit "hot complex"
for n in 1 2 3 4; do
  printf '\n# rev %s\n' "$n" >> "$TMP/hot_complex.py"
  git -C "$TMP" add hot_complex.py
  git_commit "hot complex $n"
done

printf 'def calm():\n    return 1\n' > "$TMP/hot_simple.py"
git -C "$TMP" add hot_simple.py
git_commit "hot simple"
for n in 1 2 3; do
  printf '\n# rev %s\n' "$n" >> "$TMP/hot_simple.py"
  git -C "$TMP" add hot_simple.py
  git_commit "hot simple $n"
done

write_complex "$TMP/cold_complex.py"
git -C "$TMP" add cold_complex.py
git_commit "cold complex"

# No diff: an existing hotspot is not a failure.
if ! python3 "$CHECK" --repo "$TMP" --base HEAD --paths . --fraction 0.10; then
  echo "expected PASS when nothing changed" >&2
  exit 1
fi

printf '\n# touch cold\n' >> "$TMP/cold_complex.py"
git -C "$TMP" add cold_complex.py
git_commit "touch cold"
if ! python3 "$CHECK" --repo "$TMP" --base HEAD~1 --paths . --fraction 0.10; then
  echo "expected PASS for a complex file outside the top churn set" >&2
  exit 1
fi

printf '\n# touch simple\n' >> "$TMP/hot_simple.py"
git -C "$TMP" add hot_simple.py
git_commit "touch simple"
if ! python3 "$CHECK" --repo "$TMP" --base HEAD~1 --paths . --fraction 0.10; then
  echo "expected PASS for a high-churn file that is not complex" >&2
  exit 1
fi

printf '\n# touch hot\n' >> "$TMP/hot_complex.py"
git -C "$TMP" add hot_complex.py
git_commit "touch hot"
if python3 "$CHECK" --repo "$TMP" --base HEAD~1 --paths . --fraction 0.10; then
  echo "expected FAIL when the changed file is complex and high-churn" >&2
  exit 1
fi

echo "test-check-hotspots: PASS"
