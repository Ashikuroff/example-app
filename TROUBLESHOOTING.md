# Troubleshooting Guide

Common issues and solutions when using the GitOps multi-app pattern.

## Kustomize Issues

### "error: accumulating resources: accumulating resource with Key: ..."

**Cause**: Duplicate resource names or missing resources referenced in base.

**Solution**:
```bash
# Verify kustomize can build without errors
kustomize build apps/my-app/k8s/overlays/dev

# Check that all referenced resources exist
ls apps/my-app/k8s/base/
# Should include: deployment.yaml, service.yaml, configmap.yaml, namespace.yaml
```

### "error: imageTags.newName not a string"

**Cause**: Malformed `images` field in kustomization.yaml.

**Solution**: Verify format in your `k8s/base/kustomization.yaml`:
```yaml
images:
- name: docker.io/username/imagename    # Must match exactly
  newName: docker.io/username/imagename
  newTag: latest
```

### Image tag not updating in kustomization.yaml

**Cause**: GitHub Actions workflow failed or didn't run.

**Solution**:
1. Check GitHub Actions logs: Go to repo → "Actions" tab
2. Verify secrets are set:
   - `DOCKER_USERNAME` - required
   - `DOCKER_PASSWORD` - required
   - `GITHUB_TOKEN` - automatically provided
3. Check workflow only runs on `main` or `staging` branches:
   ```yaml
   if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/staging')
   ```

## ArgoCD Issues

### ArgoCD Application won't sync

**Check 1**: Verify Application exists:
```bash
kubectl get applications -n argocd
kubectl describe application my-app-dev -n argocd
```

**Check 2**: Verify git repo is accessible:
```bash
# Check if ArgoCD can reach the repo URL
kubectl logs -f argocd-repo-server -n argocd | grep "my-repo"
```

**Check 3**: Verify path exists in git:
```bash
git ls-remote --heads https://github.com/YOUR_ORG/YOUR_REPO refs/heads/HEAD
# Then check if apps/my-app/k8s/overlays/dev/ exists
```

**Check 4**: Check for YAML syntax errors:
```bash
# Manually build the overlay to check for errors
kustomize build apps/my-app/k8s/overlays/dev

# If error, fix and commit to git
git add .
git commit -m "fix: kustomize syntax error"
git push origin main
```

### ArgoCD shows error: "spec.source.path: not found"

**Cause**: The path in Application CR doesn't exist in the git repo.

**Solution**: 
```bash
# Verify path structure matches exactly
# apps/my-app/k8s/overlays/dev/ must exist
git ls-tree -r origin/main --name-only | grep "apps/my-app"

# If missing, create directory
mkdir -p apps/my-app/k8s/overlays/dev
echo "path: apps/my-app/k8s/overlays/dev exists" > apps/my-app/k8s/overlays/dev/.placeholder

git add .
git commit -m "feat: add app structure"
git push origin main
```

### ArgoCD sync hangs or keeps retrying

**Check 1**: Pod creation errors:
```bash
kubectl describe pod -n my-app
kubectl logs -n my-app <pod-name>
```

**Check 2**: Secret decryption failing (sealed-secrets):
```bash
# Check if sealed-secrets operator is running
kubectl get pods -n kube-system | grep sealed

# Verify secret is sealed for this cluster:
kubectl get secret -n my-app -o yaml | grep 'kind: SealedSecret'
```

**Check 3**: Resource limits causing crashes:
```bash
kubectl top pods -n my-app
kubectl describe pod <pod-name> -n my-app
```

## Image & Docker Issues

### Docker build fails locally

**Cause**: Missing dependencies or Python version mismatch.

**Solution**:
```bash
# Build with verbose output
docker build -t my-app:latest --target prod . -v

# If pip install fails, check requirements.txt:
# - Pin versions (no wildcards)
# - Check specific Python version
# - Test locally first: pip install -r src/requirements.txt
```

### Image not found in Docker Hub after publish

**Cause**: GitHub Actions workflow failed to push.

**Solution**:
1. Check Actions logs for `docker/build-push-action` errors
2. Verify Docker Hub credentials haven't expired:
   ```bash
   # Regenerate Docker Hub access token
   # Update DOCKER_PASSWORD secret in repo settings
   ```
3. Verify image name matches:
   ```yaml
   env:
     IMAGE_NAME: ${{ secrets.DOCKER_USERNAME }}/my-app
   ```

### "no such file or directory" when building Docker image

**Cause**: Dockerfile references files that don't exist.

**Solution**: Check Dockerfile paths are relative to repo root:
```dockerfile
COPY ./src/requirements.txt /work/requirements.txt  # Good ✓
COPY src/requirements.txt /work/requirements.txt    # Also OK ✓
COPY requirements.txt /work/requirements.txt        # Wrong ✗
```

## Secrets Issues

### Sealed secret won't decrypt in pod

**Cause**: Secret sealed with wrong sealing key or on different cluster.

**Solution**:
```bash
# Reseal with correct cluster's sealing key
kubectl get secret my-app-secret -o yaml | kubeseal -f - -w secret.yaml

# Or, if this is a new cluster, get the public key:
kubectl -n kube-system get secret sealed-secrets-key -o jsonpath='{.data.tls\.crt}' | base64 -d

# Then on dev machine, reseal for each cluster
```

### Sealed secret error: "Sealing key is not available"

**Cause**: Sealed-secrets operator not installed or key missing.

**Solution**:
```bash
# Install sealed-secrets operator
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Wait for it to start and generate keys
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=sealed-secrets \
  -n kube-system --timeout=60s
```

### Plaintext secret committed to git

**URGENT - DO NOT PROCEED UNTIL FIXED**

```bash
# 1. Immediately rotate credentials (API keys, DB passwords)
# 2. Remove from git history:
git rm --cached apps/my-app/k8s/base/secret.yaml
git commit -m "fix: remove plaintext secret from git"
git push origin main

# 3. Force history rewrite (advanced - use with caution):
# See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

# 4. Create sealed secret properly
```

## Pod Crashing Issues

### Pod in CrashLoopBackOff

**Check 1**: Recent pod logs:
```bash
kubectl logs -n my-app --tail=50 deployment/my-app --previous
```

**Check 2**: Describe pod for events:
```bash
kubectl describe pod -n my-app <pod-name>
```

**Check 3**: Common causes:
- Missing ConfigMap: `kubectl get configmap -n my-app`
- Missing Secret: `kubectl get secret -n my-app`
- Wrong image name: `kubectl get deployment -n my-app -o yaml | grep image:`
- Port already in use: App listening on wrong port

**Solution Example** (missing ConfigMap):
```bash
# ConfigMap referenced but not created
# Check your kustomization.yaml includes configmap.yaml:
cat apps/my-app/k8s/base/kustomization.yaml | grep configmap.yaml

# If missing, add it:
resources:
  - configmap.yaml
  - deployment.yaml
  - service.yaml

git add .
git commit -m "fix: add missing configmap to kustomization"
git push origin main
```

## Networking Issues

### Service not accessible from pod

**Check 1**: Service exists:
```bash
kubectl get svc -n my-app
```

**Check 2**: DNS resolution works:
```bash
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
nslookup my-app.my-app.svc.cluster.local
```

**Check 3**: Pod has correct port exposed:
```bash
kubectl exec -it deployment/my-app -n my-app -- netstat -tuln | grep 5000
```

### Can't reach app from outside cluster

**Solution**: Use port-forward for testing:
```bash
kubectl port-forward -n my-app svc/my-app 5000:80
curl http://localhost:5000/
```

To expose externally, add Ingress:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  namespace: my-app
spec:
  rules:
  - host: my-app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
```

## Resource Issues

### Pod stuck in Pending

**Cause**: Not enough cluster resources or node selector issues.

**Solution**:
```bash
# Check node resources
kubectl top nodes
kubectl describe nodes

# Check pod resource requests
kubectl describe pod -n my-app <pod-name>

# If requesting more than available, update deployment-patch.yaml:
resources:
  requests:
    memory: "64Mi"    # Reduce from 128Mi
    cpu: "100m"       # Reduce from 250m
  limits:
    memory: "128Mi"
    cpu: "250m"

git add .
git commit -m "fix: reduce resource requests"
git push origin main
```

## Monitoring Issues

### Prometheus not scraping metrics

**Check 1**: Pod annotations:
```bash
kubectl get pods -n my-app -o jsonpath='{.items[*].metadata.annotations}' | jq .
# Should look like:
# "prometheus.io/path": "/metrics"
# "prometheus.io/port": "5000"
# "prometheus.io/scrape": "true"
```

**Check 2**: Metrics endpoint responds:
```bash
kubectl port-forward deployment/my-app 5000:5000
curl http://localhost:5000/metrics
# Should return Prometheus format text
```

**Check 3**: Prometheus targets page shows pod as UP:
- Access Prometheus UI: `http://prometheus-service:9090/targets`
- Look for your pod in targets list
- Should show "UP" status

### High memory usage in pods

**Check**: Memory leaks in app or resource limits too low:
```bash
# Check current usage
kubectl top pod -n my-app

# If consistently growing, may be memory leak
# Increase limit in deployment-patch.yaml:
limits:
  memory: "256Mi"  # Increase from 128Mi

# Or profile app with memory debugger
```

## Getting Help

If issue not listed here:

1. **Check logs** - most information is there:
   ```bash
   kubectl logs -f deployment/my-app -n my-app
   kubectl describe pod -n my-app <pod-name>
   ```

2. **Check events**:
   ```bash
   kubectl get events -n my-app --sort-by='.lastTimestamp'
   ```

3. **Validate YAML**:
   ```bash
   # Manually validate all manifests
   kustomize build apps/my-app/k8s/overlays/dev | kubectl apply --dry-run=client -f -
   ```

4. **Check GitHub Actions logs** for CI/CD issues

5. **Review application code** - check for environment variable usage mismatches

---

**Still stuck?** Open an issue with:
- Pod logs (`kubectl logs ...`)
- Describe output (`kubectl describe pod ...`)
- Kustomize build output
- GitHub Actions workflow logs
