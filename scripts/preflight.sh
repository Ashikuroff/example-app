#!/bin/bash
# Azure Deployment Preflight Wrapper
# Runs preflight validation for Bicep deployments
# Usage: ./scripts/preflight.sh [--execute] [--output <path>]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFLIGHT_PY="${SCRIPT_DIR}/.github/skills/azure-deployment-preflight/preflight.py"
EXECUTE=false
OUTPUT="preflight-report.md"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute)
      EXECUTE=true
      shift
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--execute] [--output <path>]"
      echo "  --execute     Actually run bicep/az commands (requires CLI auth)"
      echo "  --output      Output report path (default: preflight-report.md)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Check for Python
if ! command -v python3 &> /dev/null; then
  echo "ERROR: python3 not found in PATH" >&2
  exit 1
fi

# Run preflight
echo "Running Azure Deployment Preflight..."
cmd="python3 '${PREFLIGHT_PY}' --root '${SCRIPT_DIR}' --output '${OUTPUT}'"
if [ "$EXECUTE" = true ]; then
  cmd="${cmd} --execute"
fi

eval "$cmd"

echo "✓ Report written to: ${OUTPUT}"
if [ -f "${OUTPUT}" ]; then
  echo "---"
  head -20 "${OUTPUT}"
  echo "[... see full report in ${OUTPUT} ...]"
fi
