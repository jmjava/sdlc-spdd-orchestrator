#!/usr/bin/env bash
# EXPERIMENTAL: full Guide + Neo4j live stack smoke test.
#
# Brings up embabel-neo4j from jmjava/orch-guide, starts Guide (append-ingest, no
# startup corpus ingest by default), loads SPDD NamedEntity projection, probes
# MCP SSE, then tears Guide down.
#
# Opt-in (local or CI):
#   SDLC_GUIDE_STACK_LIVE=1 ./tests/test-guide-stack-live.sh
#
# Env:
#   GUIDE_HOME              path to orch-guide clone (default: ../orch-guide, ../guide, or ~/github/jmjava/orch-guide)
#   GUIDE_GIT_REF           branch/tag (default: sdlc-spdd-projection-v2)
#   GUIDE_PORT              default 21337
#   NEO4J_BOLT_PORT         default 7687
#   NEO4J_HTTP_PORT         default 7474
#   GUIDE_START_TIMEOUT_SEC wait for Guide TCP (default 600)
#   GUIDE_KEEP=1            leave Guide + Neo4j running after the test
#   GUIDE_WITH_INGEST=1     allow startup RAG ingest (slow; off by default)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh" 2>/dev/null || true

if [[ "${SDLC_GUIDE_STACK_LIVE:-}" != "1" && "${CI:-}" != "true" ]]; then
  echo "SKIP: set SDLC_GUIDE_STACK_LIVE=1 to run the experimental Guide+Neo4j stack test"
  exit 0
fi

# In CI we always run when this workflow is invoked; locally require the flag.
if [[ "${CI:-}" == "true" && "${SDLC_GUIDE_STACK_LIVE:-}" == "0" ]]; then
  echo "SKIP: SDLC_GUIDE_STACK_LIVE=0"
  exit 0
fi

GUIDE_PORT="${GUIDE_PORT:-21337}"
NEO4J_BOLT_PORT="${NEO4J_BOLT_PORT:-7687}"
NEO4J_HTTP_PORT="${NEO4J_HTTP_PORT:-7474}"
NEO4J_HTTPS_PORT="${NEO4J_HTTPS_PORT:-7473}"
GUIDE_PROFILE="${GUIDE_PROFILE:-sdlc-spdd}"
GUIDE_GIT_REF="${GUIDE_GIT_REF:-sdlc-spdd-projection-v2}"
GUIDE_START_TIMEOUT_SEC="${GUIDE_START_TIMEOUT_SEC:-600}"
SPRING_PROFILES_ACTIVE="${SPRING_PROFILES_ACTIVE:-neo4j,local,${GUIDE_PROFILE}}"

guide_log_path() {
  printf '/tmp/sdlc-guide-%s-%s.log\n' "${GUIDE_PROFILE}" "${GUIDE_PORT}"
}
GUIDE_LOG="$(guide_log_path)"

resolve_guide_home() {
  if [[ -n "${GUIDE_HOME:-}" ]]; then
    echo "${GUIDE_HOME}"
    return
  fi
  for candidate in \
    "${ROOT}/../orch-guide" \
    "${HOME}/github/jmjava/orch-guide" \
    "${ROOT}/../guide" \
    "${HOME}/github/jmjava/guide"
  do
    if [[ -d "${candidate}/.git" ]]; then
      echo "$(cd "${candidate}" && pwd)"
      return
    fi
  done
  echo ""
}

GUIDE_HOME="$(resolve_guide_home)"
if [[ -z "${GUIDE_HOME}" || ! -d "${GUIDE_HOME}" ]]; then
  echo "FAIL: GUIDE_HOME not found (clone jmjava/orch-guide or set GUIDE_HOME)" >&2
  exit 1
fi
if [[ ! -f "${GUIDE_HOME}/scripts/append-ingest.sh" ]]; then
  echo "FAIL: ${GUIDE_HOME} does not look like orch-guide" >&2
  exit 1
fi

# shellcheck source=scripts/lib/test-preflight.sh
source "${ROOT}/scripts/lib/test-preflight.sh"
test_preflight_warn_stale_jobs || true
if test_preflight_guide_health "${GUIDE_PORT}"; then
  if [[ "${SDLC_GUIDE_FORCE_BOOT:-}" != "1" ]]; then
    echo "Guide already healthy on :${GUIDE_PORT} — skipping boot (SDLC_GUIDE_FORCE_BOOT=1 to restart)"
    SKIP_GUIDE_BOOT=1
  fi
fi
if pgrep -f "append-ingest\.sh" >/dev/null 2>&1 && ! test_preflight_guide_health "${GUIDE_PORT}"; then
  echo "FAIL: append-ingest still running but Guide not healthy — wait or: pkill -f append-ingest.sh" >&2
  echo "  tail -20 ${GUIDE_LOG}" >&2
  exit 1
fi

echo "== experimental Guide+Neo4j stack =="
echo "  orchestrator: ${ROOT}"
echo "  GUIDE_HOME:   ${GUIDE_HOME}"
echo "  GUIDE_REF:    ${GUIDE_GIT_REF}"
echo "  GUIDE_PORT:   ${GUIDE_PORT}"
echo "  profiles:     ${SPRING_PROFILES_ACTIVE}"

command -v docker >/dev/null || { echo "FAIL: docker required" >&2; exit 1; }

# Prefer Python 3.12 (.venv first).
# shellcheck source=scripts/lib/python.sh
source "${ROOT}/scripts/lib/python.sh"
if ! resolve_engine_python; then
  exit 1
fi
PYTHON_BIN="${SDLC_PY}"

export PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:$PYTHONPATH}"
if ! "${PYTHON_BIN}" -c "import flask" >/dev/null 2>&1; then
  echo "Installing Flask for ${PYTHON_BIN} (experimental guide stack)..."
  "${PYTHON_BIN}" -m pip install -q 'flask>=3,<4'
fi
if ! "${PYTHON_BIN}" -c "import flask, sdlc_engine" >/dev/null 2>&1; then
  echo "FAIL: cannot import flask + sdlc_engine with ${PYTHON_BIN} (PYTHONPATH=${PYTHONPATH})" >&2
  exit 1
fi
echo "Using ${PYTHON_BIN} ($("${PYTHON_BIN}" -c 'import sys; print(sys.version.split()[0])'))"

if [[ "${SKIP_GUIDE_BOOT:-}" == "1" ]]; then
  echo "== skip boot (Guide already up) =="
else
# Write Embabel-aligned profile + start via console APIs.
"${PYTHON_BIN}" <<PY
from pathlib import Path
from sdlc_engine.installer.app import create_app
from sdlc_engine.installer.guide import save_config

root = Path(${ROOT@Q})
guide = Path(${GUIDE_HOME@Q})
cfg = save_config(root, {
    "guide_home": str(guide),
    "guide_git_url": "https://github.com/jmjava/orch-guide.git",
    "guide_git_ref": ${GUIDE_GIT_REF@Q},
    "profile": ${GUIDE_PROFILE@Q},
    "spring_profiles": ${SPRING_PROFILES_ACTIVE@Q},
    "host": "127.0.0.1",
    "port": int(${GUIDE_PORT}),
    "neo4j_bolt_port": int(${NEO4J_BOLT_PORT}),
    "neo4j_http_port": int(${NEO4J_HTTP_PORT}),
    "neo4j_https_port": int(${NEO4J_HTTPS_PORT}),
})
app = create_app(root)
c = app.test_client()

def must_ok(label, res):
    body = res.get_json() or {}
    print(label, res.status_code, "ok=", body.get("ok"))
    if not body.get("ok") and res.status_code >= 400:
        print(body)
        raise SystemExit(f"{label} failed")
    return body

no_pull = os.environ.get("CI") == "true"
must_ok("ensure", c.post("/api/guide/ensure", json={
    "target": str(root),
    "guide_home": str(guide),
    "guide_git_ref": ${GUIDE_GIT_REF@Q},
    "save_first": True,
    "no_pull": no_pull,
}))
must_ok("profile", c.post("/api/guide/ensure-profile", json={
    "target": str(root),
    "profile": ${GUIDE_PROFILE@Q},
}))
must_ok("neo4j", c.post("/api/guide/neo4j/start", json={"target": str(root)}))
import os
no_ingest = os.environ.get("GUIDE_WITH_INGEST", "") != "1"
body = must_ok("guide-start", c.post("/api/guide/start", json={
    "target": str(root),
    "no_ingest": no_ingest,
    "skip_neo4j": True,
}))
print("guide pid", (body.get("result") or {}).get("pid"))
print("guide log", (body.get("result") or {}).get("log_path"))
print("no_ingest", no_ingest)
PY

echo "== waiting for Guide health on :${GUIDE_PORT} (timeout ${GUIDE_START_TIMEOUT_SEC}s) =="
echo "  log: ${GUIDE_LOG}"
elapsed=0
while (( elapsed < GUIDE_START_TIMEOUT_SEC )); do
  if test_preflight_guide_health "${GUIDE_PORT}"; then
    echo "Guide healthy after ${elapsed}s"
    break
  fi
  sleep 5
  elapsed=$((elapsed + 5))
  if pgrep -f "append-ingest\.sh" >/dev/null 2>&1 && (( elapsed % 60 == 0 )); then
    echo "  … append-ingest still running (${elapsed}s) — first boot can take 30–90+ min"
    tail -3 "${GUIDE_LOG}" 2>/dev/null || true
  elif (( elapsed % 30 == 0 )); then
    echo "  … ${elapsed}s (probe: curl -sf --max-time 3 http://127.0.0.1:${GUIDE_PORT}/actuator/health)"
  fi
done
if (( elapsed >= GUIDE_START_TIMEOUT_SEC )); then
  echo "FAIL: Guide did not become healthy on :${GUIDE_PORT}" >&2
  echo "  Do NOT curl /sse — it hangs. Use /actuator/health with --max-time 3." >&2
  tail -20 "${GUIDE_LOG}" 2>/dev/null || true
  "${PYTHON_BIN}" <<PY
from pathlib import Path
from sdlc_engine.installer.app import create_app
app = create_app(Path(${ROOT@Q}))
print(app.test_client().post("/api/guide/stop", json={"target": ${ROOT@Q}}).get_json())
PY
  exit 1
fi
fi

"${PYTHON_BIN}" <<PY
from pathlib import Path
from sdlc_engine.installer.app import create_app

root = Path(${ROOT@Q})
app = create_app(root)
c = app.test_client()
status = c.post("/api/guide", json={"target": str(root)}).get_json() or {}
print("probe", status.get("probe"))
print("neo4j", status.get("neo4j"))
print("mcp", status.get("mcp"))
mech = {m["id"]: m["ok"] for m in status.get("embabel_mechanics") or []}
print("mechanics", mech)
for key in ("profiles", "neo4j", "named_entity", "mcp_sse"):
    if key in mech and not mech[key]:
        raise SystemExit(f"Embabel mechanics failed: {key}")

# Storage v3: orchestrator dogfood spdd/canvas/ is often empty; use example fixture.
proj_root = root / "examples" / "spring-boot-order-api"
if not proj_root.is_dir():
    raise SystemExit(f"missing Guide projection fixture: {proj_root}")
print("projection root", proj_root)
proj = c.post(
    "/api/guide/projection/load",
    json={"target": str(root), "root_path": str(proj_root)},
).get_json() or {}
print("projection", proj.get("ok"), (proj.get("result") or {}).get("status"))
if not proj.get("ok"):
    # Projection may 409 if flag off — treat as hard fail for this experimental gate.
    print(proj)
    raise SystemExit("NamedEntity projection load failed")

stats = (proj.get("projection") or {}).get("data") or (proj.get("result") or {}).get("data") or {}
print("projection stats", stats)
work = int(stats.get("workIdCount") or stats.get("workIds") or 0)
if work < 1:
    raise SystemExit(
        f"expected workIdCount >= 1 after projection from {proj_root}, got {work}"
    )

print("PASS: experimental Guide+Neo4j stack (Neo4j up, Guide up, NamedEntity projection loaded)")
PY

_run_pytest() {
  local marker="$1"
  shift
  local extra_env=("$@")
  if [[ -x "${ROOT}/.venv/bin/pytest" ]]; then
    env "${extra_env[@]}" "${ROOT}/.venv/bin/pytest" -q "$@"
  else
    env "${extra_env[@]}" PYTHONPATH="${ROOT}/engine/src${PYTHONPATH:+:${PYTHONPATH}}" \
      "${PYTHON_BIN}" -m pytest -q "$@"
  fi
}

if [[ "${SDLC_GUIDE_INTEGRATION:-1}" != "0" ]]; then
  echo "== Guide live tests (engine/tests_e2e/) =="
  _run_pytest guide_integration \
    GUIDE_BASE_URL="http://127.0.0.1:${GUIDE_PORT}" \
    "${ROOT}/engine/tests_e2e/test_guide_projection_roundtrip.py" \
    "${ROOT}/engine/tests_e2e/test_context_store_guide_live.py" \
    "${ROOT}/engine/tests_e2e/test_guide_repo_present.py"
fi

if [[ "${SDLC_GUIDE_E2E:-1}" != "0" ]]; then
  echo "== ops console Playwright (live Guide probe) =="
  if ! "${PYTHON_BIN}" -c "import playwright" >/dev/null 2>&1; then
    echo "Installing Playwright e2e extras for ${PYTHON_BIN}..."
    "${PYTHON_BIN}" -m pip install -q -e "${ROOT}/engine[dev,viewer-e2e]"
    "${PYTHON_BIN}" -m playwright install --with-deps chromium
  fi
  _run_pytest guide_e2e \
    GUIDE_PORT="${GUIDE_PORT}" \
    GUIDE_BASE_URL="http://127.0.0.1:${GUIDE_PORT}" \
    "${ROOT}/engine/tests_e2e/test_console_guide_live.py" \
    --screenshot=only-on-failure
fi

if [[ "${GUIDE_KEEP:-}" == "1" ]]; then
  echo "GUIDE_KEEP=1 — leaving Guide and Neo4j running"
  exit 0
fi

"${PYTHON_BIN}" <<PY
from pathlib import Path
from sdlc_engine.installer.app import create_app
root = Path(${ROOT@Q})
c = create_app(root).test_client()
print("stop guide", c.post("/api/guide/stop", json={"target": str(root)}).get_json())
# Keep Neo4j by default in CI caches; stop unless GUIDE_STOP_NEO4J=1
import os
if os.environ.get("GUIDE_STOP_NEO4J") == "1":
    print("stop neo4j", c.post("/api/guide/neo4j/stop", json={"target": str(root)}).get_json())
PY

echo "DONE"
