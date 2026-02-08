# Python App Template

This template provides a complete, production-ready Python application with GitOps integration, Kubernetes manifests, and CI/CD automation.

## Files

```
{APP_NAME}/
├── .github/
│   └── workflows/
│       └── main.yml              # CI/CD pipeline
├── src/
│   ├── __init__.py
│   ├── server.py                 # Main Flask app
│   └── requirements.txt           # Python dependencies
├── test/
│   ├── __init__.py
│   ├── test_server.py            # Unit tests
│   └── conftest.py               # Pytest fixtures
├── k8s/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secret-template.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── dev/
│       ├── staging/
│       └── prod/
├── Dockerfile
├── Makefile
├── README.md
└── requirements-test.txt
```

## Quick Start

1. **Copy the template**:
   ```bash
   cp -r .github/templates/python-app apps/{YOUR_APP_NAME}
   ```

2. **Replace placeholders**:
   - `{APP_NAME}` → your app name
   - `{REGISTRY_IMAGE}` → your Docker registry image (e.g., `ashik9001/my-app`)
   - `{NAMESPACE}` → deployment namespace (e.g., `my-app`)
   - `{GITHUB_REPO}` → your GitHub repo URL

3. **Setup secrets**:
   ```bash
   cd apps/{YOUR_APP_NAME}
   kubectl create secret generic {APP_NAME}-secret \
     --from-literal=api_key='your-key' \
     --dry-run=client -o yaml | kubeseal -f - -w k8s/base/secret.yaml
   ```

4. **Commit and push**:
   ```bash
   git add apps/{YOUR_APP_NAME}
   git commit -m "feat: add {YOUR_APP_NAME} to GitOps"
   git push
   ```

5. **ArgoCD auto-syncs** based on the path pattern in root-app.yaml

## Customization

### Environment-specific values

Edit `k8s/overlays/{dev,staging,prod}/kustomization.yaml`:
- Change `replicas` count
- Adjust `resource` limits
- Override `log_level` and other configs
- Set environment-specific image tags

### Health checks

Customize the health endpoints in `src/server.py`:
- `/health` - readiness/liveness checks
- `/metrics` - Prometheus metrics

### Python dependencies

Add to `src/requirements.txt`:
```
your-dependency==1.0.0
```

Then rebuild:
```bash
make setup
make test
make build
```

## CI/CD Behavior

The GitHub Actions workflow (`main.yml`):
1. Runs tests on every push/PR
2. Lints code with flake8/pylint
3. Builds Docker image
4. On `main` or `staging` branches: publishes to registry and updates Kustomize image tags
5. ArgoCD detects the change and auto-syncs
