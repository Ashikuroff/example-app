.PHONY: help setup test test-coverage test-integration server server-debug lint clean build docker-build docker-push deploy

help:
	@echo "Available commands:"
	@echo "  make setup                - Install and setup development environment"
	@echo "  make test                 - Run unit tests"
	@echo "  make test-coverage        - Run tests with coverage report"
	@echo "  make test-integration     - Run integration tests (requires running server)"
	@echo "  make lint                 - Run linting (flake8)"
	@echo "  make server               - Start development server on port 5000"
	@echo "  make server-debug         - Start dev server with debug mode"
	@echo "  make build                - Build Docker image (docker-build)"
	@echo "  make docker-build         - Build Docker image locally"
	@echo "  make docker-push          - Push Docker image to registry"
	@echo "  make deploy               - Deploy to current kubeconfig context"
	@echo "  make clean                - Clean up cache and artifacts"

setup:
	./scripts/setup.sh

test:
	./scripts/test.sh

test-coverage:
	./scripts/test.sh --coverage

test-integration:
	@echo "Running integration tests..."
	pytest test/integration_test.py -v --tb=short

lint:
	./scripts/test.sh --lint

server:
	./scripts/server.sh

server-debug:
	./scripts/server.sh --debug

docker-build:
	docker build -t {REGISTRY_IMAGE}:dev .

docker-push: docker-build
	docker push {REGISTRY_IMAGE}:dev

deploy:
	kubectl apply -k k8s/overlays/dev -n {NAMESPACE}

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache/ .coverage htmlcov/ build/ dist/ *.egg-info/
	@echo "Cleaned up cache and artifacts"
