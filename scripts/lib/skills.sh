#!/usr/bin/env bash
# harness/skills helpers: frontmatter parsing and legacy layout migration.

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

# Map legacy extension agent folder → phases column for migration.
_skills_agent_folder_phases() {
  case "${1:-}" in
    _all-agents) printf '%s' "*" ;;
    initializer-agent) printf '%s' "init" ;;
    planning-agent) printf '%s' "analysis, plan, prompt-update" ;;
    architect-agent) printf '%s' "architect" ;;
    coding-agent) printf '%s' "code, api-test" ;;
    codereview-agent) printf '%s' "review" ;;
    retro-agent) printf '%s' "retro" ;;
    curator-agent) printf '%s' "sync" ;;
    *) printf '%s' "" ;;
  esac
}

# Map legacy playbook basename → skill name and phases.
_skills_playbook_meta() {
  local base="$1"
  base="${base%.md}"
  base="${base%-playbook}"
  case "${base}" in
    session-handoff) printf '%s\t%s' "SKIP" "" ;;
    java-feature) printf '%s\t%s' "java-feature" "code" ;;
    pr-review) printf '%s\t%s' "pr-review" "review" ;;
    bugfix|refactor) printf '%s\t%s' "${base}" "code" ;;
    *) printf '%s\t%s' "${base}" "code" ;;
  esac
}

_skills_prepend_frontmatter() {
  local dest="$1"
  local skill_name="$2"
  local phases="$3"
  local aliases="${4:-}"
  local body="$5"
  {
    echo "---"
    echo "skill: ${skill_name}"
    [[ -n "${aliases}" ]] && echo "aliases: ${aliases}"
    [[ -n "${phases}" ]] && echo "phases: ${phases}"
    echo "---"
    echo ""
    printf '%s' "${body}"
    [[ "${body}" == *$'\n' ]] || echo
  } > "${dest}"
}

# Idempotent: playbooks/ + extensions/ → harness/skills/; drop manifest machinery.
migrate_playbooks_extensions_to_skills() {
  local target="$1"
  local dry_run="${2:-0}"
  local home skills_dir playbooks_dir extensions_dir
  home="$(sdlc_home "${target}")"
  skills_dir="$(sdlc_skills_dir "${target}")"
  playbooks_dir=""
  extensions_dir=""
  if [[ -d "${home}/playbooks" ]]; then
    playbooks_dir="${home}/playbooks"
  elif [[ -d "${home}/agent-context/playbooks" ]]; then
    playbooks_dir="${home}/agent-context/playbooks"
  fi
  if [[ -d "${home}/extensions" ]]; then
    extensions_dir="${home}/extensions"
  elif [[ -d "${home}/agent-context/extensions" ]]; then
    extensions_dir="${home}/agent-context/extensions"
  fi

  if [[ "${dry_run}" -eq 1 ]]; then
    echo "[dry-run] would ensure ${skills_dir}"
  else
    mkdir -p "${skills_dir}"
  fi

  local f base skill phases aliases body dest agent_dir agent_phases
  shopt -s nullglob

  if [[ -n "${playbooks_dir}" && -d "${playbooks_dir}" ]]; then
    for f in "${playbooks_dir}"/*.md; do
      base="$(basename "${f}")"
      IFS=$'\t' read -r skill phases <<< "$(_skills_playbook_meta "${base}")"
      [[ "${skill}" == "SKIP" ]] && continue
      dest="${skills_dir}/${skill}.md"
      if [[ -f "${dest}" ]]; then
        continue
      fi
      body="$(<"${f}")"
      if [[ "${skill}" == "java-feature" ]]; then
        aliases="java"
      else
        aliases=""
      fi
      if [[ "${dry_run}" -eq 1 ]]; then
        echo "[dry-run] would migrate playbook ${f} -> ${dest}"
      else
        _skills_prepend_frontmatter "${dest}" "${skill}" "${phases}" "${aliases}" "${body}"
      fi
    done
  fi

  if [[ -n "${extensions_dir}" && -d "${extensions_dir}" ]]; then
    for f in "${extensions_dir}"/skills/*.md; do
      [[ -f "${f}" ]] || continue
      base="$(basename "${f}" .md)"
      dest="${skills_dir}/${base}.md"
      [[ -f "${dest}" ]] && continue
      body="$(<"${f}")"
      if [[ "${dry_run}" -eq 1 ]]; then
        echo "[dry-run] would migrate extension skill ${f} -> ${dest}"
      else
        if [[ "${body}" == ---* ]]; then
          cp "${f}" "${dest}"
        else
          _skills_prepend_frontmatter "${dest}" "${base}" "" "" "${body}"
        fi
      fi
    done

    for agent_dir in "${extensions_dir}"/*-agent "${extensions_dir}/_all-agents"; do
      [[ -d "${agent_dir}" ]] || continue
      agent_phases="$(_skills_agent_folder_phases "$(basename "${agent_dir}")")"
      [[ -n "${agent_phases}" ]] || continue
      for f in "${agent_dir}"/*.md; do
        [[ -f "${f}" ]] || continue
        base="$(basename "${f}" .md)"
        case "${base}" in
          README|manifest|example-manifest-extension) continue ;;
        esac
        dest="${skills_dir}/${base}.md"
        [[ -f "${dest}" ]] && continue
        body="$(<"${f}")"
        if [[ "${dry_run}" -eq 1 ]]; then
          echo "[dry-run] would migrate extension ${f} -> ${dest} (phases: ${agent_phases})"
        else
          _skills_prepend_frontmatter "${dest}" "${base}" "${agent_phases}" "" "${body}"
        fi
      done
    done
  fi

  shopt -u nullglob

  # Move phase-index beside harness core files when still under memory/.
  local harness_dir phase_src phase_dest
  harness_dir="$(sdlc_harness_dir "${target}")"
  phase_dest="${harness_dir}/phase-index.md"
  for phase_src in \
    "${home}/agent-context/memory/phase-index.md" \
    "${home}/memory/phase-index.md"; do
    [[ -f "${phase_src}" && ! -f "${phase_dest}" ]] || continue
    if [[ "${dry_run}" -eq 1 ]]; then
      echo "[dry-run] would move ${phase_src} -> ${phase_dest}"
    else
      mkdir -p "${harness_dir}"
      cp "${phase_src}" "${phase_dest}"
    fi
  done

  if [[ -n "${extensions_dir}" && -d "${extensions_dir}" ]]; then
    if [[ "${dry_run}" -eq 1 ]]; then
      echo "[dry-run] would remove legacy extensions tree ${extensions_dir}"
    else
      rm -rf "${extensions_dir}"
    fi
  fi
  if [[ -n "${playbooks_dir}" && -d "${playbooks_dir}" ]]; then
    if [[ "${dry_run}" -eq 1 ]]; then
      echo "[dry-run] would remove legacy playbooks tree ${playbooks_dir}"
    else
      rm -rf "${playbooks_dir}"
    fi
  fi
}
