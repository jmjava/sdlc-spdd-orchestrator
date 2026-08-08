#!/usr/bin/env bash
set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/common.sh"
# shellcheck source=/dev/null
source "${_SCRIPT_DIR}/lib/paths.sh"

usage() {
  cat <<'EOF'
Usage: detect-stack.sh --target <path>

Detect project technologies. Findings are printed and written to the
gitignored runtime file <home>/.sdlc/stack-detection.md (regenerated each run).
EOF
}

TARGET="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

TARGET="$(sdlc_resolve_target "${TARGET}")"
export SDLC_ROOT="${TARGET}"
detection_file="$(sdlc_runtime_dir "${TARGET}")/stack-detection.md"
mkdir -p "$(dirname "${detection_file}")"

detected=()

[[ -f "${TARGET}/pom.xml" ]] && detected+=("Maven Java project")
[[ -f "${TARGET}/build.gradle" || -f "${TARGET}/build.gradle.kts" ]] && detected+=("Gradle project")
[[ -d "${TARGET}/src/main/java" ]] && detected+=("Java source layout")
[[ -d "${TARGET}/src/main/kotlin" ]] && detected+=("Kotlin source layout")
[[ -f "${TARGET}/package.json" ]] && detected+=("Node project")
[[ -f "${TARGET}/requirements.txt" || -f "${TARGET}/pyproject.toml" ]] && detected+=("Python project")
[[ -f "${TARGET}/Dockerfile" ]] && detected+=("Docker project")
[[ -f "${TARGET}/docker-compose.yml" || -f "${TARGET}/docker-compose.yaml" ]] && detected+=("Docker Compose project")
[[ -d "${TARGET}/k8s" || -d "${TARGET}/kubernetes" ]] && detected+=("Kubernetes manifests")
[[ -d "${TARGET}/tekton" || -d "${TARGET}/.tekton" ]] && detected+=("Tekton pipelines")
[[ -d "${TARGET}/.github/workflows" ]] && detected+=("GitHub Actions workflows")
[[ -d "${TARGET}/charts" || -f "${TARGET}/Chart.yaml" ]] && detected+=("Helm chart")

timestamp="$(sdlc_timestamp_iso)"
{
  echo "# Stack Detection"
  echo
  echo "Last run: ${timestamp}"
  echo
  if ((${#detected[@]} == 0)); then
    echo "- No known stack markers detected"
  else
    for item in "${detected[@]}"; do
      echo "- ${item}"
    done
  fi
} > "${detection_file}"

echo "Stack detection complete. Updated: ${detection_file}"
if ((${#detected[@]} > 0)); then
  printf 'Detected:\n'
  printf '  - %s\n' "${detected[@]}"
else
  echo "No known stack markers detected."
fi
