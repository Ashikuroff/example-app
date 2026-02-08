.PHONY: setup test lint build push deploy-dev deploy-staging deploy-prod clean help

help:
	@echo "Available targets:"
	@echo "  make setup            - Set up Python virtual environment and install dependencies"
	@echo "  make test             - Run pytest on test/ directory"
	@echo "  make lint             - Run flake8 and pylint on src/"
	@echo "  make security         - Run bandit security scanner"
	@echo "  make build            - Build Docker image locally"
	@echo "  make push             - Push Docker image to registry"
	@echo "  make deploy-dev       - Deploy to dev cluster"
	@echo "  make deploy-staging   - Deploy to staging cluster"
	@echo "  make deploy-prod      - Deploy to prod cluster"
	@echo "  make clean            - Remove build artifacts and caches"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r src/requirements.txt
	. .venv/bin/activate && pip install -r requirements-test.txt

test:
	. .venv/bin/activate && pytest test/ -v --tb=short --cov=src/

lint:
	. .venv/bin/activate && flake8 src/ --max-line-length=100 --exclude=__pycache__
	. .venv/bin/activate && pylint src/server.py --exit-zero

security:
	. .venv/bin/activate && bandit -r src/ -f json -o bandit-report.json --exit-code 0

build:
	docker build -t {APP_NAME}:latest --target prod .

push:
	docker tag {APP_NAME}:latest {REGISTRY_IMAGE}:latest
	docker push {REGISTRY_IMAGE}:latest

deploy-dev:
	kustomize build k8s/overlays/dev | kubectl apply -f -
	kubectl rollout status deployment/dev-{APP_NAME} -n {NAMESPACE} -w

deploy-staging:
	kustomize build k8s/overlays/staging | kubectl apply -f -
	kubectl rollout status deployment/staging-{APP_NAME} -n {NAMESPACE} -w

deploy-prod:
	kustomize build k8s/overlays/prod | kubectl apply -f -
	kubectl rollout status deployment/prod-{APP_NAME} -n {NAMESPACE} -w

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	rm -rf .venv/
