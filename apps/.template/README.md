# {APP_NAME} Python Application

A Python Flask application following the GitOps pattern for multi-environment Kubernetes deployment.

## Quick Start

### Local Development

```bash
# Set up Python environment
make setup

# Run tests
make test

# Build container image
make build

# Deploy to local Kubernetes (kind)
make deploy-dev
```

### Structure

- `src/server.py` - Main Flask application with Prometheus metrics
- `src/requirements.txt` - Python dependencies
- `test/` - Unit and integration tests
- `Dockerfile` - Multi-stage build (debug/prod targets)
- `k8s/` - Kubernetes manifests with Kustomize overlays

### Kubernetes Environments

- **dev**: Single replica, DEBUG logging, auto-synced by ArgoCD
- **staging**: 2 replicas, INFO logging, pre-prod validation
- **prod**: 3 replicas, WARNING logging, production deployment

### Health Checks

- Liveness: `GET /` (returns 200)
- Readiness: `GET /health` (returns 200)
- Metrics: `GET /metrics` (Prometheus format)

### Observability

- **Prometheus metrics** at `/metrics`:
  - `app_requests_total` - Request count by endpoint/status
  - `app_request_duration_seconds` - Request latency histogram
- **Structured logging** with timestamps and levels
- **Pod annotations** for automatic Prometheus scraping

---

See [../../ONBOARDING.md](../../ONBOARDING.md) for full onboarding guide.
