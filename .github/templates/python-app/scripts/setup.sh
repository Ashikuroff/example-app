#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up development environment...${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
if [ -f "src/requirements.txt" ]; then
    echo -e "${YELLOW}Installing application dependencies...${NC}"
    pip install -r src/requirements.txt
fi

if [ -f "requirements-test.txt" ]; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -r requirements-test.txt
fi

echo -e "${GREEN}Setup complete! Activate env with: source .venv/bin/activate${NC}"
