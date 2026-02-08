#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Parse arguments
COVERAGE=false
LINT=false

for arg in "$@"; do
    case $arg in
        --coverage)
            COVERAGE=true
            ;;
        --lint)
            LINT=true
            ;;
    esac
done

# Run linting if requested
if [ "$LINT" = true ]; then
    echo -e "${YELLOW}Running flake8...${NC}"
    flake8 src/ test/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
    echo -e "${GREEN}Flake8 complete${NC}"
fi

# Run tests
echo -e "${YELLOW}Running pytest...${NC}"

if [ "$COVERAGE" = true ]; then
    pytest test/ -v --tb=short --cov=src --cov-report=html --cov-report=term
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
else
    pytest test/ -v --tb=short
fi

echo -e "${GREEN}Tests complete${NC}"
