# Plan: GitOps Python App Onboarding Pattern

**TL;DR:** Transform the existing example-app into a templated, multi-environment GitOps pattern that future Python apps can follow. Establish directory conventions, automated image tag management, and Kustomize-based environment overlays. Maintain the current app as a working reference implementation while fixing critical gaps (image sync, secrets management) that would block new app adoption. Result: developers can copy a template, follow a checklist, and have a complete GitOps-managed Python app in minutes.

## Steps

### 1. Establish Repository Structure Pattern

- Create a clear `apps/` directory structure where each Python app gets a subdirectory
- Convert `argo/example-app/` into a reusable template pattern with placeholder names
- Document the expected layout: `apps/{app-name}/k8s/base/`, `apps/{app-name}/k8s/overlays/{dev,staging,prod}`
- Keep `src/` as reference; new apps will have their own app-specific source trees

### 2. Implement Automated Image Tag Updates (Critical)

- Migrate GitHub Actions workflow to use a tool (e.g., `kustomize set image`) or custom action to update image tags in kustomization files automatically
- Instead of hardcoding `deployment.yaml` images, move to `kustomization.yaml` with `images` field
- This breaks the manual sync bottleneck and enables true GitOps automation
- Document in `.github/workflows/` how image tags propagate to specific environments

### 3. Introduce Kustomize for Multi-Environment Support

- Create `apps/example-app/k8s/base/` with core manifests (deployment, service, configmap, secret templates)
- Create `apps/example-app/k8s/overlays/dev/`, `staging/`, `prod/` with `kustomization.yaml` defining environment-specific patches:
  - Replicas (1 dev, 2 staging, 3 prod)
  - Resource limits per environment
  - Image tags from CI/CD registry prefixes
  - ConfigMap values (log levels, feature flags)
- Update ArgoCD `app.yaml` to track overlays per environment (e.g., `argo/apps/example-app/k8s/overlays/prod`)

### 4. Define Secret Management Pattern

- Replace plaintext secret templates with a documented approach: either **sealed-secrets** or **external-secrets-operator**
- Create `apps/example-app/k8s/base/secret-sealed.yaml` as template (sealed-secrets chosen for simplicity in single-cluster context)
- Document the onboarding checklist: "Generate sealed secret for your app key using `kubeseal`"
- Prevent accidental plaintext secret commits

### 5. Create Python App Template (Boilerplate)

- Copy `Dockerfile`, `src/` structure, `test/`, `requirements.txt` into a reusable template directory
- Include Makefile pattern for `setup`, `test`, `build`, `deploy` targets
- Ensure all apps inherit patterns: health checks, Prometheus metrics, structured logging, non-root user
- Template placeholders: `{APP_NAME}`, `{REGISTRY_IMAGE}`, `{NAMESPACE}`, `{GITHUB_REPO}`

### 6. Update ArgoCD Multi-App Configuration

- Modify ArgoCD `install.yaml` to support AppProject RBAC per team or environment
- Create an umbrella `argo/root-app.yaml` or `apps/kustomization.yaml` that ArgoCD uses as single entry point
- Each new app's overlays registered automatically when committed to repo (path-matching)
- Enables adding apps without manual ArgoCD configuration changes

### 7. Document Onboarding Checklist

- Create `ONBOARDING.md` with step-by-step guide:
  1. Copy template to `apps/my-python-app/`
  2. Update placeholders in kustomize and k8s manifests
  3. Configure CI/CD workflow (image registry, DockerHub username)
  4. Generate sealed secret for credentials
  5. Create git branch + merge → ArgoCD auto-syncs
  6. Verify health checks and metrics in Prometheus
- Include troubleshooting section (common image tag errors, secret decryption failures)

### 8. Improve Observability & Testing Foundation

- Consolidate Prometheus + Grafana manifests into `argo/observability/` with Kustomize overlays
- Update `src/server.py` to fix Prometheus registry duplication bug
- Create `test/integration_test.py` for post-deployment validation (curl health endpoint, scrape metrics)
- Document coverage expectations and linting in CI

## Verification

- **Unit test**: Run existing tests on example-app to ensure refactoring doesn't break app logic
- **Kustomize validation**: `kustomize build apps/example-app/k8s/overlays/dev` outputs valid YAML for all environments
- **Image tag automation**: Simulate GitHub Actions push → verify image tag auto-updates in kustomization, ArgoCD detects change
- **Onboarding dry-run**: Create a second test Python app (e.g., `apps/test-app/`) using the template; verify it deploys via same GitOps pipeline
- **Secret encryption**: Verify sealed secrets decrypt only in cluster, fail outside it
- **Multi-environment**: Deploy to 3 different overlays in same cluster; confirm replica/resource differences apply correctly

## Decisions

- **Chosen**: Kustomize over Helm for overlay management (simpler for small team, no templating complexity)
- **Chosen**: Sealed-secrets over External Secrets Operator (lower operational burden, secrets stay in git)
- **Chosen**: Flatten single-app repo into multi-app pattern (`apps/{app-name}/`) rather than creating separate repos per app (keeps CI/CD, observability, & docs centralized)
- **Not included in scope**: Azure infrastructure/Bicep (preflight.sh exists but out of scope for this pattern); can be layered later
- **Not included**: Monitoring stack (Prometheus/Grafana) automation in phase 1; documented as post-deployment manual install, can be added to observability overlays in phase 2
