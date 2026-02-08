# Sealed Secrets Implementation

This guide explains how to use sealed-secrets for secure secret management in your GitOps workflow.

## Installation

Sealed-secrets is assumed to be installed in your cluster. If not, install it with:

```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml
```

## Sealing a Secret

1. **Create a temporary secret** (DO NOT commit this):
```bash
kubectl create secret generic example-app-secret \
  --from-literal=api_key='your-api-key' \
  --from-literal=database_url='postgres://...' \
  --dry-run=client -o yaml > /tmp/secret.yaml
```

2. **Seal the secret** (safe to commit):
```bash
kubeseal -f /tmp/secret.yaml -w apps/example-app/k8s/base/secret.yaml
```

3. **Cleanup**:
```bash
rm /tmp/secret.yaml
```

4. **Commit the sealed secret**:
```bash
git add apps/example-app/k8s/base/secret.yaml
git commit -m "chore: add sealed secret for example-app"
```

## Updating a Secret

To update a secret, repeat the sealing process:

```bash
kubectl create secret generic example-app-secret \
  --from-literal=api_key='new-api-key' \
  --dry-run=client -o yaml | kubeseal -f - -w apps/example-app/k8s/base/secret.yaml
```

## Using Sealed Secrets in Your Manifest

Sealed secrets are automatically decrypted by the controller when deployed. They appear as regular Kubernetes secrets inside the cluster.

Configure your deployment to use them:

```yaml
volumeMounts:
- name: secret-volume
  mountPath: /secrets/
  readOnly: true
volumes:
- name: secret-volume
  secret:
    secretName: example-app-secret
    defaultMode: 0400
```

## Troubleshooting

- **"sealing key not found"**: Ensure the sealing key is accessible. Run `kubeseal -f secret.yaml` to verify.
- **"cannot decrypt"**: The sealed secret was created with a different sealing key. Re-seal using the current key.
- **Local development**: Use plain secrets locally; seal only before committing to the repo.
