#!/usr/bin/env bash
# Path and lib-sourcing helpers for SDLC-SPDD scripts (storage v3).

# Lib files copied into installed targets (scripts/sdlc-spdd/lib/).
SDLC_SHIPPED_LIB_FILES=(
  common.sh
  paths.sh
  areas.sh
  work-id.sh
  milestone.sh
  context-index.sh
  readiness.sh
)

# Orchestrator-only libs (never installed into targets).
SDLC_ORCHESTRATOR_ONLY_LIB_FILES=(
  shipped-docs-boundary.sh
  framework-install.sh
)

# Source a lib file from ${caller_dir}/lib/<name>.sh; fail loud if missing.
sdlc_require_lib() {
  local lib_name="$1"
  local caller_dir
  caller_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
  local lib_path="${caller_dir}/lib/${lib_name}.sh"
  if [[ ! -f "${lib_path}" ]]; then
    echo "Error: missing shared library ${lib_path}" >&2
    echo "Re-run init-project.sh or upgrade-project.sh to install scripts/sdlc-spdd/lib/." >&2
    exit 1
  fi
  # shellcheck source=/dev/null
  source "${lib_path}"
}

# --- storage v3 path resolution (no side effects) ---

# Git toplevel or pwd.
sdlc_root() {
  local root="${1:-}"
  if [[ -z "${root}" && -n "${SDLC_ROOT:-}" ]]; then
    root="${SDLC_ROOT}"
  fi
  if [[ -n "${root}" ]]; then
    printf '%s' "${root}"
    return 0
  fi
  git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null || pwd
}

# Framework home: SDLC_HOME > <root>/sdlc-spdd if dir > root.
sdlc_home() {
  local root="${1:-$(sdlc_root)}"
  if [[ -n "${SDLC_HOME:-}" ]]; then
    printf '%s' "${SDLC_HOME}"
    return 0
  fi
  if [[ -d "${root}/sdlc-spdd" ]]; then
    printf '%s' "${root}/sdlc-spdd"
  else
    printf '%s' "${root}"
  fi
}

sdlc_runtime_dir() {
  printf '%s' "$(sdlc_home "$1")/.sdlc"
}

sdlc_ledger() {
  printf '%s' "$(sdlc_home "$1")/spdd/memory/lessons.jsonl"
}

sdlc_stage() {
  printf '%s' "$(sdlc_runtime_dir "$1")/staged/lessons.jsonl"
}

sdlc_registry() {
  printf '%s' "$(sdlc_home "$1")/spdd/memory/registry.jsonl"
}

sdlc_spdd_dir() {
  printf '%s' "$(sdlc_home "$1")/spdd"
}

sdlc_requirements_dir() {
  printf '%s' "$(sdlc_home "$1")/requirements"
}

sdlc_harness_dir() {
  local home
  home="$(sdlc_home "$1")"
  if [[ -d "${home}/harness" ]]; then
    printf '%s' "${home}/harness"
  else
    printf '%s' "${home}/agent-context/harness"
  fi
}

sdlc_sessions_dir() {
  printf '%s' "$(sdlc_runtime_dir "$1")/sessions"
}

sdlc_extensions_dir() {
  local home
  home="$(sdlc_home "$1")"
  if [[ -d "${home}/extensions" ]]; then
    printf '%s' "${home}/extensions"
  else
    printf '%s' "${home}/agent-context/extensions"
  fi
}

sdlc_playbooks_dir() {
  local home
  home="$(sdlc_home "$1")"
  if [[ -d "${home}/playbooks" ]]; then
    printf '%s' "${home}/playbooks"
  else
    printf '%s' "${home}/agent-context/playbooks"
  fi
}

# JSON string escape via python3 (preferred over jq).
sdlc_json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()), end="")' <<<"$1"
}

# Append one JSONL line (mkdir -p parent dir).
sdlc_append_jsonl() {
  local file="$1"
  local json="$2"
  mkdir -p "$(dirname "${file}")"
  printf '%s\n' "${json}" >> "${file}"
}

# Short git HEAD for lesson commit field.
sdlc_git_head_short() {
  local root="${1:-$(sdlc_root)}"
  git -C "${root}" rev-parse --short HEAD 2>/dev/null || true
}

# Lesson id: kind:work_id:area_or_(none):source
sdlc_lesson_id() {
  local kind="$1" work_id="$2" area="$3" source="$4"
  local area_part="${area:-(none)}"
  [[ -n "${area_part}" ]] || area_part="(none)"
  local src="${source:-capture}"
  [[ -n "${src}" ]] || src="capture"
  printf '%s:%s:%s:%s' "${kind}" "${work_id}" "${area_part}" "${src}"
}

# Build a lesson JSON object via python3 (handles escaping).
sdlc_build_lesson_json() {
  local kind="$1" work_id="$2" area="$3" phase="$4" ts="$5" title="$6" body="$7" source="$8"
  local keywords_csv="${9:-}"
  local commit="${10:-}"
  local root="${11:-$(sdlc_root)}"
  KIND="${kind}" WORK_ID="${work_id}" AREA="${area}" PHASE="${phase}" TS="${ts}" \
  TITLE="${title}" BODY="${body}" SOURCE="${source}" KEYWORDS_CSV="${keywords_csv}" \
  COMMIT="${commit:-$(sdlc_git_head_short "${root}")}" \
  python3 - <<'PY'
import json, os
kind = os.environ["KIND"]
work_id = os.environ["WORK_ID"]
area = os.environ.get("AREA", "").strip()
phase = os.environ.get("PHASE", "")
ts = os.environ.get("TS", "")
title = os.environ.get("TITLE", "")
body = os.environ.get("BODY", "")
source = os.environ.get("SOURCE", "capture") or "capture"
commit = os.environ.get("COMMIT", "")
kw_csv = os.environ.get("KEYWORDS_CSV", "")
keywords = [k.strip() for k in kw_csv.split(",") if k.strip()]
area_part = area or "(none)"
rec_id = f"{kind}:{work_id}:{area_part}:{source}"
if not title and body:
    title = body.strip().splitlines()[0][:120]
print(json.dumps({
    "id": rec_id,
    "kind": kind,
    "work_id": work_id,
    "area": area,
    "phase": phase,
    "ts": ts,
    "title": title,
    "body": body,
    "source": source,
    "keywords": keywords,
    "commit": commit,
    "schema": 1,
}, ensure_ascii=False))
PY
}
