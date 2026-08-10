#!/usr/bin/env bash
# Code-area and analysis-section parsing helpers.

normalize_token() {
  local t="$1"
  t="$(printf '%s' "${t}" | tr '[:upper:]' '[:lower:]')"
  t="${t#"${t%%[![:space:]]*}"}"
  t="${t%"${t##*[![:space:]]}"}"
  t="${t%%[.,;:)]}"
  t="${t##[.,;(]}"
  printf '%s' "${t}"
}

normalize_area() {
  local a="$1"
  a="$(printf '%s' "${a}" | tr '[:upper:]' '[:lower:]')"
  a="${a#"${a%%[![:space:]]*}"}"
  a="${a%"${a##*[![:space:]]}"}"
  a="$(printf '%s' "${a}" | tr -s '/')"
  a="${a%/}"
  printf '%s' "${a}"
}

parse_section_bullets() {
  local file="$1"
  local section="$2"
  [[ -f "${file}" ]] || return 0
  awk -v section="${section}" '
    BEGIN { in_section = 0 }
    $0 ~ "^##[[:space:]]+" section "[[:space:]]*$" { in_section = 1; next }
    in_section && /^## / { exit }
    in_section && /^-[[:space:]]+/ {
      line = $0
      sub(/^-[[:space:]]+/, "", line)
      sub(/[[:space:]]+\(.+\)$/, "", line)
      gsub(/`/, "", line)
      if (length(line) > 0) print line
    }
  ' "${file}"
}
