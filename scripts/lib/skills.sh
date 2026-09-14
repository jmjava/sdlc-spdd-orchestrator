#!/usr/bin/env bash
# harness/skills helpers: frontmatter parsing and phase/name matching.

_SKILLS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! declare -f sdlc_home >/dev/null 2>&1; then
  # shellcheck source=/dev/null
  source "${_SKILLS_LIB_DIR}/paths.sh"
fi

# Emit one line per skill file: name<TAB>aliases<TAB>phases<TAB>path
_skills_list_meta() {
  local skills_dir="$1"
  [[ -d "${skills_dir}" ]] || return 0
  SKILLS_DIR="${skills_dir}" python3 - <<'PY'
import os
from pathlib import Path

skills_dir = Path(os.environ["SKILLS_DIR"])

def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip()
    return meta

for path in sorted(skills_dir.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    name = meta.get("skill") or path.stem
    aliases = meta.get("aliases", "")
    phases = meta.get("phases", "")
    print(f"{name}\x1f{aliases}\x1f{phases}\x1f{path}")
PY
}

skill_phases_match() {
  local phases_col="$1"
  local phase="$2"
  phases_col="${phases_col#"${phases_col%%[![:space:]]*}"}"
  phases_col="${phases_col%"${phases_col##*[![:space:]]}"}"
  [[ -z "${phases_col}" ]] && return 1
  [[ "${phases_col}" == "*" ]] && return 0
  local part
  IFS=',' read -ra parts <<< "${phases_col}"
  for part in "${parts[@]}"; do
    part="${part#"${part%%[![:space:]]*}"}"
    part="${part%"${part##*[![:space:]]}"}"
    if [[ "${part}" == */* ]]; then
      local sub
      IFS='/' read -ra subs <<< "${part}"
      for sub in "${subs[@]}"; do
        sub="${sub#"${sub%%[![:space:]]*}"}"
        sub="${sub%"${sub##*[![:space:]]}"}"
        [[ "${sub}" == "${phase}" ]] && return 0
      done
    elif [[ "${part}" == "${phase}" ]]; then
      return 0
    fi
  done
  return 1
}

skill_name_matches() {
  local name="$1"
  local aliases="$2"
  local token="$3"
  [[ "${name}" == "${token}" ]] && return 0
  [[ "$(printf '%s' "${name}" | tr '[:upper:]' '[:lower:]')" == "$(printf '%s' "${token}" | tr '[:upper:]' '[:lower:]')" ]] && return 0
  [[ -z "${aliases}" ]] && return 1
  local part
  IFS=',' read -ra parts <<< "${aliases}"
  for part in "${parts[@]}"; do
    part="${part#"${part%%[![:space:]]*}"}"
    part="${part%"${part##*[![:space:]]}"}"
    [[ "${part}" == "${token}" ]] && return 0
    [[ "$(printf '%s' "${part}" | tr '[:upper:]' '[:lower:]')" == "$(printf '%s' "${token}" | tr '[:upper:]' '[:lower:]')" ]] && return 0
  done
  return 1
}
