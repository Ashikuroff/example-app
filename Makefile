.PHONY: help setup test test-coverage server preflight lint clean

help:
	@echo "Available commands:"
	@echo "  make setup           - Install and setup development environment"
	@echo "  make test            - Run tests"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make lint            - Run linting (flake8)"
	@echo "  make server          - Start development server on port 5000"
	@echo "  make server-debug    - Start dev server with debug mode"
	@echo "  make preflight       - Run Azure Deployment Preflight (dry-run)"
	@echo "  make preflight-exec  - Run preflight with actual command execution"
	@echo "  make clean           - Clean up cache and artifacts"

setup:
	./scripts/setup.sh

test:
	./scripts/test.sh

test-coverage:
	./scripts/test.sh --coverage

lint:
	./scripts/test.sh --lint

server:
	./scripts/server.sh

server-debug:
	./scripts/server.sh --debug

preflight:
	./scripts/preflight.sh

preflight-exec:
	./scripts/preflight.sh --execute

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache/ .coverage htmlcov/ build/ dist/ *.egg-info/
	@echo "Cleaned up cache and artifacts"
