#!/usr/bin/env bash
# Extensive unit/edge tests for scripts/lib shared helpers (FEAT-001 + FEAT-005).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB="${REPO_ROOT}/scripts/lib"

pass=0
fail=0

ok()  { echo "  ok   $1"; pass=$((pass + 1)); }
bad() { echo "  FAIL $1" >&2; fail=$((fail + 1)); }

assert_eq() {
  local got="$1" want="$2" label="$3"
  if [[ "${got}" == "${want}" ]]; then ok "${label}"; else bad "${label} (got '${got}', want '${want}')"; fi
}

assert_match() {
  local got="$1" re="$2" label="$3"
  if [[ "${got}" =~ ${re} ]]; then ok "${label}"; else bad "${label} (got '${got}', want ~/${re}/)"; fi
}

assert_true() {
  local label="$1"
  shift
  if "$@"; then ok "${label}"; else bad "${label}"; fi
}

assert_false() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then bad "${label}"; else ok "${label}"; fi
}

assert_contains() {
  local hay="$1" needle="$2" label="$3"
  if grep -Fq -- "${needle}" <<< "${hay}"; then ok "${label}"; else bad "${label} (missing '${needle}')"; fi
}

# shellcheck source=/dev/null
source "${LIB}/common.sh"
# shellcheck source=/dev/null
source "${LIB}/areas.sh"
# shellcheck source=/dev/null
source "${LIB}/work-id.sh"
# shellcheck source=/dev/null
source "${LIB}/milestone.sh"
# shellcheck source=/dev/null
source "${LIB}/readiness.sh"
# shellcheck source=/dev/null
source "${LIB}/paths.sh"
# shellcheck source=/dev/null
source "${LIB}/shipped-docs-boundary.sh"
# shellcheck source=/dev/null
source "${LIB}/framework-install.sh"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

# ---------------------------------------------------------------------------
echo "== common.sh: timestamps =="
assert_match "$(sdlc_timestamp_iso)" '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$' \
  "timestamp_iso format"
assert_match "$(sdlc_timestamp_file)" '^[0-9]{8}T[0-9]{6}Z$' "timestamp_file format"
assert_match "$(sdlc_timestamp_day)" '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' "timestamp_day format"

echo "== common.sh: oneline edges =="
assert_eq "$(sdlc_oneline $'hello\nworld' 20)" "hello world" "oneline collapses newlines"
assert_eq "$(sdlc_oneline 'a|b|c' 20)" "a/b/c" "oneline collapses pipes"
assert_eq "$(sdlc_oneline '  spaced  out  ' 20)" "spaced out" "oneline trims and squeezes spaces"
assert_eq "$(sdlc_oneline 'abcdefghijklmnopqrstuvwxyz' 10)" "abcdefghij..." "oneline truncates with ellipsis"
assert_eq "$(sdlc_oneline 'short' 10)" "short" "oneline no truncate when under max"
assert_eq "$(sdlc_oneline '' 10)" "" "oneline empty"
assert_eq "$(sdlc_oneline $'a\n|b' )" "a /b" "oneline default max leaves short string"

echo "== common.sh: ensure_dir / ensure_file =="
sdlc_ensure_dir "${WORK}/nest/a" 0
assert_true "ensure_dir creates path" test -d "${WORK}/nest/a"
dry_out="$(sdlc_ensure_dir "${WORK}/nest/dry" 1)"
assert_contains "${dry_out}" "[dry-run] would mkdir -p" "ensure_dir dry-run message"
assert_false "ensure_dir dry-run does not create" test -d "${WORK}/nest/dry"

sdlc_ensure_file "${WORK}/nest/a/note.md" "Hello Title" 0
assert_true "ensure_file creates file" test -f "${WORK}/nest/a/note.md"
assert_eq "$(head -n1 "${WORK}/nest/a/note.md")" "# Hello Title" "ensure_file writes title"
# idempotent when present
printf 'keep\n' > "${WORK}/nest/a/note.md"
sdlc_ensure_file "${WORK}/nest/a/note.md" "Other" 0
# Command substitution strips a final newline; content must remain "keep".
assert_eq "$(cat "${WORK}/nest/a/note.md")" "keep" "ensure_file leaves existing file"
dry_out="$(sdlc_ensure_file "${WORK}/nest/missing.md" "X" 1)"
assert_contains "${dry_out}" "[dry-run] would create" "ensure_file dry-run"
assert_false "ensure_file dry-run does not create" test -f "${WORK}/nest/missing.md"

echo "== common.sh: resolve_target / die / unknown_option =="
mkdir -p "${WORK}/tgt"
resolved="$(sdlc_resolve_target "${WORK}/tgt")"
assert_eq "${resolved}" "$(cd "${WORK}/tgt" && pwd)" "resolve_target absolute"
if ( sdlc_resolve_target "${WORK}/no-such-dir" ) >/dev/null 2>&1; then
  bad "resolve_target should fail for missing dir"
else
  ok "resolve_target fails for missing dir"
fi
usage_stub() { echo "USAGE"; }
if out="$( ( sdlc_die "boom" 7 ) 2>&1 )" ; then
  bad "sdlc_die should exit non-zero"
else
  rc=$?
  assert_eq "${rc}" "7" "sdlc_die exit code"
  assert_eq "${out}" "boom" "sdlc_die message"
fi
if out="$( ( sdlc_unknown_option --bogus usage_stub ) 2>&1 )" ; then
  bad "unknown_option should exit"
else
  assert_contains "${out}" "Unknown option: --bogus" "unknown_option message"
  assert_contains "${out}" "USAGE" "unknown_option calls usage"
fi

# ---------------------------------------------------------------------------
echo "== areas.sh edges =="
assert_eq "$(normalize_area '  Src/Billing/  ')" "src/billing" "normalize_area trims and lowercases"
assert_eq "$(normalize_area 'a///b//c/')" "a/b/c" "normalize_area squeezes slashes"
assert_eq "$(normalize_area '/')" "" "normalize_area lone slash → empty"
assert_eq "$(normalize_area '')" "" "normalize_area empty"
assert_eq "$(normalize_token ' Billing. ')" "billing" "normalize_token strips punctuation"
assert_eq "$(normalize_token 'Foo.')" "foo" "normalize_token strips trailing punct"
assert_eq "$(normalize_token '(Foo)')" "foo" "normalize_token strips matching wrap"
assert_eq "$(normalize_token '(Foo).')" "foo)" "normalize_token one-pass: trailing then leading"
assert_eq "$(normalize_token '(Foo);')" "foo)" "normalize_token one-pass leaves inner paren"
assert_eq "$(normalize_token '  ')" "" "normalize_token whitespace-only"

cat > "${WORK}/sample.md" <<'MD'
## Code Areas

- com.acme.billing
- `src/foo`
- path/with (annotation)
-   

## Other

- ignored
MD
mapfile -t bullets < <(parse_section_bullets "${WORK}/sample.md" "Code Areas")
assert_eq "${#bullets[@]}" "3" "parse_section_bullets count"
assert_eq "${bullets[0]}" "com.acme.billing" "parse_section_bullets first"
assert_eq "${bullets[1]}" "src/foo" "parse_section_bullets strips backticks"
assert_eq "${bullets[2]}" "path/with" "parse_section_bullets strips (annotation)"
mapfile -t none < <(parse_section_bullets "${WORK}/missing-file.md" "Code Areas")
assert_eq "${#none[@]}" "0" "parse_section_bullets missing file → empty"
mapfile -t other < <(parse_section_bullets "${WORK}/sample.md" "Missing Section")
assert_eq "${#other[@]}" "0" "parse_section_bullets missing section → empty"

# ---------------------------------------------------------------------------
echo "== work-id.sh: slugify edges =="
assert_eq "$(slugify 'FEAT Foo/Bar' strict)" "feat-foo-bar" "slugify strict slash"
assert_eq "$(slugify 'FEAT Foo Bar' legacy)" "feat-foo-bar" "slugify legacy spaces"
assert_eq "$(slugify 'Hello_World' strict)" "hello-world" "slugify strict underscore"
assert_eq "$(slugify 'Hello_World' legacy)" "hello-world" "slugify legacy underscore"
assert_eq "$(slugify '  --Ab!!C--  ' strict)" "abc" "slugify strict strips junk (no hyphen left)"
assert_eq "$(slugify 'Ab C!!' strict)" "ab-c" "slugify strict keeps word separators"
assert_eq "$(slugify 'Ab!!C' legacy)" "abc" "slugify legacy strips non-alnum"
assert_eq "$(slugify '' strict)" "" "slugify empty"
if ( slugify 'x' bogus ) >/dev/null 2>&1; then
  bad "slugify unknown mode should fail"
else
  ok "slugify unknown mode fails"
fi

echo "== work-id.sh: next_work_number edges =="
mkdir -p "${WORK}/spdd/canvas"
touch "${WORK}/spdd/canvas/FEAT-003-alpha.md"
touch "${WORK}/spdd/canvas/FEAT-005-beta.md"
touch "${WORK}/spdd/canvas/FEAT-009-z.md"
touch "${WORK}/spdd/canvas/FEAT-notanumber.md"
n="$(next_work_number FEAT "${WORK}" \
  "${WORK}/spdd/canvas/FEAT-"*.md)"
assert_eq "${n}" "10" "next_work_number max+1 across sources"
n="$(next_work_number BUG "${WORK}")"
assert_eq "${n}" "1" "next_work_number empty globs → 1"
# leading-zero numeric compare
touch "${WORK}/spdd/canvas/BUG-007-x.md" "${WORK}/spdd/canvas/BUG-08-y.md"
n="$(next_work_number BUG "${WORK}" "${WORK}/spdd/canvas/BUG-"*.md)"
assert_eq "${n}" "9" "next_work_number leading zeros"

echo "== work-id.sh: work_type_prefix matrix =="
assert_eq "$(work_type_prefix feature)" "FEAT" "prefix feature"
assert_eq "$(work_type_prefix FEAT)" "FEAT" "prefix FEAT"
assert_eq "$(work_type_prefix bugfix)" "BUG" "prefix bugfix"
assert_eq "$(work_type_prefix Bug)" "BUG" "prefix Bug"
assert_eq "$(work_type_prefix refactor)" "REF" "prefix refactor"
assert_eq "$(work_type_prefix ref)" "REF" "prefix ref"
assert_eq "$(work_type_prefix spike)" "SPIKE" "prefix spike"
assert_eq "$(work_type_prefix doc)" "DOC" "prefix doc"
assert_eq "$(work_type_prefix test)" "TEST" "prefix test"
assert_eq "$(work_type_prefix chore)" "CHORE" "prefix chore"
assert_eq "$(work_type_prefix weird)" "FEAT" "prefix unknown → FEAT"

# ---------------------------------------------------------------------------
echo "== milestone.sh: list / prefer / dual layout =="
M="${WORK}/ms"
mkdir -p "${M}"
echo 'FEAT-099-demo' > "${M}/milestone-1.md"
abs="$(resolve_milestone "${M}" FEAT-099-demo "" absolute)"
rel="$(resolve_milestone "${M}" FEAT-099-demo "" relative)"
assert_eq "${abs}" "${M}/milestone-1.md" "resolve_milestone absolute root"
assert_eq "${rel}" "milestone-1.md" "resolve_milestone relative root"

mkdir -p "${M}/requirements/milestones/milestone-1"
echo 'FEAT-099-demo' > "${M}/requirements/milestones/milestone-1/MILESTONE-1.md"
warn="$(resolve_milestone "${M}" FEAT-099-demo "" absolute 2>&1 >/dev/null || true)"
# list emits warning when both exist; resolve uses list
list_warn="$(list_milestone_files "${M}" relative 2>&1 >/dev/null || true)"
assert_contains "${list_warn}" "preferring subdirectory" "list_milestone_files warns on dual layout"
abs="$(resolve_milestone "${M}" FEAT-099-demo "" absolute 2>/dev/null)"
assert_eq "${abs}" "${M}/requirements/milestones/milestone-1/MILESTONE-1.md" \
  "resolve_milestone prefers subdirectory"

# README.md as subdirectory definition
mkdir -p "${M}/requirements/milestones/milestone-2"
echo 'FEAT-200-readme' > "${M}/requirements/milestones/milestone-2/README.md"
abs="$(resolve_milestone "${M}" FEAT-200-readme "" absolute 2>/dev/null)"
assert_eq "${abs}" "${M}/requirements/milestones/milestone-2/README.md" \
  "resolve_milestone finds README definition"

# explicit candidate path
cand="$(resolve_milestone "${M}" "" "milestone-1.md" relative 2>/dev/null || true)"
# with dual layout, candidate milestone-1.md exists at root
assert_eq "${cand}" "milestone-1.md" "resolve_milestone explicit root candidate"
# Bare milestone-1 resolves to existing root milestone-1.md before number lookup.
cand="$(resolve_milestone "${M}" "" "milestone-1" absolute 2>/dev/null)"
assert_eq "${cand}" "${M}/milestone-1.md" \
  "resolve_milestone bare name hits existing root .md first"
# Number lookup prefers subdirectory when the root .md is absent.
mkdir -p "${M}/requirements/milestones/milestone-3"
echo 'FEAT-303' > "${M}/requirements/milestones/milestone-3/MILESTONE-3.md"
cand="$(resolve_milestone "${M}" "" "milestone-3" absolute 2>/dev/null)"
assert_eq "${cand}" "${M}/requirements/milestones/milestone-3/MILESTONE-3.md" \
  "resolve_milestone bare name → subdir when root .md absent"

# missing work id / missing milestone
if resolve_milestone "${M}" FEAT-DOES-NOT-EXIST "" absolute >/dev/null 2>&1; then
  bad "resolve_milestone missing work id should fail"
else
  ok "resolve_milestone missing work id fails"
fi
if resolve_milestone "${M}" "" "nope.md" absolute >/dev/null 2>&1; then
  bad "resolve_milestone missing candidate should fail"
else
  ok "resolve_milestone missing candidate fails"
fi

req_dir="$(requirement_dir_for_milestone "${M}" "${abs}")"
# abs is README for m2 from earlier overwrite - re-resolve m1
m1="$(resolve_milestone "${M}" FEAT-099-demo "" absolute 2>/dev/null)"
req_dir="$(requirement_dir_for_milestone "${M}" "${m1}")"
assert_eq "${req_dir}" "${M}/requirements/milestones/milestone-1" \
  "requirement_dir_for_milestone nested"

printf '# req\n' > "${M}/requirements/milestones/milestone-1/FEAT-099-demo.md"
printf '# flat\n' > "${M}/requirements/milestones/FEAT-099-demo.md"
req_rel="$(resolve_requirement_path "${M}" FEAT-099-demo relative 2>/dev/null)"
assert_eq "${req_rel}" "requirements/milestones/milestone-1/FEAT-099-demo.md" \
  "resolve_requirement_path prefers nested"
req_warn="$(resolve_requirement_path "${M}" FEAT-099-demo relative 2>&1 >/dev/null || true)"
assert_contains "${req_warn}" "preferring subdirectory" "resolve_requirement_path warns on dual"

# flat-only
printf '# only\n' > "${M}/requirements/milestones/FEAT-300-flat.md"
req_rel="$(resolve_requirement_path "${M}" FEAT-300-flat relative)"
assert_eq "${req_rel}" "requirements/milestones/FEAT-300-flat.md" "resolve_requirement_path flat"

# root milestone → flat req dir when no subdir exists for that number
echo 'FEAT-400-root' > "${M}/milestone-9.md"
req_dir="$(requirement_dir_for_milestone "${M}" "${M}/milestone-9.md")"
assert_eq "${req_dir}" "${M}/requirements/milestones" \
  "requirement_dir_for_milestone root → flat when no subdir"

assert_true "has_any_milestone true" has_any_milestone "${M}"
empty_ms="$(mktemp -d)"
assert_false "has_any_milestone false" has_any_milestone "${empty_ms}"
rmdir "${empty_ms}"

# number helpers
assert_eq "$(_milestone_number_from_path "${M}/milestone-12.md")" "12" "number from root file"
assert_eq "$(_milestone_number_from_path "${M}/requirements/milestones/milestone-3/README.md")" "3" \
  "number from subdir path"
assert_true "subdir definition detect" _is_subdir_milestone_definition \
  "${M}/requirements/milestones/milestone-1/MILESTONE-1.md"
assert_false "root not subdir definition" _is_subdir_milestone_definition "${M}/milestone-1.md"

# ---------------------------------------------------------------------------
echo "== paths.sh manifest + sdlc_require_lib =="
assert_true "paths lists readiness.sh" \
  bash -c 'printf "%s\n" "$@" | grep -qx readiness.sh' -- "${SDLC_SHIPPED_LIB_FILES[@]}"
assert_true "paths has >=6 shipped libs" test "${#SDLC_SHIPPED_LIB_FILES[@]}" -ge 6
assert_true "orchestrator-only includes boundary" \
  bash -c 'printf "%s\n" "$@" | grep -qx shipped-docs-boundary.sh' -- "${SDLC_ORCHESTRATOR_ONLY_LIB_FILES[@]}"
assert_true "orchestrator-only includes framework-install" \
  bash -c 'printf "%s\n" "$@" | grep -qx framework-install.sh' -- "${SDLC_ORCHESTRATOR_ONLY_LIB_FILES[@]}"

# sdlc_require_lib: success via stub that lives next to a lib/ copy
stub_root="${WORK}/require-ok"
mkdir -p "${stub_root}/lib" "${stub_root}/bin"
cp "${LIB}/common.sh" "${stub_root}/lib/common.sh"
cat > "${stub_root}/bin/caller.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/../lib/paths.sh"
# Override: sdlc_require_lib uses BASH_SOURCE[1] dirname/lib — place paths in bin/../lib via symlink layout
# Re-implement call using copied paths.sh which looks at caller_dir/lib.
# Our layout: bin/caller.sh → lib is sibling of bin → need lib under bin/lib
EOF
# Fix layout: caller in scripts/, lib under scripts/lib/
rm -rf "${stub_root}"
mkdir -p "${WORK}/require-ok/scripts/lib"
cp "${LIB}/paths.sh" "${WORK}/require-ok/scripts/lib/paths.sh"
cp "${LIB}/common.sh" "${WORK}/require-ok/scripts/lib/common.sh"
cat > "${WORK}/require-ok/scripts/caller.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"
sdlc_require_lib common
# prove common loaded
sdlc_oneline "a" 1 >/dev/null
echo LOADED
EOF
chmod +x "${WORK}/require-ok/scripts/caller.sh"
out="$("${WORK}/require-ok/scripts/caller.sh")"
assert_eq "${out}" "LOADED" "sdlc_require_lib sources sibling lib"

mkdir -p "${WORK}/require-bad/scripts/lib"
cp "${LIB}/paths.sh" "${WORK}/require-bad/scripts/lib/paths.sh"
cat > "${WORK}/require-bad/scripts/caller.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"
sdlc_require_lib missing-lib
EOF
chmod +x "${WORK}/require-bad/scripts/caller.sh"
if err="$("${WORK}/require-bad/scripts/caller.sh" 2>&1)"; then
  bad "sdlc_require_lib should fail when missing"
else
  assert_contains "${err}" "missing shared library" "sdlc_require_lib error text"
fi

# ---------------------------------------------------------------------------
echo "== readiness.sh: normalize matrix =="
assert_eq "$(normalize_readiness 'Ready For Coding')" "ready-for-coding" "normalize Ready For Coding"
assert_eq "$(normalize_readiness 'Needs Redesign')" "needs-redesign" "normalize Needs Redesign"
assert_eq "$(normalize_readiness 'Needs Analysis')" "needs-analysis" "normalize Needs Analysis"
assert_eq "$(normalize_readiness 'Needs Clarification')" "needs-clarification" "normalize Needs Clarification"
assert_eq "$(normalize_readiness 'Blocked')" "blocked" "normalize Blocked"
assert_eq "$(normalize_readiness 'Reviewed — Approved With Notes')" "reviewed" "normalize Reviewed em dash"
assert_eq "$(normalize_readiness 'Ready For Coding (note)')" "ready-for-coding" "normalize parenthetical"
assert_eq "$(normalize_readiness 'ready_for_coding')" "ready-for-coding" "normalize underscores"
assert_eq "$(normalize_readiness 'complete')" "complete" "normalize complete"
assert_eq "$(normalize_readiness 'Done')" "complete" "normalize Done alias"
assert_eq "$(normalize_readiness 'COMPLETED')" "complete" "normalize COMPLETED"
assert_eq "$(normalize_readiness 'complete-shipped')" "complete" "normalize complete-* prefix"
assert_eq "$(normalize_readiness 'need-analysis')" "needs-analysis" "normalize need-analysis alias"
assert_eq "$(normalize_readiness 'ready-for-code')" "ready-for-coding" "normalize ready-for-code alias"
assert_eq "$(normalize_readiness 'ready-for-coding-extra')" "ready-for-coding" "normalize ready-for-coding-*"
assert_eq "$(normalize_readiness 'reviewed-approved')" "reviewed" "normalize reviewed-*"
assert_eq "$(normalize_readiness '  Blocked  ')" "blocked" "normalize trims"
assert_eq "$(normalize_readiness '')" "" "normalize empty"
assert_eq "$(normalize_readiness 'not-a-real-value')" "" "unknown normalizes empty"
assert_eq "$(normalize_readiness 'almost-ready')" "" "near-miss unknown → empty"

echo "== readiness.sh: allows_coding =="
assert_true "allows coding when ready" readiness_allows_coding "ready-for-coding"
assert_true "allows coding when absent" readiness_allows_coding ""
assert_true "allows coding when reviewed" readiness_allows_coding "reviewed"
assert_true "allows coding when complete" readiness_allows_coding "complete"
assert_false "blocks coding when needs-analysis" readiness_allows_coding "needs-analysis"
assert_false "blocks coding when needs-clarification" readiness_allows_coding "needs-clarification"
assert_false "blocks coding when needs-redesign" readiness_allows_coding "needs-redesign"
assert_false "blocks coding when blocked" readiness_allows_coding "blocked"
assert_false "blocks coding when garbage" readiness_allows_coding "garbage"

echo "== readiness.sh: extract / canvas edges =="
rtmp="${WORK}/readiness"
mkdir -p "${rtmp}"
cat > "${rtmp}/meta.md" <<'EOF'
# Canvas
## Metadata
- Work ID: FEAT-R
- Readiness: Needs Clarification
EOF
assert_eq "$(extract_readiness_raw "${rtmp}/meta.md")" "Needs Clarification" "extract Metadata Readiness"
assert_eq "$(canvas_readiness "${rtmp}/meta.md")" "needs-clarification" "canvas_readiness Metadata"

cat > "${rtmp}/yaml.md" <<'EOF'
---
readiness: ready-for-coding
work_id: FEAT-Y
---
# Canvas
## Metadata
- Work ID: FEAT-Y
- Readiness: Blocked
EOF
# YAML wins over Metadata when present
assert_eq "$(extract_readiness_raw "${rtmp}/yaml.md")" "ready-for-coding" "extract YAML readiness wins"
assert_eq "$(canvas_readiness "${rtmp}/yaml.md")" "ready-for-coding" "canvas_readiness YAML wins"

cat > "${rtmp}/yaml-quoted.md" <<'EOF'
---
readiness: "Needs Analysis"
---
# Canvas
EOF
assert_eq "$(extract_readiness_raw "${rtmp}/yaml-quoted.md")" "Needs Analysis" "extract YAML quoted"
assert_eq "$(canvas_readiness "${rtmp}/yaml-quoted.md")" "needs-analysis" "canvas_readiness quoted YAML"

cat > "${rtmp}/case.md" <<'EOF'
# Canvas
## Metadata
- readiness: blocked
EOF
assert_eq "$(extract_readiness_raw "${rtmp}/case.md")" "blocked" "extract lowercase readiness key"

cat > "${rtmp}/none.md" <<'EOF'
# Canvas
## Metadata
- Work ID: FEAT-N
EOF
assert_eq "$(extract_readiness_raw "${rtmp}/none.md")" "" "extract absent readiness"
assert_eq "$(canvas_readiness "${rtmp}/none.md")" "" "canvas_readiness absent"
assert_eq "$(canvas_readiness "${rtmp}/missing.md")" "" "canvas_readiness missing file"

cat > "${rtmp}/unknown.md" <<'EOF'
# Canvas
## Metadata
- Readiness: Almost Ready Maybe
EOF
assert_eq "$(canvas_readiness "${rtmp}/unknown.md")" "" "canvas_readiness unknown → empty"

# Canonical list present
assert_true "READINESS_CANONICAL non-empty" test "${#READINESS_CANONICAL[@]}" -ge 7
assert_contains "$(printf '%s\n' "${READINESS_CANONICAL[@]}")" "ready-for-coding" \
  "canonical includes ready-for-coding"

# ---------------------------------------------------------------------------
echo "== shipped-docs-boundary.sh =="
assert_true "README.md is orchestrator-only" is_orchestrator_only_doc "docs/README.md"
assert_true "contributing-command-specs.md is orchestrator-only" \
  is_orchestrator_only_doc "docs/contributing-command-specs.md"
assert_true "contributing-skills.md is orchestrator-only" \
  is_orchestrator_only_doc "docs/contributing-skills.md"
assert_true "mcp-guide-for-agents.md is orchestrator-only" \
  is_orchestrator_only_doc "docs/mcp-guide-for-agents.md"
assert_true "dice-projection-runbook.md is orchestrator-only" \
  is_orchestrator_only_doc "docs/dice-projection-runbook.md"
assert_false "session-prompt-standard ships" is_orchestrator_only_doc "docs/session-prompt-standard.md"
assert_false "daily-runbook ships" is_orchestrator_only_doc "docs/daily-runbook.md"

pushd "${REPO_ROOT}" >/dev/null
shipped=()
collect_shipped_doc_paths shipped
popd >/dev/null
assert_true "collect_shipped_doc_paths non-empty" test "${#shipped[@]}" -gt 0
# must not include orchestrator-only basenames
leak=0
for p in "${shipped[@]}"; do
  if is_orchestrator_only_doc "${p}"; then
    leak=1
    bad "shipped list leaked orchestrator-only: ${p}"
  fi
done
if [[ "${leak}" -eq 0 ]]; then ok "shipped list excludes orchestrator-only docs"; fi
found_session=0
for p in "${shipped[@]}"; do
  [[ "$(basename "${p}")" == "session-prompt-standard.md" ]] && found_session=1
done
assert_eq "${found_session}" "1" "shipped list includes session-prompt-standard.md"

# ---------------------------------------------------------------------------
echo "== test-preflight.sh: Embabel snapshot repo =="
# shellcheck source=/dev/null
source "${LIB}/test-preflight.sh"
assert_match "${EMBABEL_SNAPSHOT_REPO_URL}" 'repo\.embabel\.com' \
  "default Embabel snapshot URL"
assert_false "unreachable host fails Embabel preflight" \
  test_preflight_embabel_snapshot_repo "http://127.0.0.1:1/" 1

# ---------------------------------------------------------------------------
echo "== framework-install.sh =="
fw="${WORK}/fw"
framework_ensure_dir "${fw}/a/b" 0
assert_true "framework_ensure_dir creates" test -d "${fw}/a/b"
fw_dry="$(framework_ensure_dir "${fw}/c" 1)"
assert_contains "${fw_dry}" "[dry-run] would mkdir -p" "framework_ensure_dir dry-run"
assert_false "framework_ensure_dir dry-run skips create" test -d "${fw}/c"

# ---------------------------------------------------------------------------
echo "== python.sh: 3.12 resolver skips broken shims =="
# shellcheck source=/dev/null
source "${LIB}/python.sh"
assert_eq "$(PYTHON=/opt/custom/python3.12 pick_bootstrap_python)" \
  "/opt/custom/python3.12" "pick_bootstrap_python honors PYTHON"
shim="${WORK}/broken-python3.12"
cat > "${shim}" <<'EOF'
#!/bin/sh
echo "pyenv: version '3.12' not installed" >&2
exit 127
EOF
chmod +x "${shim}"
assert_false "broken pyenv-style shim is not usable 3.12" _python_is_usable_312 "${shim}"
if command -v python3.12 >/dev/null 2>&1 && _python_is_usable_312 python3.12; then
  assert_true "real python3.12 is usable" _python_is_usable_312 python3.12
else
  ok "skip live python3.12 usable check (none on PATH)"
fi

# ---------------------------------------------------------------------------
echo "== verify-script-lib-duplicates.sh =="
if "${REPO_ROOT}/scripts/verify-script-lib-duplicates.sh" >/dev/null; then
  ok "no stray lib helper duplicates in scripts/"
else
  bad "verify-script-lib-duplicates reported issues"
fi


echo
echo "Summary: ${pass} passed, ${fail} failed"
if (( fail > 0 )); then exit 1; fi
