#!/usr/bin/env bash
set -euo pipefail

# Regression harness for capture-session-memory.sh memory indexing + rotation.
#
# Covers the relevance-based retrieval model:
#   - per-session entry files under agent-context/memory/sessions/
#   - newest-first session-index.md (with Areas column)
#   - reverse code-area-index.md (area -> work/sessions), agent-supplied --areas
#   - recent-window rotation of session-history.md into archive/
#   - --no-history-rotate and --dry-run behavior
#
# Runs entirely against a throwaway target directory; touches nothing else.
#
# Usage: ./tests/test-session-memory-index.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CAPTURE="${REPO_ROOT}/scripts/capture-session-memory.sh"
START="${REPO_ROOT}/scripts/start-agent-session.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

pass=0
fail=0
ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

mem() { echo "${T}/agent-context/memory${1:+/$1}"; }

assert_file()   { if [[ -f "$1" ]]; then ok "exists: ${1#"${T}"/}"; else bad "missing: ${1#"${T}"/}"; fi; }
assert_absent() { if [[ ! -e "$1" ]]; then ok "absent: ${1#"${T}"/}"; else bad "should be absent: ${1#"${T}"/}"; fi; }

assert_contains() {
  local file="$1" needle="$2" label="$3"
  if [[ -f "${file}" ]] && grep -Fq "${needle}" "${file}"; then ok "contains ${label}"; else bad "missing ${label} in ${file#"${T}"/}"; fi
}

assert_count() {
  local file="$1" pattern="$2" expected="$3" label="$4" actual
  actual="$(grep -cE "${pattern}" "${file}" 2>/dev/null || true)"
  actual="${actual:-0}"
  if [[ "${actual}" == "${expected}" ]]; then ok "count ${label}: ${actual}"; else bad "expected ${expected} ${label}, got ${actual} in ${file#"${T}"/}"; fi
}

cap() { "${CAPTURE}" --target "${T}" "$@" >/dev/null 2>&1; }

# ---------------------------------------------------------------------------
echo "== Test 1: indexes + per-session entry created, areas recorded =="
T="${WORK}/idx"; mkdir -p "${T}"
cap --work-id FEAT-001-alpha --phase code --summary "First" --areas "src/billing, com.acme.billing"
assert_file "$(mem session-index.md)"
assert_file "$(mem code-area-index.md)"
assert_contains "$(mem session-index.md)" "| Areas |" "session-index Areas column"
assert_contains "$(mem session-index.md)" "FEAT-001-alpha" "session-index work row"
# Two declared areas -> two reverse-index rows for one session.
assert_count "$(mem code-area-index.md)" '^\| (src/billing|com\.acme\.billing) \|' 2 "code-area rows for 2 areas"
entry_file="$(ls "$(mem sessions)"/*.md 2>/dev/null | head -n 1)"
assert_file "${entry_file}"
assert_contains "${entry_file}" "Code areas: src/billing, com.acme.billing" "per-session areas line"

# ---------------------------------------------------------------------------
echo "== Test 2: newest-first ordering in session-index =="
T="${WORK}/order"; mkdir -p "${T}"
cap --work-id FEAT-010-old --phase plan --summary "Older session"
sleep 1
cap --work-id FEAT-011-new --phase plan --summary "Newer session"
first_row="$(grep -E '^\| 20' "$(mem session-index.md)" | head -n 1)"
if grep -q "FEAT-011-new" <<<"${first_row}"; then ok "newest session is first row"; else bad "newest session not first: ${first_row}"; fi

# ---------------------------------------------------------------------------
echo "== Test 3: code-area index enables cross-work retrieval by area =="
T="${WORK}/area"; mkdir -p "${T}"
cap --work-id FEAT-020-one --phase code --summary "Touches shared area" --areas "scripts/sdlc-spdd"
sleep 1
cap --work-id BUG-021-two --phase code --summary "Also touches it" --areas "scripts/sdlc-spdd"
# Both unrelated work items are discoverable under the same area.
matches="$(grep -cE '^\| scripts/sdlc-spdd \|' "$(mem code-area-index.md)" || true)"
if [[ "${matches}" == "2" ]]; then ok "area lookup returns both work items"; else bad "expected 2 area rows, got ${matches}"; fi
assert_contains "$(mem code-area-index.md)" "FEAT-020-one" "first work in area"
assert_contains "$(mem code-area-index.md)" "BUG-021-two" "second work in area"

# ---------------------------------------------------------------------------
echo "== Test 4: --areas dedupe (comma + space) =="
T="${WORK}/dedupe"; mkdir -p "${T}"
cap --work-id FEAT-030-dup --phase code --summary "Dup areas" --areas "src/x, src/x src/y"
assert_count "$(mem code-area-index.md)" '^\| src/x \|' 1 "deduped src/x rows"
assert_count "$(mem code-area-index.md)" '^\| src/y \|' 1 "src/y row"

# ---------------------------------------------------------------------------
echo "== Test 5: history rotation bounds the recent window =="
T="${WORK}/rotate"; mkdir -p "${T}"
for i in 1 2 3 4; do cap --work-id FEAT-040-rot --phase code --summary "entry ${i}" --history-limit 2; sleep 1; done
assert_count "$(mem session-history.md)" '^### ' 2 "inline entries kept (limit 2)"
assert_file "$(mem archive/session-history.md)"
assert_count "$(mem archive/session-history.md)" '^### ' 2 "archived entries (4 captured - 2 kept)"

# ---------------------------------------------------------------------------
echo "== Test 6: --no-history-rotate keeps append-only, no archive =="
T="${WORK}/norotate"; mkdir -p "${T}"
for i in 1 2 3; do cap --work-id FEAT-050-keep --phase code --summary "k${i}" --history-limit 1 --no-history-rotate; sleep 1; done
assert_count "$(mem session-history.md)" '^### ' 3 "all entries kept inline"
assert_absent "$(mem archive/session-history.md)"

# ---------------------------------------------------------------------------
echo "== Test 7: --dry-run writes nothing =="
T="${WORK}/dry"; mkdir -p "${T}"
"${CAPTURE}" --target "${T}" --work-id FEAT-060-dry --phase code --summary "no write" --areas "src/z" --dry-run >/dev/null 2>&1
assert_absent "$(mem session-index.md)"
assert_absent "$(mem code-area-index.md)"
assert_absent "$(mem sessions)"

# ---------------------------------------------------------------------------
echo "== Test 8: start-agent-session brief bootstraps the framework =="
T="${WORK}/brief"; mkdir -p "${T}"
"${START}" --target "${T}" --work-id FEAT-070-brief --phase plan >/dev/null 2>&1
current="${T}/agent-context/sessions/current-session.md"
assert_file "${current}"
assert_contains "${current}" "## Framework Orientation" "Framework Orientation section"
assert_contains "${current}" "loaded on every request" "always-on grounding pointer"
assert_contains "${current}" "context-loading-and-scaling.md" "context-loading doc pointer"
# The reverted canvas-file-parsing section must not reappear.
if grep -Fq "Initial Files To Create" "${current}"; then bad "reverted 'Initial Files To Create' section present"; else ok "no canvas file-list section in brief"; fi

# ---------------------------------------------------------------------------
echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Session memory index regression tests FAILED." >&2
  exit 1
fi
echo "All session memory index regression tests passed."
