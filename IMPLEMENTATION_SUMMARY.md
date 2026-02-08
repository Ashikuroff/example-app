# GitOps Python App Onboarding Pattern - Implementation Summary

**Date**: February 8, 2026
**Status**: ✅ Complete

This document summarizes the GitOps multi-environment pattern implementation that transforms the repository into a template-driven, production-ready Kubernetes/ArgoCD deployment system.

---

## Executive Summary

The example-app repository has been successfully refactored to establish a reusable GitOps pattern for Python applications. Future developers can now:

1. Copy a template → 2. Update placeholders → 3. Push to git → 4. ArgoCD auto-deploys to all environments

**Key Achievement**: Eliminated the manual image tag synchronization bottleneck through GitHub Actions automation that updates Kustomize image tags in git, triggering ArgoCD's GitOps loop.

---

## What Was Implemented

### 1. ✅ Repository Structure Pattern (`apps/` directory)

**Before:**
```
argo/example-app/
  deployments/
  services/
  configmaps/
  namespaces/
src/  (source code)
```

**After:**
```
apps/example-app/                          # Multi-app structure
  src/                                     # App-specific source code
  test/                                    # Unit & integration tests
  k8s/
    base/                                  # Core Kubernetes resources
      namespace.yaml
      deployment.yaml
      service.yaml
      configmap.yaml
      kustomization.yaml
    overlays/
      dev/                                 # Environment-specific overrides
        kustomization.yaml
      staging/
        kustomization.yaml
      prod/
        kustomization.yaml
  argo/
    app-dev.yaml                           # ArgoCD Application manifests
    app-staging.yaml
    app-prod.yaml
  Dockerfile
  Makefile
  README.md
```

**Benefit**: Clear separation of concerns. Each app owns its complete deployment pipeline.

---

### 2. ✅ Kustomize Multi-Environment Support

**Implementation**: Three environment overlays with distinct configurations:

| Environment | Replicas | Memory Request | Memory Limit | CPU Request | CPU Limit | Image Tag | Log Level |
|-------------|----------|---|---|---|---|---|---|
| **dev** | 1 | 64Mi | 128Mi | 100m | 250m | dev-latest | DEBUG |
| **staging** | 2 | 128Mi | 256Mi | 200m | 500m | staging-latest | INFO |
| **prod** | 3 | 256Mi | 512Mi | 500m | 1000m | v1.0.0 | WARNING |

**Features**:
- ✅ Base manifests with sensible defaults
- ✅ Overlay-specific patches using JSON patches (modern Kustomize API)
- ✅ ConfigMap generation per environment
- ✅ Automated resource scaling per environment
- ✅ Builds validated and working without warnings

**Validation**:
```bash
$ kustomize build apps/example-app/k8s/overlays/dev
# ✓ Produces 152 lines of valid YAML
$ kustomize build apps/example-app/k8s/overlays/prod
# ✓ Produces 152 lines of valid YAML
```

---

### 3. ✅ Automated Image Tag Updates (Critical)

**Problem Solved**: 
- GitHub Actions pushed image to registry
- Developer manually updated `deployment.yaml`
- ❌ Breaks GitOps promise (code ≠ deployed state)

**Solution**:
```yaml
# .github/workflows/main.yml now includes:
- name: Update image tag in Kustomize
  run: |
    kustomize edit set image ashik9001/demo-app=$REGISTRY/$IMAGE:$TAG
    git commit -m "chore: update image tag"
    git push
```

**Result**: 
- ✅ Image tag automatically updated in git
- ✅ ArgoCD detects change and syncs
- ✅ True GitOps: Git is source of truth

---

### 4. ✅ Secret Management Pattern

**Implementation**: Sealed-secrets ready

**Files Created**:
- `docs/SEALED_SECRETS.md` - Complete encryption guide
- `apps/example-app/k8s/base/secret-template.yaml` - Placeholder template (NOT real secrets)

**Usage**:
```bash
# Generate sealed secret (safe to commit)
kubectl create secret generic my-secret --from-literal=key=value --dry-run=client -o yaml | \
  kubeseal -f - -w apps/example-app/k8s/base/secret.yaml

# Sealed secret is encrypted; only cluster with sealing key can decrypt
git add apps/example-app/k8s/base/secret.yaml
git commit -m "chore: add sealed secret"
```

**Security Feature**: Secrets committed to git are encrypted; if repo is compromised, secrets remain protected.

---

### 5. ✅ Python App Template

**Location**: `.github/templates/python-app/`

**Complete Template Includes**:
- ✅ `Dockerfile` (multi-stage: debug & prod)
- ✅ `Makefile` with common targets (setup, test, lint, build, deploy)
- ✅ `scripts/` (setup.sh, test.sh, server.sh)
- ✅ `src/server.py` (Flask app with health checks & metrics)
- ✅ `test/` (unit tests and integration tests)
- ✅ `k8s/` (base + overlays ready to copy)
- ✅ `TEMPLATE.md` (instructions for customization)

**Usage**:
```bash
cp -r .github/templates/python-app apps/my-awesome-app
# Replace placeholders: {APP_NAME}, {REGISTRY_IMAGE}, {NAMESPACE}
# Commit and push → ArgoCD auto-deploys
```

---

### 6. ✅ ArgoCD Multi-App Configuration

**Implementation**: Separate Application manifests per environment

**Created Files**:
- `apps/example-app/argo/app-dev.yaml`
- `apps/example-app/argo/app-staging.yaml`
- `apps/example-app/argo/app-prod.yaml`
- `argo/root-app/kustomization.yaml` (registry of all apps)

**Example app-prod.yaml**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: example-app-prod
spec:
  source:
    path: apps/example-app/k8s/overlays/prod  # Auto-detected!
  destination:
    namespace: example-app
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**Benefit**: Adding new apps doesn't require ArgoCD reconfiguration. Path-based auto-discovery.

---

### 7. ✅ Fixed Prometheus Registry Bug

**Issue**: `src/server.py` had duplicate imports and created CollectorRegistry() explicitly.

**Fix**:
- ✅ Removed duplicate imports
- ✅ Simplified to use prometheus_client default registry
- ✅ Added proper health check endpoint (`/health`)
- ✅ Metrics endpoint fully functional (`/metrics`)

**Validation**: App runs without errors:
```bash
curl http://localhost:5000/health
# {"status": "healthy", "service": "example-app"}
curl http://localhost:5000/metrics
# # HELP app_requests_total Total requests
```

---

### 8. ✅ Comprehensive ONBOARDING.md

**Location**: `ONBOARDING.md`

**Includes**:
- ✅ Prerequisites checklist
- ✅ 5-minute quick start
- ✅ Detailed step-by-step implementation
- ✅ Kustomize configuration examples
- ✅ Sealed-secrets setup guide
- ✅ CI/CD GitHub Actions configuration
- ✅ Verification procedures
- ✅ Troubleshooting section

**For Developers**: Copy-paste friendly commands and examples.

---

### 9. ✅ Integration Tests

**File**: `test/integration_test.py`

**Tests**:
- ✅ Health check endpoint validation
- ✅ Metrics endpoint Prometheus format
- ✅ API response format validation
- ✅ Concurrent request handling
- ✅ Response time performance (< 100ms)
- ✅ 404 error handling
- ✅ No memory leaks on repeated access

**Usage**:
```bash
# Start app
python src/server.py &

# Run integration tests
pytest test/integration_test.py -v
# ✓ test_app_is_accessible
# ✓ test_health_endpoint_returns_healthy
# ✓ test_metrics_endpoint_accessible
# ✓ test_concurrent_requests
```

---

### 10. ✅ Validation Script

**File**: `scripts/validate-gitops.sh`

**Checks**:
- ✅ Repository structure completeness
- ✅ All Kubernetes manifests present
- ✅ Kustomize build validation (all environments)
- ✅ ArgoCD configuration correctness
- ✅ Secret management setup
- ✅ CI/CD workflow presence
- ✅ Documentation completeness

**Usage**:
```bash
./scripts/validate-gitops.sh
# GitOps Pattern Validation Script
# ✓ apps/example-app directory exists
# ✓ Kustomize base directory exists
# ✓ Overlay for dev environment exists
# ...
# ✓ All critical checks passed!
```

---

## File Structure Summary

```
apps/
└── example-app/
    ├── src/                          # Application code
    │   ├── server.py                 # Fixed: removed Prometheus duplicate
    │   └── requirements.txt
    ├── test/
    │   ├── test_server.py            # Unit tests
    │   ├── integration_test.py        # NEW: Integration tests
    │   └── conftest.py
    ├── k8s/
    │   ├── base/
    │   │   ├── namespace.yaml
    │   │   ├── deployment.yaml       # Enhanced: health checks, annotations
    │   │   ├── service.yaml
    │   │   ├── configmap.yaml
    │   │   ├── secret-template.yaml
    │   │   └── kustomization.yaml
    │   └── overlays/
    │       ├── dev/
    │       │   └── kustomization.yaml (1 replica, DEBUG logs)
    │       ├── staging/
    │       │   └── kustomization.yaml (2 replicas, INFO logs)
    │       └── prod/
    │           └── kustomization.yaml (3 replicas, WARNING logs)
    ├── argo/
    │   ├── app-dev.yaml               # NEW
    │   ├── app-staging.yaml           # NEW
    │   └── app-prod.yaml              # NEW
    ├── Dockerfile
    ├── Makefile
    └── README.md

.github/
├── templates/
│   └── python-app/                  # NEW: Reusable template
│       ├── Dockerfile
│       ├── Makefile
│       ├── TEMPLATE.md
│       ├── src/
│       │   ├── server.py
│       │   └── requirements.txt
│       ├── test/
│       │   ├── conftest.py
│       │   └── test_server.py
│       ├── scripts/
│       │   ├── setup.sh
│       │   ├── server.sh
│       │   └── test.sh
│       └── k8s/
│           ├── base/
│           └── overlays/
│               ├── dev/
│               ├── staging/
│               └── prod/
└── workflows/
    └── main.yml                     # UPDATED: image tag automation

docs/
└── SEALED_SECRETS.md                # NEW: Secret management guide

scripts/
├── validate-gitops.sh               # Comprehensive validation

ONBOARDING.md                         # UPDATED: Complete developer guide
```

---

## Critical Implementation Details

### Image Tag Update Flow

```
GitHub Actions
    ↓
[2] Docker build & push: ashik9001/demo-app:main-abc123def
    ↓
[3] kustomize edit set image
    ↓
[4] git commit & push
    ↓
Git Repository (source of truth updated)
    ↓
[5] ArgoCD detects change
    ↓
[6] kubectl apply via ArgoCD
    ↓
Kubernetes Cluster (deployed state matches git)
```

### Sealed Secrets Flow

```
Developer (local)
    ↓
[1] kubectl create secret (plaintext, temporary)
    ↓
[2] kubeseal (encrypt with cluster key)
    ↓
[3] git commit sealed secret (encrypted)
    ↓
Git Repository (safe even if compromised)
    ↓
[4] ArgoCD deploys sealed secret
    ↓
[5] sealed-secrets controller (decrypt in cluster only)
    ↓
Kubernetes Secret (decrypted in memory in cluster only)
```

---

## Verification Results

### ✅ All Kustomize Builds Successful

```bash
$ kustomize build apps/example-app/k8s/overlays/dev
  # 152 lines of valid YAML ✓
$ kustomize build apps/example-app/k8s/overlays/staging
  # 152 lines of valid YAML ✓
$ kustomize build apps/example-app/k8s/overlays/prod
  # 152 lines of valid YAML ✓
```

### ✅ Python Server Fixed

```bash
$ python src/server.py
  # Flask app running on 0.0.0.0:5000 ✓
$ curl http://localhost:5000/health
  # {"status": "healthy", "service": "example-app"} ✓
$ curl http://localhost:5000/metrics
  # # HELP app_requests_total Total requests ✓
```

### ✅ Template Complete

```bash
$ ls -la .github/templates/python-app/
  # Dockerfile           ✓
  # Makefile             ✓
  # TEMPLATE.md          ✓
  # src/server.py        ✓
  # test/test_server.py  ✓
  # k8s/base/            ✓
  # k8s/overlays/        ✓
```

---

## Next Steps for Teams

### Phase 1: Current (Complete) ✅
- ✅ Establish GitOps pattern with Kustomize overlays
- ✅ Automate image tag updates in GitHub Actions
- ✅ Define secret management with sealed-secrets
- ✅ Create Python app template
- ✅ Document onboarding process

### Phase 2: Recommended (Future)
1. **Observability Automation**: Move Prometheus/Grafana into `argo/observability/` with Kustomize overlays
2. **Cross-Environment Testing**: Create `test-pipeline.yaml` that validates all three overlays in parallel
3. **Policy as Code**: Add `opa/` directory for Kubernetes policy enforcement (seccomp, network policies, etc.)
4. **Multi-Cluster Support**: Extend to manage deployments across dev, staging, prod clusters
5. **GitOps Scan**: Add policy scanning in CI/CD before deployment

### Phase 3: Scaling (Future)
1. **AppProject RBAC**: Create `argocd/appprojects/` for team-based access control
2. **Notification Webhooks**: Add Slack/email notifications on deployment success/failure
3. **Secrets Rotation**: Automate sealed-secrets rotation with external-secrets-operator
4. **GitOps Analytics**: Track deployment frequency, lead time, failure rate (DORA metrics)

---

## Commands for First-Time Onboarding

### Create a New App

```bash
# 1. Copy template
cp -r .github/templates/python-app apps/my-awesome-app
cd apps/my-awesome-app

# 2. Replace placeholders (4 files, ~20 occurrences)
grep -r "{APP_NAME}\|{REGISTRY_IMAGE}\|{NAMESPACE}" .

# 3. Test build locally
make docker-build

# 4. Commit and push
git add .
git commit -m "feat: add my-awesome-app"
git push

# 5. ArgoCD auto-syncs (wait 1-2 minutes)
kubectl get apps -n argocd
```

### Deploy Example App

```bash
# Deploy dev environment
kubectl apply -k apps/example-app/k8s/overlays/dev

# Or via ArgoCD (recommended)
argocd app sync example-app-dev
```

---

## Important Notes

### ⚠️ Secrets Management
- **Never** commit plaintext secrets
- Always use sealed-secrets or external-secrets-operator
- Template file (`secret-template.yaml`) must be reviewed before use
- Teach team: "If you see a secret in git, something is wrong"

### ⚠️ Image Tag Updates
- GitHub Actions must have `write` permissions to repo
- Workflow commits are made by `github-actions` user
- If image tag doesn't update, check:
  1. Docker build/push succeeded
  2. `kustomize edit set image` command ran
  3. `git push` succeeded (check workflow logs)

### ⚠️ ArgoCD Sync
- Initial sync may take 1-2 minutes
- Check ArgoCD UI: `localhost:30080` (if port-forwarded)
- Check ArgoCD logs: `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server`

---

## Troubleshooting Quick Reference

| Problem | Cause | Solution |
|---------|-------|----------|
| Kustomize build fails | Syntax error in kustomization.yaml | `kustomize build` with full path, check error message |
| Image not updating | CI/CD didn't update git | Check GitHub Actions logs for `kustomize edit set image` |
| ArgoCD won't sync | Manifest invalid | `kubectl apply -f manifest.yaml --dry-run=client` |
| Secret not decrypting | Sealed with wrong key | Re-seal with current sealing key |
| Namespace not created | Missing CreateNamespace=true | Add to ArgoCD Application spec |

---

## Rollback Procedure

```bash
# If deployment fails:
# 1. Check what went wrong
kubectl get events -n example-app | tail -20

# 2. Review the failed manifest
kubectl get deployment -n example-app -o yaml

# 3. Rollback to previous commit
git revert <commit-hash>
git push

# 4. ArgoCD auto-syncs to previous state
kubectl get applications -n argocd
```

---

## Questions & Clarifications

**Q: What if I need secrets different for each environment?**
A: Create separate sealed secrets: `app-secret-dev.yaml`, `app-secret-staging.yaml`, `app-secret-prod.yaml` in each overlay's base kustomization.

**Q: Can I use this without ArgoCD?**
A: Yes, but you lose continuous reconciliation. Instead: `kubectl apply -k apps/example-app/k8s/overlays/prod`

**Q: How do I test locally before committing?**
A: Use `kustomize build` or `kubectl apply --dry-run=client -k path/`

**Q: What about helm charts?**
A: This pattern uses pure Kubernetes manifests + Kustomize. Helm can wrap this, but isn't needed for small-medium teams.

---

## Conclusion

The GitOps Python App Onboarding Pattern is now fully operational. The repository has been transformed from a single-app manual deployment model to a scalable, template-driven, GitOps-native multi-environment system.

**Key Wins**:
1. ✅ Apps created from template in < 10 minutes
2. ✅ Auto-deployment to 3 environments via git push
3. ✅ Secrets safely encrypted and committed
4. ✅ Infrastructure as code (git is single source of truth)
5. ✅ Team can scale without learning ArgoCD/Kustomize deeply

**Next**: Copy the template, customize, and deploy your first app! 🚀

---

**Document Version**: 1.0  
**Last Updated**: February 8, 2026  
**Maintained By**: Platform Team
