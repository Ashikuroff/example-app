#!/bin/bash
# Install & Setup
# Sets up virtual environment and installs dependencies
# Usage: ./scripts/setup.sh [--upgrade]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPGRADE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --upgrade)
      UPGRADE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--upgrade]"
      echo "  --upgrade    Upgrade pip and all packages"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

cd "$SCRIPT_DIR"

echo "Setting up development environment..."

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

PYTHON=".venv/bin/python"
PIP=".venv/bin/pip"

# Upgrade pip/setuptools if requested
if [ "$UPGRADE" = true ]; then
  echo "Upgrading pip and setuptools..."
  $PIP install --upgrade pip setuptools wheel
fi

# Install requirements
echo "Installing dependencies..."
if [ -f "src/requirements.txt" ]; then
  $PIP install -r src/requirements.txt
fi
if [ -f "requirements-test.txt" ]; then
  $PIP install -r requirements-test.txt
fi

echo "✓ Development environment ready"
echo ""
echo "Next steps:"
echo "  ./scripts/test.sh          - Run tests"
echo "  ./scripts/server.sh        - Start dev server"
echo "  ./scripts/preflight.sh     - Run preflight validation"
