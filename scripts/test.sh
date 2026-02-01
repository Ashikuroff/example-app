#!/bin/bash
# Test Runner
# Runs pytest with coverage and optional linting
# Usage: ./scripts/test.sh [--coverage] [--lint]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COVERAGE=false
LINT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --coverage)
      COVERAGE=true
      shift
      ;;
    --lint)
      LINT=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--coverage] [--lint]"
      echo "  --coverage    Generate coverage report"
      echo "  --lint        Run linting (requires flake8)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

cd "$SCRIPT_DIR"

# Check for Python venv
if [ ! -d ".venv" ]; then
  echo "ERROR: Virtual environment not found at .venv" >&2
  exit 1
fi

PYTHON=".venv/bin/python"
PYTEST=".venv/bin/pytest"

# Lint if requested
if [ "$LINT" = true ]; then
  echo "Running linting..."
  if command -v flake8 &> /dev/null; then
    flake8 src/ test/ --max-line-length=120 || true
  else
    echo "flake8 not installed, skipping lint"
  fi
fi

# Run tests
echo "Running tests..."
if [ "$COVERAGE" = true ]; then
  if ! $PYTHON -c "import coverage" 2>/dev/null; then
    echo "coverage module not found, installing..."
    $PYTHON -m pip install -q coverage
  fi
  $PYTEST --cov=src --cov-report=term-missing test/
else
  $PYTEST test/ -v
fi

echo "✓ Tests passed"
