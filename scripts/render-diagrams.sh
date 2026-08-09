#!/usr/bin/env bash
set -euo pipefail

# Render (or validate) the PlantUML system diagrams in docs/diagrams/*.puml.
#
# PlantUML is the single diagram toolchain for this repo (no Mermaid).
# Requires Java; the PlantUML jar is fetched once into a local cache.

usage() {
  cat <<'EOF'
Usage: render-diagrams.sh [--out <dir>] [--check] [files...]

Render PlantUML sources to SVG.

Options:
  --out <dir>       Output directory for images (default: docs/diagrams).
  --check           Validate only (plantuml -checkonly); render nothing.
                    Exit non-zero if any diagram fails.
  -h, --help        Show this help.

Files:
  Defaults to docs/diagrams/*.puml when none are given.

Tooling:
  Needs Java. The PlantUML jar is fetched to ~/.cache/plantuml on first use
  (override the location with PLANTUML_JAR). C4 diagrams include the
  C4-PlantUML stdlib from the network at render time.

Examples:
  ./scripts/render-diagrams.sh                  # render all diagrams to SVG
  ./scripts/render-diagrams.sh --check          # CI: validate all diagrams
  ./scripts/render-diagrams.sh docs/diagrams/01-context.puml
EOF
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${REPO_ROOT}/docs/diagrams"
CHECK_ONLY=0
declare -a INPUTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT_DIR="$2"; shift 2 ;;
    --check) CHECK_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; while [[ $# -gt 0 ]]; do INPUTS+=("$1"); shift; done ;;
    -*) echo "Unknown option: $1" >&2; usage; exit 2 ;;
    *) INPUTS+=("$1"); shift ;;
  esac
done

if [[ ${#INPUTS[@]} -eq 0 ]]; then
  while IFS= read -r f; do INPUTS+=("$f"); done < <(find "${REPO_ROOT}/docs/diagrams" -maxdepth 1 -name '*.puml' | sort)
fi

PLANTUML_JAR="${PLANTUML_JAR:-${HOME}/.cache/plantuml/plantuml.jar}"
ensure_plantuml() {
  if [[ -f "${PLANTUML_JAR}" ]]; then
    return 0
  fi
  if ! command -v java >/dev/null 2>&1; then
    echo "PlantUML rendering needs Java. Install a JRE or set PLANTUML_JAR." >&2
    return 1
  fi
  mkdir -p "$(dirname "${PLANTUML_JAR}")"
  echo "Fetching PlantUML jar -> ${PLANTUML_JAR}"
  curl -fsSL -o "${PLANTUML_JAR}" \
    "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"
}

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

echo "PlantUML: ${#INPUTS[@]} source(s), jar ${PLANTUML_JAR}"
echo "Mode:     $([[ "${CHECK_ONLY}" -eq 1 ]] && echo validate || echo "render -> ${OUT_DIR}")"
echo

ensure_plantuml || exit 1
[[ "${CHECK_ONLY}" -eq 1 ]] || mkdir -p "${OUT_DIR}"

total=0
failed=0

for puml in "${INPUTS[@]}"; do
  if [[ ! -f "${puml}" ]]; then
    echo "skip (not found): ${puml}" >&2
    continue
  fi
  total=$((total + 1))
  name="$(basename "${puml}")"
  if [[ "${CHECK_ONLY}" -eq 1 ]]; then
    if java -Djava.awt.headless=true -jar "${PLANTUML_JAR}" -checkonly "${puml}" >/dev/null 2>"${TMP_ROOT}/${name}.err"; then
      echo "  ok    ${name}"
    else
      failed=$((failed + 1))
      echo "  FAIL  ${name}"
      sed 's/^/        /' "${TMP_ROOT}/${name}.err" >&2 || true
    fi
  else
    if java -Djava.awt.headless=true -jar "${PLANTUML_JAR}" -tsvg -o "${OUT_DIR}" "${puml}" >/dev/null 2>"${TMP_ROOT}/${name}.err"; then
      echo "  ok    ${name} -> ${OUT_DIR}/${name%.puml}.svg"
    else
      failed=$((failed + 1))
      echo "  FAIL  ${name}"
      sed 's/^/        /' "${TMP_ROOT}/${name}.err" >&2 || true
    fi
  fi
done

echo
if [[ ${total} -eq 0 ]]; then
  echo "No diagrams found."
  exit 0
fi
echo "Diagrams: ${total}, failed: ${failed}"
[[ ${failed} -eq 0 ]] || exit 1
