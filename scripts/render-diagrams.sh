#!/usr/bin/env bash
set -euo pipefail

# Render (or validate) Mermaid diagrams embedded in Markdown files.
#
# Reproducible across machines: it uses a system-installed Chrome/Chromium
# instead of downloading one, and a committed puppeteer config for the
# launch flags. Run it locally or in CI to confirm diagrams parse and to
# regenerate committed image exports for PDF/non-Mermaid renderers.

usage() {
  cat <<'EOF'
Usage: render-diagrams.sh [--out <dir>] [--format svg|png|both] [--check] [files...]

Render every ```mermaid block found in the given Markdown files to an image.

Options:
  --out <dir>       Output directory for images (default: docs/diagrams).
  --format <fmt>    Image format: both (default), svg, or png.
  --check           Validate only: render to a temp dir and discard.
                    Exit non-zero if any diagram fails to render.
  -h, --help        Show this help.

Files:
  Defaults to README.md and docs/*.md when none are given.

Browser:
  Auto-detects google-chrome / chromium. Override with PUPPETEER_EXECUTABLE_PATH.

Examples:
  ./scripts/render-diagrams.sh                  # render SVG + PNG to docs/diagrams
  ./scripts/render-diagrams.sh --check          # CI: validate all diagrams
  ./scripts/render-diagrams.sh --format svg README.md
EOF
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUPPETEER_CONFIG="${REPO_ROOT}/scripts/mermaid-puppeteer.json"
# Render native SVG <text> (htmlLabels:false) so output is viewable outside a
# browser — IDE SVG previews and PDF exporters do not render foreignObject HTML.
MERMAID_CONFIG="${REPO_ROOT}/scripts/mermaid-config.json"

OUT_DIR="${REPO_ROOT}/docs/diagrams"
FORMAT="both"
CHECK_ONLY=0
declare -a INPUTS=()
declare -a FORMATS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT_DIR="$2"; shift 2 ;;
    --format) FORMAT="$2"; shift 2 ;;
    --check) CHECK_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; while [[ $# -gt 0 ]]; do INPUTS+=("$1"); shift; done ;;
    -*) echo "Unknown option: $1" >&2; usage; exit 2 ;;
    *) INPUTS+=("$1"); shift ;;
  esac
done

case "${FORMAT}" in
  both) FORMATS=(svg png) ;;
  svg|png) FORMATS=("${FORMAT}") ;;
  *)
    echo "Invalid --format '${FORMAT}'. Use both, svg, or png." >&2
    exit 2
    ;;
esac

detect_chrome() {
  if [[ -n "${PUPPETEER_EXECUTABLE_PATH:-}" && -x "${PUPPETEER_EXECUTABLE_PATH}" ]]; then
    echo "${PUPPETEER_EXECUTABLE_PATH}"
    return 0
  fi
  local candidate
  for candidate in google-chrome google-chrome-stable chromium chromium-browser chrome; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      command -v "${candidate}"
      return 0
    fi
  done
  for candidate in /opt/google/chrome/chrome /usr/bin/google-chrome \
    /usr/bin/chromium /usr/bin/chromium-browser /snap/bin/chromium; do
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

CHROME_BIN="$(detect_chrome || true)"
if [[ -z "${CHROME_BIN}" ]]; then
  echo "No Chrome/Chromium found." >&2
  echo "Install Chrome or Chromium, or set PUPPETEER_EXECUTABLE_PATH to a browser binary." >&2
  exit 1
fi
export PUPPETEER_EXECUTABLE_PATH="${CHROME_BIN}"

if [[ ${#INPUTS[@]} -eq 0 ]]; then
  INPUTS+=("${REPO_ROOT}/README.md")
  while IFS= read -r f; do INPUTS+=("$f"); done < <(find "${REPO_ROOT}/docs" -maxdepth 1 -name '*.md' | sort)
fi

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

if [[ "${CHECK_ONLY}" -eq 1 ]]; then
  RENDER_DIR="${TMP_ROOT}/out"
else
  RENDER_DIR="${OUT_DIR}"
fi
mkdir -p "${RENDER_DIR}"

# Chrome can intermittently time out while bringing up its WebSocket endpoint
# in CI ("Timed out ... waiting for the WS endpoint URL"). Retry a few times so
# a transient browser-launch hiccup does not fail the whole validation.
RENDER_ATTEMPTS="${RENDER_ATTEMPTS:-3}"

render_block() {
  local block="$1"
  local out_file="$2"
  local attempt=1
  while :; do
    if npx -y -p @mermaid-js/mermaid-cli mmdc \
      -p "${PUPPETEER_CONFIG}" \
      -c "${MERMAID_CONFIG}" \
      -i "${block}" \
      -o "${out_file}" \
      -b white >/dev/null 2>"${block}.err"; then
      return 0
    fi
    # Only retry transient browser-launch failures; real syntax errors fail fast.
    if (( attempt < RENDER_ATTEMPTS )) && grep -qiE 'WS endpoint|Timed out|Target closed|Protocol error|net::' "${block}.err"; then
      echo "  retry ${attempt}/${RENDER_ATTEMPTS} (transient browser launch) ..." >&2
      attempt=$((attempt + 1))
      sleep 3
      continue
    fi
    return 1
  done
}

echo "Browser:  ${CHROME_BIN}"
echo "Config:   ${PUPPETEER_CONFIG}"
echo "Formats:  ${FORMATS[*]}"
echo "Mode:     $([[ "${CHECK_ONLY}" -eq 1 ]] && echo validate || echo "render -> ${RENDER_DIR}")"
echo

total=0
failed=0

for md in "${INPUTS[@]}"; do
  if [[ ! -f "${md}" ]]; then
    echo "skip (not found): ${md}" >&2
    continue
  fi
  # Unique, path-derived slug so README.md and docs/README.md never collide.
  rel="${md#"${REPO_ROOT}/"}"
  base="$(printf '%s' "${rel%.md}" | tr '/ ' '__')"
  block_dir="${TMP_ROOT}/${base}"
  mkdir -p "${block_dir}"

  # Split each ```mermaid ... ``` fenced block into its own .mmd file.
  awk -v prefix="${block_dir}/block" '
    /^```mermaid[[:space:]]*$/ { inblock=1; n++; fname=prefix n ".mmd"; next }
    /^```[[:space:]]*$/ { if (inblock) { inblock=0; close(fname) }; next }
    inblock { print > fname }
  ' "${md}"

  shopt -s nullglob
  blocks=("${block_dir}"/block*.mmd)
  shopt -u nullglob
  [[ ${#blocks[@]} -eq 0 ]] && continue

  idx=0
  for block in "${blocks[@]}"; do
    idx=$((idx + 1))
    diagram_ok=1
    declare -a rendered_files=()
    for fmt in "${FORMATS[@]}"; do
      total=$((total + 1))
      out_file="${RENDER_DIR}/${base}-${idx}.${fmt}"
      if render_block "${block}" "${out_file}"; then
        rendered_files+=("${out_file}")
      else
        diagram_ok=0
        failed=$((failed + 1))
        echo "  FAIL  ${base} (diagram ${idx}, ${fmt})"
        sed 's/^/        /' "${block}.err" >&2 || true
      fi
    done
    if [[ ${diagram_ok} -eq 1 ]]; then
      if [[ "${CHECK_ONLY}" -eq 1 ]]; then
        echo "  ok    ${base} (diagram ${idx})"
      else
        echo "  ok    ${base} (diagram ${idx}) -> ${rendered_files[*]}"
      fi
    fi
  done
done

echo
if [[ ${total} -eq 0 ]]; then
  echo "No Mermaid diagrams found."
  exit 0
fi
echo "Diagrams: ${total}, failed: ${failed}"
[[ ${failed} -eq 0 ]] || exit 1
