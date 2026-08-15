#!/usr/bin/env bash
# Fast checks before long test runs — fail in seconds, not after a hung curl or 600s wait.
#
# Sourced by run-test-suites.sh and test-guide-stack-live.sh.

test_preflight_guide_health() {
  local port="${1:-${GUIDE_PORT:-21337}}"
  curl -sf --max-time 3 "http://127.0.0.1:${port}/actuator/health" >/dev/null 2>&1
}

test_preflight_guide_tcp() {
  local port="${1:-${GUIDE_PORT:-21337}}"
  python3 - <<PY 2>/dev/null
import socket, sys
s = socket.socket()
s.settimeout(1.0)
try:
    s.connect(("127.0.0.1", int("${port}")))
    sys.exit(0)
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
}

test_preflight_warn_stale_jobs() {
  local found=0
  if pgrep -f "pytest.*engine/tests[^_]" >/dev/null 2>&1; then
    echo "preflight WARN: pytest still running against removed path engine/tests/ (kill it)" >&2
    pgrep -af "pytest.*engine/tests[^_]" >&2 || true
    found=1
  fi
  if pgrep -f "curl.*21337/sse" >/dev/null 2>&1; then
    echo "preflight WARN: hung curl on /sse (use /actuator/health with --max-time 3)" >&2
    found=1
  fi
  if pgrep -f "append-ingest\.sh" >/dev/null 2>&1; then
    echo "preflight WARN: append-ingest.sh still running — first boot can take 30–90+ min" >&2
    pgrep -af "append-ingest\.sh" | head -3 >&2 || true
    echo "  tail -f /tmp/sdlc-guide-21337.log  # or GUIDE_INGEST_LOG" >&2
    found=1
  fi
  if pgrep -f "pytest.*tests_unit|pytest.*tests_integration|pytest.*tests_e2e" >/dev/null 2>&1; then
    echo "preflight WARN: another pytest suite run is in progress" >&2
    pgrep -af "pytest.*tests_" | head -5 >&2 || true
    found=1
  fi
  return "${found}"
}

test_preflight_kill_stale() {
  pkill -f "curl.*21337/sse" 2>/dev/null || true
  pkill -f "pytest.*engine/tests[^_]" 2>/dev/null || true
  echo "preflight: killed stale curl /sse and pytest engine/tests (if any)"
}

test_preflight_python() {
  local py="${1:?python binary}"
  local minor
  minor="$("${py}" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null)" || {
    echo "preflight FAIL: cannot run ${py}" >&2
    return 1
  }
  if (( minor != 12 )); then
    echo "preflight FAIL: ${py} is 3.${minor} — engine requires Python 3.12" >&2
    echo "  sudo apt install python3.12 python3.12-venv && ./scripts/setup-engine-venv.sh --e2e" >&2
    return 1
  fi
  echo "preflight OK: ${py} ($("${py}" -c 'import sys; print(sys.version.split()[0])'))"
}

test_preflight_suite_layout() {
  local root="${1:?repo root}"
  for dir in tests_unit tests_integration tests_e2e; do
    if [[ ! -d "${root}/engine/${dir}" ]]; then
      echo "preflight FAIL: missing engine/${dir}/" >&2
      return 1
    fi
  done
  if [[ -d "${root}/engine/tests" ]]; then
    echo "preflight WARN: legacy engine/tests/ still present — use tests_unit|integration|e2e" >&2
  fi
}

test_preflight_gh_e2e() {
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo "preflight OK: gh authenticated (GitHub e2e will run)"
    return 0
  fi
  if [[ -n "${GH_TOKEN:-}${GITHUB_TOKEN:-}" ]]; then
    echo "preflight OK: GH_TOKEN set (GitHub e2e will run)"
    return 0
  fi
  echo "preflight WARN: no gh auth / GH_TOKEN — tests_e2e/test_issues_github_integration.py will FAIL" >&2
  return 0
}

test_preflight_playwright() {
  local py="${1:?python}"
  if ! "${py}" -c "import playwright" >/dev/null 2>&1; then
    echo "preflight WARN: playwright not installed — e2e will pip install + chromium (~1–3 min)" >&2
    return 0
  fi
  if ! "${py}" -m playwright install --dry-run chromium 2>/dev/null | grep -q "is already installed"; then
    echo "preflight WARN: chromium may need install (playwright install chromium)" >&2
  else
    echo "preflight OK: playwright + chromium present"
  fi
}

# orch-guide KSP resolves com.embabel.agent:embabel-agent-api SNAPSHOT here.
# GitHub-hosted runners often cannot connect (TCP timeout). Live Guide boot
# then dies with BUILD FAILURE; skip instead of waiting GUIDE_START_TIMEOUT_SEC.
EMBABEL_SNAPSHOT_REPO_URL="${EMBABEL_SNAPSHOT_REPO_URL:-https://repo.embabel.com/artifactory/libs-snapshot/}"

test_preflight_embabel_snapshot_repo() {
  local url="${1:-${EMBABEL_SNAPSHOT_REPO_URL}}"
  local timeout="${2:-15}"
  curl -fsS --max-time "${timeout}" -o /dev/null "${url}" >/dev/null 2>&1
}

test_preflight_guide_stack() {
  local port="${GUIDE_PORT:-21337}"
  if test_preflight_guide_health "${port}"; then
    echo "preflight OK: Guide healthy on :${port} (skip boot with SDLC_GUIDE_ALREADY_UP=1)"
    return 0
  fi
  if test_preflight_guide_tcp "${port}"; then
    echo "preflight WARN: port :${port} open but /actuator/health failed — Spring still starting or stuck ingest" >&2
    return 1
  fi
  if pgrep -f "append-ingest\.sh" >/dev/null 2>&1; then
    echo "preflight FAIL: append-ingest in progress but Guide not healthy yet — wait or kill stale ingest" >&2
    return 1
  fi
  echo "preflight OK: Guide not up — test-guide-stack-live.sh will boot stack"
}

test_preflight_print() {
  local suite="${1:-all}"
  cat <<EOF
preflight: suite=${suite}
  unit         ~2–4 min   engine/tests_unit
  integration  ~3–6 min   engine/tests_integration (+ installer cov)
  e2e          ~5–15 min  Playwright + gh (no Guide)
  e2e --guide  ~20–90 min Guide boot + tests_e2e (first ingest is slow)
Probe Guide:  curl -sf --max-time 3 http://127.0.0.1:21337/actuator/health
Do NOT use:    curl http://127.0.0.1:21337/sse  (hangs forever)
Fix loop:     ./scripts/run-test-suites.sh unit --lf
              ./scripts/run-test-suites.sh unit -- path::test_name
Resume CI:    ./scripts/run-test-suites.sh all --from integration
EOF
}

# Per-suite pass markers at current git HEAD (.sdlc/test-suite-state.tsv, gitignored).
test_suite_state_file() {
  echo "${1:?root}/.sdlc/test-suite-state.tsv"
}

test_suite_state_head() {
  git -C "${1:?root}" rev-parse HEAD 2>/dev/null || echo "unknown"
}

test_suite_state_mark() {
  local root="$1" suite="$2"
  local dir="${root}/.sdlc" file head line
  mkdir -p "${dir}"
  file="$(test_suite_state_file "${root}")"
  head="$(test_suite_state_head "${root}")"
  {
    if [[ -f "${file}" ]]; then
      grep -v "^${suite}	" "${file}" || true
    fi
    printf '%s\t%s\t%s\n' "${suite}" "${head}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "${file}.tmp"
  mv "${file}.tmp" "${file}"
}

test_suite_state_clear() {
  local root="$1" suite="${2:-}"
  local file
  file="$(test_suite_state_file "${root}")"
  if [[ -z "${suite}" ]]; then
    rm -f "${file}"
    return 0
  fi
  [[ -f "${file}" ]] || return 0
  grep -v "^${suite}	" "${file}" > "${file}.tmp" 2>/dev/null || true
  mv "${file}.tmp" "${file}"
}

test_suite_state_is_current() {
  local root="$1" suite="$2"
  local file head line
  file="$(test_suite_state_file "${root}")"
  [[ -f "${file}" ]] || return 1
  head="$(test_suite_state_head "${root}")"
  line="$(grep "^${suite}	" "${file}" 2>/dev/null | tail -1)" || return 1
  [[ "${line}" == "${suite}	${head}"* ]]
}

# Exit 0 = run suite; 1 = skip (already green at HEAD).
test_suite_state_should_run() {
  local root="$1" suite="$2" force="${3:-0}"
  if [[ "${force}" == "1" ]]; then
    return 0
  fi
  if test_suite_state_is_current "${root}" "${suite}"; then
    return 1
  fi
  return 0
}

test_suite_state_print() {
  local root="$1"
  local file
  file="$(test_suite_state_file "${root}")"
  if [[ ! -f "${file}" ]]; then
    echo "suite state: (none — run each suite once at this commit)"
    return 0
  fi
  echo "suite state at HEAD $(test_suite_state_head "${root}"):"
  while IFS=$'\t' read -r suite head ts; do
    if test_suite_state_is_current "${root}" "${suite}"; then
      echo "  ${suite}: green (${ts})"
    else
      echo "  ${suite}: stale (recorded ${head})"
    fi
  done < "${file}"
}
