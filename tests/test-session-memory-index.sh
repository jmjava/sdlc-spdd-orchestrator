#!/usr/bin/env bash
set -euo pipefail

# Regression harness for capture-session-memory.sh memory indexing + rotation.
#
# Covers the relevance-based retrieval model:
#   - per-session entry files under agent-context/memory/sessions/
#   - newest-first session-index.md (with Areas column)
#   - context-index.md (session, decision, pitfall, pattern kinds by area)
#   - code-areas.md registry: session text match + --areas merge + append new
#   - --no-session-areas opt-out, canvas/brief content matching
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
assert_file "$(mem context-index.md)"
assert_contains "$(mem session-index.md)" "| Areas |" "session-index Areas column"
assert_contains "$(mem session-index.md)" "FEAT-001-alpha" "session-index work row"
# Two declared areas -> two session rows in context index.
assert_count "$(mem context-index.md)" '^\| (src/billing|com\.acme\.billing) \| session \|' 2 "context rows for 2 session areas"
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
matches="$(grep -cE '^\| scripts/sdlc-spdd \| session \|' "$(mem context-index.md)" || true)"
if [[ "${matches}" == "2" ]]; then ok "area lookup returns both work items"; else bad "expected 2 area rows, got ${matches}"; fi
assert_contains "$(mem context-index.md)" "FEAT-020-one" "first work in area"
assert_contains "$(mem context-index.md)" "BUG-021-two" "second work in area"

# ---------------------------------------------------------------------------
echo "== Test 4: --areas dedupe (comma + space) =="
T="${WORK}/dedupe"; mkdir -p "${T}"
cap --work-id FEAT-030-dup --phase code --summary "Dup areas" --areas "src/x, src/x src/y"
assert_count "$(mem context-index.md)" '^\| src/x \| session \|' 1 "deduped src/x rows"
assert_count "$(mem context-index.md)" '^\| src/y \| session \|' 1 "src/y row"

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
assert_absent "$(mem context-index.md)"
assert_absent "$(mem sessions)"

# ---------------------------------------------------------------------------
echo "== Test 8: start-agent-session brief bootstraps the framework (hot .sdlc/sessions) =="
T="${WORK}/brief"; mkdir -p "${T}"
"${START}" --target "${T}" --work-id FEAT-070-brief --phase plan >/dev/null 2>&1
current="${T}/.sdlc/sessions/current-session.md"
assert_file "${current}"
assert_contains "${current}" "## Framework Orientation" "Framework Orientation section"
assert_contains "${current}" "loaded on every request" "always-on grounding pointer"
assert_contains "${current}" "context-loading-and-scaling.md" "context-loading doc pointer"
assert_contains "${current}" "context-index.md" "context index pointer in brief"
assert_contains "${current}" "code-areas.md" "code areas registry pointer in brief"
assert_contains "${current}" ".sdlc/sessions/current-session.md" "hot session resume path"
# Must not write new hot brief into legacy sessions path as current-session.
if [[ -f "${T}/agent-context/sessions/current-session.md" ]] \
  && grep -Fq "## Framework Orientation" "${T}/agent-context/sessions/current-session.md"; then
  bad "wrote new brief into legacy agent-context/sessions/current-session.md"
else
  ok "no new legacy current-session brief"
fi
# The reverted canvas-file-parsing section must not reappear.
if grep -Fq "Initial Files To Create" "${current}"; then bad "reverted 'Initial Files To Create' section present"; else ok "no canvas file-list section in brief"; fi

# ---------------------------------------------------------------------------
echo "== Test 9: session text matches known categories from registry =="
T="${WORK}/sess-match"; mkdir -p "${T}/agent-context/memory"
cat > "$(mem code-areas.md)" <<'REG'
# Code Areas

- src/billing
- scripts/sdlc-spdd
REG
cap --work-id FEAT-080-match --phase code --summary "Fixed handler under src/billing today"
entry_file="$(ls "$(mem sessions)"/*.md 2>/dev/null | head -n 1)"
assert_contains "${entry_file}" "Code areas: src/billing" "session matched registry category"
assert_count "$(mem context-index.md)" '^\| src/billing \| session \|' 1 "index row for session-matched area"

# ---------------------------------------------------------------------------
echo "== Test 10: --areas reuses canonical registry spelling =="
T="${WORK}/canon"; mkdir -p "${T}/agent-context/memory"
cat > "$(mem code-areas.md)" <<'REG'
# Code Areas

- scripts/sdlc-spdd
REG
cap --work-id FEAT-081-canon --phase code --summary "CLI work" --areas "Scripts/SDLC-SPDD/"
entry_file="$(ls "$(mem sessions)"/*.md 2>/dev/null | head -n 1)"
assert_contains "${entry_file}" "Code areas: scripts/sdlc-spdd" "canonical registry spelling reused"
assert_count "$(mem code-areas.md)" '^- scripts/sdlc-spdd$' 1 "no duplicate registry entry"

# ---------------------------------------------------------------------------
echo "== Test 11: new category parsed from current summary and appended to registry =="
T="${WORK}/newcat"; mkdir -p "${T}/agent-context/memory"
cap --work-id FEAT-082-new --phase code --summary "Added src/payments module"
assert_file "$(mem code-areas.md)"
assert_contains "$(mem code-areas.md)" "src/payments" "new category in registry"
# Second capture mentions same area with different casing in summary text.
cap --work-id FEAT-083-reuse --phase code --summary "More work under Src/Payments"
assert_count "$(mem code-areas.md)" '^- src/payments$' 1 "registry still has one payments entry"

# ---------------------------------------------------------------------------
echo "== Test 18: daily session notes are parsed for category extraction =="
T="${WORK}/daily-notes"; mkdir -p "${T}/agent-context/memory" "${T}/session-notes"
cat > "$(mem code-areas.md)" <<'REG'
# Code Areas

- src/billing
REG
note_day="$(date -u +"%Y-%m-%d")"
cat > "${T}/session-notes/${note_day}.md" <<'NOTE'
Earlier session today touched src/billing.
NOTE
cap --work-id FEAT-084-current --phase code --summary "Added src/payments."
entry_file="$(ls "$(mem sessions)"/*.md 2>/dev/null | head -n 1)"
assert_contains "${entry_file}" "src/payments" "punctuated path parsed from summary"
assert_count "$(mem context-index.md)" '^\| src/payments \| session \|' 1 "payments indexed from current summary"
assert_count "$(mem context-index.md)" '^\| src/billing \| session \|' 1 "daily note area indexed"

# ---------------------------------------------------------------------------
echo "== Test 19: full latest timestamped session brief is parsed for areas =="
T="${WORK}/latest-brief"; mkdir -p "${T}/agent-context/memory" "${T}/agent-context/sessions"
# A prior session brief left on disk; its body names a code area only it knows about.
cat > "${T}/agent-context/sessions/20260101T000000Z-code-FEAT-OLD.md" <<'BRIEF'
# SDLC-SPDD Agent Session

## Notes
Touched scripts/legacy-runner for the migration shim.
BRIEF
cap --work-id FEAT-085-brief --phase code --summary "Unrelated summary with no paths"
assert_contains "$(mem code-areas.md)" "scripts/legacy-runner" "area parsed from latest session brief"
assert_count "$(mem context-index.md)" '^\| scripts/legacy-runner \| session \|' 1 "latest-brief area indexed"

# ---------------------------------------------------------------------------
echo "== Test 20: Java package parsed from maven path in canvas prose =="
T="${WORK}/java-parse"; mkdir -p "${T}/spdd/canvas"
cat > "${T}/spdd/canvas/FEAT-095-java.md" <<'CAN'
Touched src/main/java/com/acme/billing/OrderService.java for billing lookup.
CAN
cap --work-id FEAT-095-java --phase code --summary "Billing lookup service"
entry_file="$(ls "$(mem sessions)"/*.md 2>/dev/null | head -n 1)"
assert_contains "${entry_file}" "com.acme.billing" "java package parsed from canvas prose"
assert_contains "$(mem code-areas.md)" "com.acme.billing" "java package in registry"

# ---------------------------------------------------------------------------
echo "== Test 12: context index includes decisions and pitfalls by area =="
T="${WORK}/ctx-kinds"; mkdir -p "${T}/agent-context/memory"
cap --work-id FEAT-090-ctx --phase architect --summary "Billing API design" \
  --areas "src/billing" \
  --decisions "Use idempotent POST for payment intents" \
  --pitfalls "Legacy orders omit tax field"
assert_count "$(mem context-index.md)" '^\| src/billing \| session \|' 1 "session kind indexed"
assert_count "$(mem context-index.md)" '^\| src/billing \| decision \|' 1 "decision kind indexed"
assert_count "$(mem context-index.md)" '^\| src/billing \| pitfall \|' 1 "pitfall kind indexed"
assert_contains "$(mem architecture-decisions.md)" "Code areas: src/billing" "areas on decision entry"
assert_contains "$(mem known-pitfalls.md)" "Code areas: src/billing" "areas on pitfall entry"

# ---------------------------------------------------------------------------
echo "== Test 13: context index includes reusable patterns by area =="
T="${WORK}/pattern"; mkdir -p "${T}/agent-context/memory"
cap --work-id FEAT-091-pattern --phase retro --summary "Extracted billing helper" \
  --areas "src/billing" \
  --patterns "Wrap payment gateway calls in a retryable adapter"
assert_count "$(mem context-index.md)" '^\| src/billing \| pattern \|' 1 "pattern kind indexed"
assert_contains "$(mem reusable-patterns.md)" "Code areas: src/billing" "areas on pattern entry"

# ---------------------------------------------------------------------------
echo "== Test 14: --no-session-areas skips text matching against registry =="
T="${WORK}/no-sess-areas"; mkdir -p "${T}/agent-context/memory"
cat > "$(mem code-areas.md)" <<'REG'
# Code Areas

- src/billing
REG
cap --work-id FEAT-092-nosa --phase code --summary "Fixed handler under src/billing" --no-session-areas
entry_file="$(ls "$(mem sessions)"/*.md 2>/dev/null | head -n 1)"
assert_contains "${entry_file}" "Code areas: none" "no session-derived areas"
assert_absent "$(mem context-index.md)"

# ---------------------------------------------------------------------------
echo "== Test 15: canvas prose contributes to session area matching =="
T="${WORK}/canvas-match"; mkdir -p "${T}/agent-context/memory" "${T}/spdd/canvas"
cat > "$(mem code-areas.md)" <<'REG'
# Code Areas

- scripts/capture-session-memory.sh
REG
cat > "${T}/spdd/canvas/FEAT-093-canvas.md" <<'CAN'
# FEAT-093

Work touches scripts/capture-session-memory.sh for session capture.
CAN
cap --work-id FEAT-093-canvas --phase code --summary "Implemented capture hook"
entry_file="$(ls "$(mem sessions)"/*.md 2>/dev/null | head -n 1)"
assert_contains "${entry_file}" "Code areas: scripts/capture-session-memory.sh" "canvas matched registry category"
assert_count "$(mem context-index.md)" '^\| scripts/capture-session-memory.sh \| session \|' 1 "canvas-driven session index row"

# ---------------------------------------------------------------------------
echo "== Test 16: memory entries without areas are not context-indexed =="
T="${WORK}/no-area-ctx"; mkdir -p "${T}/agent-context/memory"
cap --work-id FEAT-094-noarea --phase plan --summary "Planning only" \
  --decisions "Defer billing refactor" --pitfalls "None yet"
assert_file "$(mem architecture-decisions.md)"
assert_absent "$(mem context-index.md)"

# ---------------------------------------------------------------------------
echo "== Test 17: phase-index ships static context by SDLC phase =="
phase_index="${REPO_ROOT}/agent-context/memory/phase-index.md"
assert_file "${phase_index}"
assert_contains "${phase_index}" "quality-gates.md" "review phase harness entry"
assert_contains "${phase_index}" "java-feature-playbook.md" "code phase playbook entry"

# ---------------------------------------------------------------------------
echo "== Test 21: start-agent-session rotates old briefs into .sdlc/sessions/archive =="
T="${WORK}/sess-rot"; mkdir -p "${T}"
"${START}" --target "${T}" --work-id FEAT-100-a --phase plan --session-limit 2 >/dev/null 2>&1
sleep 1
"${START}" --target "${T}" --work-id FEAT-100-b --phase plan --session-limit 2 >/dev/null 2>&1
sleep 1
"${START}" --target "${T}" --work-id FEAT-100-c --phase plan --session-limit 2 >/dev/null 2>&1
sess="${T}/.sdlc/sessions"
assert_file "${sess}/current-session.md"
active_count="$(ls -1 "${sess}"/[0-9]*T*.md 2>/dev/null | wc -l | tr -d ' ')"
if [[ "${active_count}" == "2" ]]; then ok "keeps 2 timestamped briefs"; else bad "expected 2 active briefs, got ${active_count}"; fi
arch_count="$(ls -1 "${sess}/archive"/[0-9]*T*.md 2>/dev/null | wc -l | tr -d ' ')"
if [[ "${arch_count}" == "1" ]]; then ok "archived 1 older brief"; else bad "expected 1 archived brief, got ${arch_count}"; fi
"${START}" --target "${T}" --work-id FEAT-100-d --phase plan --session-limit 2 --no-session-rotate >/dev/null 2>&1
active_count="$(ls -1 "${sess}"/[0-9]*T*.md 2>/dev/null | wc -l | tr -d ' ')"
if [[ "${active_count}" -ge 3 ]]; then ok "--no-session-rotate skips archive"; else bad "expected >=3 active with --no-session-rotate, got ${active_count}"; fi

# ---------------------------------------------------------------------------
echo "== Test 22: capture metric flags write Kind: metric rows (FEAT-004 T02) =="
T="${WORK}/metrics"; mkdir -p "${T}"
cap --work-id FEAT-004-metrics --phase code --summary "With metrics" \
  --areas "scripts/capture-session-memory.sh" \
  --readiness "Ready For Coding" --review-result pass --rework 0 --context-files 8
assert_count "$(mem context-index.md)" '^\| scripts/capture-session-memory.sh \| metric \|' 1 "metric kind indexed"
assert_contains "$(mem context-index.md)" "review-result=pass" "metric entry includes review-result"
assert_contains "$(mem session-history.md)" "Metrics: readiness=" "session history records metrics"
# Omitting flags must not invent metric rows
T="${WORK}/metrics-omit"; mkdir -p "${T}"
cap --work-id FEAT-004-omit --phase code --summary "No metrics" --areas "scripts/capture-session-memory.sh"
assert_count "$(mem context-index.md)" '\| metric \|' 0 "no metric rows when flags omitted"
# Unknown review-result warns and skips that field only
T="${WORK}/metrics-bad"; mkdir -p "${T}"
out="$(${CAPTURE} --target "${T}" --work-id FEAT-004-bad --phase code --summary "Bad enum" \
  --areas "scripts/x" --review-result nope --rework 1 2>&1)" || true
if grep -q "Warning: --review-result" <<<"${out}"; then ok "unknown review-result warns"; else bad "expected warning for bad review-result"; fi
assert_contains "$(mem context-index.md)" "rework=1" "valid rework still indexed after bad review-result"
if grep -q 'review-result=nope' "$(mem context-index.md)" 2>/dev/null; then
  bad "invalid review-result should not be indexed"
else
  ok "invalid review-result skipped"
fi

# ---------------------------------------------------------------------------
echo "== Test 22b: capture auto-fills readiness from canvas when --readiness omitted =="
T="${WORK}/metrics-auto"; mkdir -p "${T}/spdd/canvas" "${T}/scripts/lib"
cp "${REPO_ROOT}/scripts/lib/"*.sh "${T}/scripts/lib/" 2>/dev/null || true
# Capture script sources lib from its own install path (orchestrator scripts/lib) —
# auto-readiness uses TARGET canvas.
cat > "${T}/spdd/canvas/FEAT-004-auto.md" <<'EOF'
# REASONS Canvas: FEAT-004-auto

## Metadata
- Work ID: FEAT-004-auto
- Readiness: Ready For Coding

## O - Operations
EOF
cap --work-id FEAT-004-auto --phase code --summary "Auto readiness" --areas "scripts/capture-session-memory.sh"
assert_contains "$(mem context-index.md)" "readiness=ready-for-coding" "auto readiness from canvas"
assert_contains "$(mem session-history.md)" "Metrics: readiness=ready-for-coding" "session history auto readiness"

# Explicit --readiness overrides canvas value
T="${WORK}/metrics-override"; mkdir -p "${T}/spdd/canvas"
cat > "${T}/spdd/canvas/FEAT-004-over.md" <<'EOF'
# REASONS Canvas
## Metadata
- Readiness: Needs Analysis
EOF
cap --work-id FEAT-004-over --phase code --summary "Override" \
  --areas "scripts/capture-session-memory.sh" --readiness "Blocked"
assert_contains "$(mem context-index.md)" "readiness=Blocked" "explicit --readiness overrides canvas"
if grep -q 'needs-analysis' "$(mem context-index.md)" 2>/dev/null; then
  bad "canvas readiness should not win over --readiness"
else
  ok "canvas value not used when --readiness set"
fi

# YAML frontmatter auto-fill + reasons-canvas.md fallback
T="${WORK}/metrics-yaml"; mkdir -p "${T}/agent-context/features/FEAT-004-yaml"
cat > "${T}/agent-context/features/FEAT-004-yaml/reasons-canvas.md" <<'EOF'
---
readiness: blocked
---
# Canvas
## Metadata
- Work ID: FEAT-004-yaml
EOF
cap --work-id FEAT-004-yaml --phase architect --summary "YAML fallback" \
  --areas "scripts/capture-session-memory.sh"
assert_contains "$(mem context-index.md)" "readiness=blocked" "auto readiness from reasons-canvas YAML"

# ---------------------------------------------------------------------------
echo "== Test 23: prompt-optimization ledger rotates like session-history (FEAT-004 T04) =="
T="${WORK}/ledger-rot"; mkdir -p "${T}/agent-context/memory"
ledger="$(mem prompt-optimization-log.md)"
{
  echo '# Prompt Optimization Log'
  echo
  echo '## Entries'
  for i in 1 2 3; do
    echo
    echo "### Entry ${i}"
    echo
    echo "- Date: 2026-07-0${i}"
    echo "- Work ID: FEAT-004-rot"
    echo "- Change: c${i}"
    echo "- Hypothesis: h${i}"
    echo "- Signal: s${i}"
    echo "- Outcome: unknown"
  done
} > "${ledger}"
cap --work-id FEAT-004-rot --phase code --summary "rotate ledger" --history-limit 2 --areas "scripts/x"
assert_count "${ledger}" '^### ' 2 "ledger keeps recent window"
assert_file "$(mem archive/prompt-optimization-log.md)"
assert_count "$(mem archive/prompt-optimization-log.md)" '^### ' 1 "older ledger entry archived"

# ---------------------------------------------------------------------------
echo "== Test lean: capture reads hot session + writes lean indexes (#85/#86) =="
T="${WORK}/lean-hot"; mkdir -p "${T}/.sdlc/sessions" "${T}/spdd/canvas"
cat > "${T}/.sdlc/sessions/current-session.md" <<'HOT'
# Hot session
Working under scripts/lib for lean capture proof.
HOT
printf '# canvas\n' > "${T}/spdd/canvas/FEAT-085-lean.md"
cap --work-id FEAT-085-lean --phase sync --summary "Hot session lean capture under scripts/lib" --areas "scripts/lib"
assert_file "${T}/spdd/memory/context-index.md"
assert_count "${T}/spdd/memory/context-index.md" '^\| scripts/lib \| session \|' 1 "lean context-index session row"
assert_file "${T}/spdd/memory/entries/progress.md"
assert_contains "${T}/spdd/memory/entries/progress.md" "FEAT-085-lean" "lean progress append"
lean_sess="$(ls "${T}/spdd/memory/sessions"/*.md 2>/dev/null | head -n 1 || true)"
if [[ -n "${lean_sess}" && -f "${lean_sess}" ]]; then ok "lean session entry exists"; else bad "missing lean session entry"; fi
assert_absent "${T}/agent-context/features"

# ---------------------------------------------------------------------------
echo
echo "Summary: ${pass} passed, ${fail} failed"
if [[ "${fail}" -gt 0 ]]; then
  echo "Session memory index regression tests FAILED." >&2
  exit 1
fi
echo "All session memory index regression tests passed."
