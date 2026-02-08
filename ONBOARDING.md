# GitOps Python App Onboarding Guide

Welcome! This guide will walk you through adding a new Python application to our GitOps-managed Kubernetes cluster. The process leverages Kustomize overlays, sealed-secrets for credentials, and GitOps automation via ArgoCD.

## Quick Start (5 minutes)

Follow these steps to onboard a new Python app with full multi-environment support:

### Step 1: Copy the Template

```bash
# Clone the template from example-app
cp -r apps/example-app apps/my-new-app

# Update references to use your app name
cd apps/my-new-app
```

### Step 2: Update Kubernetes Manifests

Update placeholders in `k8s/base/` and overlays:

1. **k8s/base/kustomization.yaml**
   ```yaml
   commonLabels:
     app: my-new-app  # Change from example-app
   
   resources:
     # ... same as example-app ...
   
   images:
   - name: my-docker-image  # Update image name
     newName: your-registry/my-new-app
     newTag: latest
   ```

2. **k8s/base/deployment.yaml**
   ```yaml
   metadata:
     name: my-new-app  # Change from example-app
     labels:
       app: my-new-app
   spec:
     selector:
       matchLabels:
         app: my-new-app
     template:
       metadata:
         labels:
           app: my-new-app
       spec:
         containers:
         - name: my-new-app  # Change container name
           image: your-registry/my-new-app:latest
   ```

3. **k8s/base/service.yaml**
   ```yaml
   spec:
     selector:
       app: my-new-app
   ```

4. **k8s/base/namespace.yaml** (if using custom namespace)
   ```yaml
   metadata:
     name: my-new-app  # Change namespace name
   ```

5. **Update all overlay** `kustomization.yaml` files:
   ```yaml
   commonLabels:
     app: my-new-app  # Update in dev, staging, prod
   
   replicas:
   - name: my-new-app  # Updated name reference
     count: 1  # (dev=1, staging=2, prod=3)
   
   images:
   - name: my-docker-image  # Match your base image name
     newTag: dev-latest  # (or staging-latest, v1.0.0)
   ```

### Step 3: Update Application Source Code

```bash
# Copy your app code, replacing example-app files
rm -rf src/*
cp -r /path/to/your/app/src/* src/

# Update Dockerfile if needed (or reuse example template)
# Update requirements.txt for your dependencies
```

### Step 4: Configure CI/CD (GitHub Actions)

Update `.github/workflows/main.yml` **if needed** (most config is automatic):

1. Verify `IMAGE_NAME` environment variable uses your registry/app name:
   ```yaml
   env:
     REGISTRY: docker.io
     IMAGE_NAME: ${{ secrets.DOCKER_USERNAME }}/my-new-app
   ```

2. Verify GitHub Actions secrets are configured:
   - `DOCKER_USERNAME` - Your Docker Hub username
   - `DOCKER_PASSWORD` - Your Docker Hub token/password
   - `GITHUB_TOKEN` - Auto-provided by GitHub

3. The workflow automatically:
   - Runs tests on PR/push
   - Builds Docker image on push to main/staging
   - Publishes to Docker Hub with semantic versioning
   - Updates kustomization.yaml with new image tag
   - Commits and pushes changes (enabling GitOps sync)

### Step 5: Create Sealed Secrets for Credentials

Generate encrypted secrets using `kubeseal` (sealed-secrets operator must be deployed):

```bash
# Generate a sealed secret
echo -n 'your-api-key-value' | \
  kubectl create secret generic my-new-app-secret \
    --from-literal=api_key=- \
    --dry-run=client \
    -o yaml | \
  kubeseal -f - -w apps/my-new-app/k8s/base/secret.yaml

# Verify it was created
cat apps/my-new-app/k8s/base/secret.yaml

# If not auto-read, also create for staging/prod with environment-specific prefixes
```

**⚠️ IMPORTANT: Do NOT commit plaintext secrets. The sealed secret is encrypted and only decrypts in-cluster.**

### Step 6: Verify Kustomize Configuration

Test that all Kustomize overlays build correctly:

```bash
# Test each overlay
kustomize build apps/my-new-app/k8s/overlays/dev
kustomize build apps/my-new-app/k8s/overlays/staging
kustomize build apps/my-new-app/k8s/overlays/prod

# All three should output valid YAML with no errors
```

### Step 7: Register with ArgoCD

Create ArgoCD Application manifests for each environment:

```bash
# Create a directory for ArgoCD config (optional, can use same repo)
mkdir -p argo/apps/my-new-app

# Create Application manifests for each environment
cat > argo/apps/my-new-app/app-dev.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-new-app-dev
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR_ORG/YOUR_REPO
    targetRevision: HEAD
    path: apps/my-new-app/k8s/overlays/dev
  destination:
    server: https://kubernetes.default.svc
    namespace: my-new-app
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF

# Repeat for staging and prod with appropriate paths
# Then apply:
kubectl apply -f argo/apps/my-new-app/
```

### Step 8: Push to Git & Deploy

```bash
# Commit your changes
git add apps/my-new-app/
git commit -m "feat: onboard my-new-app with GitOps pattern"
git push origin main

# ArgoCD automatically detects changes in git and syncs:
# - Watches argo/apps/ directory
# - Creates resources if missing
# - Automatically syncs on git push
# View ArgoCD UI to confirm sync status:
# https://your-argocd-dashboard/ → applications
```

## Directory Structure Reference

Your app will follow this standardized structure:

```
apps/my-new-app/
├── k8s/
│   ├── base/                          # Core manifests (single copy)
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml                # Sealed (encrypted) secret
│   │   ├── namespace.yaml
│   │   └── kustomization.yaml         # Image patch config
│   └── overlays/                      # Per-environment customizations
│       ├── dev/
│       │   ├── kustomization.yaml     # 1 replica, dev image tags, DEBUG logs
│       │   └── deployment-patch.yaml  # Optional resource overrides
│       ├── staging/
│       │   ├── kustomization.yaml     # 2 replicas, staging image tags, INFO logs
│       │   └── deployment-patch.yaml
│       └── prod/
│           ├── kustomization.yaml     # 3 replicas, prod image tags, WARNING logs
│           └── deployment-patch.yaml
├── src/                               # Application source code
│   ├── server.py                      # Main app (Flask with Prometheus metrics)
│   ├── requirements.txt               # Python dependencies
│   └── __init__.py
├── test/                              # Automated tests
│   ├── test_app.py
│   └── __init__.py
├── Dockerfile                         # Multi-stage: debug → prod targets
├── Makefile                           # Local tasks: setup, test, build, deploy
└── README.md                          # App-specific documentation
```

## Docker Image Tag Strategy

The CI/CD pipeline automatically manages image tags based on your git branch:

| Branch | Image Tag | Kustomize Path | Use Case |
|--------|-----------|-----------------|----------|
| `develop` | `dev-latest` | `overlays/dev` | Local testing |
| `staging` | `staging-latest` | `overlays/staging` | Pre-prod validation |
| `main` | `v1.0.0` (semver) | `overlays/prod` | Production release |

**Note**: The workflow updates the image tag in `kustomization.yaml` automatically after pushing to Docker Hub.

## Troubleshooting

### Issue: "Kustomize build" fails with undefined image

**Solution**: Ensure your `k8s/base/kustomization.yaml` has an `images` section:
```yaml
images:
- name: your-docker-image  # Must match Dockerfile/registry image
  newName: your-registry/my-new-app
  newTag: latest
```

### Issue: Sealed secret won't decrypt in pod

**Cause**: Secret was sealed with wrong sealing key (different cluster)
**Solution**:
```bash
# Reseal on the correct cluster:
kubectl get secret my-secret -o yaml | kubeseal -f - -w secret.yaml
```

### Issue: Image tag not updating in kustomization.yaml after push

**Cause**: GitHub Actions workflow failed or incorrect `IMAGE_NAME` env var
**Solution**:
1. Check Actions tab in GitHub for workflow logs
2. Verify `secrets.DOCKER_USERNAME` is set in repo settings
3. Verify push branch is `main` or `staging` (workflow only runs on these)

### Issue: ArgoCD not syncing changes

**Cause**: Application CR not found or watching wrong git path
**Solution**:
```bash
# Verify Application exists in argocd namespace:
kubectl get applications -n argocd

# Check Application status:
kubectl describe application my-new-app-dev -n argocd

# Force refresh (usually not needed):
argocd app sync my-new-app-dev
```

### Issue: Pods in CrashLoopBackOff

**Common causes**:
- Missing environment variables (check ConfigMap values)
- Sealed secret failed to decrypt (check sealing key)
- Image not found in registry (check image name in kustomization.yaml)

**Debug**:
```bash
# Check pod logs
kubectl logs -f deployment/my-new-app -n my-new-app

# Check event history
kubectl describe pod <pod-name> -n my-new-app

# Verify secrets mounted correctly
kubectl get secret -n my-new-app
```

## Multi-Environment Deployment Example

Once your app is onboarded, deploying to all 3 environments is automatic:

```bash
# Push code change to main branch
git commit -am "feat: add new API endpoint"
git push origin main

# 1. GitHub Actions workflow triggers
# 2. Tests run, image builds, publishes to Docker Hub
# 3. Image tag updates in kustomization.yaml (prod overlay gets v1.0.0)
# 4. Changes committed and pushed back to git
# 5. ArgoCD detects updated manifests and syncs
# 6. Cluster pulls new image and rolls out pods

# View deployment progress (from local machine or CI/CD):
kubectl rollout status deployment/prod-my-new-app -n my-new-app -w
```

## Best Practices

✅ **DO:**
- Keep source code (`src/`) in your `apps/{app}/` directory
- Run tests locally before pushing: `make test`
- Pin Python dependencies in `requirements.txt` (no wildcards)
- Use sealed-secrets for all credentials
- Commit kustomization.yaml updates (auto-generated by CI/CD)

❌ **DON'T:**
- Hardcode image tags in Deployment manifests (use kustomize)
- Commit plaintext secrets to git
- Use `:latest` tag in prod overlays (always use semver)
- Manually edit kustomize overlay files from CI/CD output
- Deploy without running tests

## Example App Walkthrough

For reference, see `apps/example-app/` which implements all these patterns:

1. Base manifests define core app: [apps/example-app/k8s/base/](../apps/example-app/k8s/base/)
2. Dev overlay: 1 replica, debug logs: [apps/example-app/k8s/overlays/dev/](../apps/example-app/k8s/overlays/dev/)
3. Staging overlay: 2 replicas, info logs: [apps/example-app/k8s/overlays/staging/](../apps/example-app/k8s/overlays/staging/)
4. Prod overlay: 3 replicas, warning logs: [apps/example-app/k8s/overlays/prod/](../apps/example-app/k8s/overlays/prod/)
5. CI/CD automation: [.github/workflows/main.yml](./.github/workflows/main.yml)

---

**Questions?** Check `TROUBLESHOOTING.md` or review `example-app` structure for a working reference.
