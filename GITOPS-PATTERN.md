# GitOps Multi-App Repository Structure

This repository implements a GitOps pattern for managing multiple Python applications across development, staging, and production Kubernetes environments.

## Quick Navigation

- 🚀 **[ONBOARDING.md](./ONBOARDING.md)** - Step-by-step guide to add new Python apps
- 📊 **[OBSERVABILITY.md](./OBSERVABILITY.md)** - Prometheus, Grafana, and logging setup
- 🔍 **[apps/example-app/](./apps/example-app/)** - Working reference implementation
- ⚙️ **[.github/workflows/main.yml](./.github/workflows/main.yml)** - CI/CD automation

## Repository Structure

```
├── apps/                          # Applications managed by GitOps
│   ├── .template/                # Copy this to create new apps
│   │   ├── k8s/                  # Kubernetes manifests (base + overlays)
│   │   ├── src/                  # Python application code
│   │   ├── test/                 # Automated tests
│   │   ├── Dockerfile
│   │   ├── Makefile
│   │   └── README.md
│   └── example-app/              # Reference implementation
│       ├── k8s/
│       │   ├── base/            # Core manifests
│       │   └── overlays/        # Environment-specific patches
│       ├── src/
│       └── test/
├── argo/                          # ArgoCD configuration
│   ├── root-app.yaml            # Root application (entry point)
│   ├── apps/                    # Per-app and per-environment definitions
│   │   ├── example-app-dev.yaml
│   │   ├── example-app-staging.yaml
│   │   └── example-app-prod.yaml
│   ├── argo-cd/                 # ArgoCD installer and manifests
│   └── example-app/             # Deprecated - use apps/example-app instead
├── .github/
│   ├── workflows/
│   │   └── main.yml            # Automated build, test, publish, deploy
│   ├── prompts/                # Planning and design documents
│   └── skills/                 # Reusable automation tasks
├── ONBOARDING.md               # How to add new apps
├── OBSERVABILITY.md            # Monitoring setup
├── TROUBLESHOOTING.md          # Common issues and solutions
└── README.md                   # This file
```

## How It Works

### 1. Application Structure per App

Each app in `apps/{app-name}/` has:

- **`k8s/base/`** - Common Kubernetes manifests (Deployment, Service, ConfigMap)
- **`k8s/overlays/{dev,staging,prod}/`** - Environment-specific Kustomize patches:
  - Replica count (1 → 2 → 3)
  - Resource limits per environment
  - Image tags (dev-latest → staging-latest → semver)
  - Environment variables (DEBUG → INFO → WARNING)
- **`src/`** - Python Flask app with Prometheus metrics
- **`test/`** - Unit and integration tests
- **CI/CD integration** - Automated build and image tag management

### 2. Automated Image Tag Management

GitHub Actions workflow automatically:

1. **Runs on push** to `main`, `staging`, `develop`
2. **Builds Docker image** with semantic versioning
3. **Publishes to Docker Hub** with automatic tags:
   - Branch-based: `dev-latest`, `staging-latest`
   - Version-based: `v1.0.0` (main branch semver tags)
4. **Updates kustomization.yaml** with new image tag
5. **Commits changes** back to git - **enables GitOps sync**

```
git push → GitHub Actions → Docker Hub → image tag update → git push → ArgoCD detects → syncs cluster
```

### 3. GitOps Sync via ArgoCD

ArgoCD watches `argo/apps/` directory:

- **Root app** (`argo/root-app.yaml`) watches all app definitions
- **Each environment app** (e.g., `example-app-dev.yaml`) syncs overlay:
  ```yaml
  path: apps/example-app/k8s/overlays/dev
  ```
- **Automatic sync** - detects git changes and applies within seconds
- **Self-healing** - auto-recovers if manual changes made to cluster
- **Pruning** - removes resources no longer in git

## Core Concepts

### Kustomize Overlays

All apps use Kustomize for configuration management:

```bash
# View what will be deployed (no changes made)
kustomize build apps/example-app/k8s/overlays/prod

# Deploy manually (ArgoCD does this automatically)
kustomize build apps/example-app/k8s/overlays/prod | kubectl apply -f -
```

### Sealed Secrets

Sensitive data (API keys, DB URLs) encrypted with kubeseal:

```bash
# Encrypt a secret (one-time setup per app)
echo -n 'api-key-value' | kubectl create secret generic app-secret \
  --from-literal=api_key=- --dry-run=client -o yaml | \
  kubeseal -f - -w k8s/base/secret.yaml

# Only decrypts in-cluster with correct sealing key
```

### Multi-Environment Configuration

Each environment has its own overlay:

| Environment | Replicas | Log Level | Image Tag | Purpose |
|-------------|----------|-----------|-----------|---------|
| **dev** | 1 | DEBUG | dev-latest | Local testing, fast iteration |
| **staging** | 2 | INFO | staging-latest | Pre-prod validation |
| **prod** | 3 | WARNING | v1.0.0 | Production, stable version |

## Getting Started

### For New App Developers

1. **Copy template**: `cp -r apps/.template apps/my-app`
2. **Update placeholders** in `k8s/` manifests (app name, image, namespace)
3. **Write app code** in `src/server.py`
4. **Configure secrets**: `kubectl create secret ... | kubeseal ...`
5. **Push to github** → CI/CD builds and publishes → ArgoCD syncs

See **[ONBOARDING.md](./ONBOARDING.md)** for detailed steps.

### For DevOps Engineers

1. **Install ArgoCD**: `kubectl apply -f argo/argo-cd/install.yaml`
2. **Create sealed-secrets operator**: Deploy kubeseal to cluster
3. **Register root app**: `kubectl apply -f argo/root-app.yaml`
4. **Monitor**: Access ArgoCD UI to see all apps and sync status

See **[OBSERVABILITY.md](./OBSERVABILITY.md)** for monitoring setup.

## Development Workflow

### Local Development

```bash
# Set up virtual environment and dependencies
cd apps/example-app
make setup

# Run tests
make test

# Run app locally
python src/server.py  # or `flask run`

# View metrics
curl http://localhost:5000/metrics
```

### CI/CD Pipeline

```bash
# Just push to a branch - everything else is automated
git add .
git commit -m "feat: add user API endpoint"
git push origin feature-branch

# Workflow runs:
# 1. Tests run (pytest)
# 2. Linting (flake8, pylint)
# 3. Security scan (bandit)
# 4. Docker build & publish (on main/staging only)
# 5. Kustomize update (on main/staging only)
# 6. Git push with new image tag
# 7. ArgoCD detects and syncs cluster
```

### Monitoring & Observability

All apps expose metrics for Prometheus:

```bash
# View metrics from deployed app
kubectl port-forward deployment/dev-example-app 5000:5000
curl http://localhost:5000/metrics

# Or set up Grafana dashboard
# See OBSERVABILITY.md for instructions
```

## Common Tasks

### Deploy a new app to production

```bash
# 1. Prepare in dev environment
git checkout -b feature/my-new-app
cp -r apps/.template apps/my-app
# ... make changes ...
git push origin feature/my-new-app

# 2. Review in staging
git checkout staging
git merge feature/my-new-app
# Tests from main branch, but staging overlay testing

# 3. Release to production
git checkout main
git merge feature/my-new-app
git tag -a v1.0.0 -m "Release my-app v1.0.0"
git push origin main --tags

# Done! ArgoCD auto-syncs prod environment
```

### Update app dependency

```bash
cd apps/my-app
# Update src/requirements.txt with new version
# Commit changes
git commit -am "chore: upgrade flask to 3.1.0"
git push origin main

# CI/CD rebuilds and publishes
# ArgoCD syncs cluster automatically
```

### Fix a production bug

```bash
# Emergency patch
git checkout -b hotfix/bug-fix main
# Fix the bug
git commit -am "fix: handle edge case in API"
git push origin hotfix/bug-fix

# Merge to main and staging
git checkout main && git merge hotfix/bug-fix
git checkout staging && git merge hotfix/bug-fix

# Production gets new version automatically via ArgoCD
```

## Troubleshooting

Common issues and solutions are documented in [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

Key areas:
- Kustomize build failures
- Image tag not updating
- ArgoCD sync issues
- Secret decryption failures
- Pod crashes

## Best Practices

✅ **DO:**
- Use sealed-secrets for all credentials
- Run tests locally before pushing: `make test`
- Pin Python dependencies (no wildcards in requirements.txt)
- Create git branch for every change
- Commit Kustomize updates generated by CI/CD
- Use semantic versioning for prod releases

❌ **DON'T:**
- Commit plaintext secrets
- Manually edit deployments in cluster (use git)
- Use `:latest` tag in prod (always use semver)
- Skip tests or linting
- Deploy directly to prod without testing in staging

## Architecture Decisions

### Why Kustomize over Helm?

- Simpler for small teams (no Helm server needed)
- Works with plain YAML (lower learning curve)
- Excellent for multi-environment overlays
- No templating language to learn

### Why Sealed-Secrets over External Secrets Operator?

- Lower operational burden (no external system dependency)
- Secrets stay in git (audit trail)
- Works with single cluster setup
- Can add ESO layer later if needed

### Why Single Repo for Multiple Apps?

- Shared CI/CD, observability, documentation
- Easier onboarding (copy template, done)
- Centralized secrets and RBAC policy
- Can split repos per team if needed later

## Support & Documentation

- **New to this repo?** Start with [ONBOARDING.md](./ONBOARDING.md)
- **Issues deploying?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Need to monitor apps?** See [OBSERVABILITY.md](./OBSERVABILITY.md)
- **Working reference app?** Look at `apps/example-app/`

---

**Last Updated**: January 2025
**Maintainers**: DevOps/Platform Team
