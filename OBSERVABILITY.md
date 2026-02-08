# Observability Setup Guide

This guide covers Prometheus monitoring and logging for the GitOps-managed Python applications.

## Prometheus Configuration

### Application Metrics

All Python applications expose metrics at `/metrics` endpoint:

- **app_requests_total**: Counter tracking requests by method, endpoint, and status
- **app_request_duration_seconds**: Histogram tracking request latency
- **Standard Python metrics**: Available from prometheus_client library

### Automatic Scraping

Deployments are annotated for automatic Prometheus scraping:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "5000"
  prometheus.io/path: "/metrics"
```

### Configure Prometheus to Scrape Kubernetes Pods

If using Prometheus Operator or kube-prometheus-stack:

```bash
# Install with Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

If using manual Prometheus:

```yaml
# prometheus-config.yaml - update scrape config
global:
  scrape_interval: 15s

scrape_configs:
- job_name: 'kubernetes-pods'
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: true
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
    action: replace
    target_label: __metrics_path__
    regex: (.+)
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
    action: replace
    regex: ([^:]+)(?::\d+)?;(\d+)
    replacement: $1:$2
    target_label: __address__
```

## Grafana Dashboards

### Create Dashboard for App Metrics

1. **Add Prometheus Data Source**:
   - URL: `http://prometheus:9090`
   - Access: Server

2. **Create Dashboard Panel** (Request Rate):
   ```
   rate(app_requests_total[5m])
   ```

3. **Create Dashboard Panel** (Request Latency - p95):
   ```
   histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[5m]))
   ```

4. **Create Dashboard Panel** (Error Rate):
   ```
   rate(app_requests_total{status=~"5.."}[5m])
   ```

## Logging

### Structured Logging

Applications use Python's standard logging with timestamps:

```python
logger.info("Message here")  # app sends to stdout
```

### View Logs

```bash
# Real-time logs from deployment
kubectl logs -f deployment/dev-my-app -n my-app

# Last N lines
kubectl logs --tail=100 deployment/dev-my-app -n my-app

# All pods across environment
kubectl logs -f -l app=my-app -n my-app --all-containers=true
```

### Log Levels by Environment

- **dev**: DEBUG - detailed logging for troubleshooting
- **staging**: INFO - standard operational logging
- **prod**: WARNING - only important events

Configured automatically in overlay ConfigMap:

```yaml
configMapGenerator:
- name: my-app-config
  literals:
  - log_level=DEBUG  # or INFO, WARNING
```

## Alerting (Optional)

### PrometheusRule Example

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: app-alerts
  namespace: monitoring
spec:
  groups:
  - name: app
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: rate(app_requests_total{status=~"5.."}[5m]) > 0.05
      for: 5m
      annotations:
        summary: "High error rate detected"
    
    - alert: HighLatency
      expr: histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[5m])) > 1
      for: 10m
      annotations:
        summary: "Request latency p95 > 1s"
```

## Health Checks

### Kubernetes Probes

Deployments include health check endpoints:

- **Liveness Probe**: `GET /` (app is running)
- **Readiness Probe**: `GET /health` (app is ready for traffic)

Both return HTTP 200 when healthy.

### Manual Health Check

```bash
# Check if app is healthy
kubectl exec -it deployment/my-app -c my-app -- \
  curl -s http://localhost:5000/health | jq .
```

## Observability Troubleshooting

### Issue: Prometheus not scraping metrics

**Solution**: Verify pod annotations:
```bash
kubectl get pods -n my-app -o jsonpath='{.items[*].metadata.annotations}' | jq .
```

### Issue: Missing metrics in Prometheus

1. Check if metrics endpoint responds:
   ```bash
   kubectl port-forward deployment/my-app 5000:5000
   curl http://localhost:5000/metrics
   ```

2. Verify Prometheus scrape targets:
   - Access Prometheus UI at `http://prometheus:9090/targets`
   - Check if pod target is listed and "UP"

### Issue: High error rates or latency

1. Check pod logs:
   ```bash
   kubectl logs -f deployment/my-app -n my-app
   ```

2. Check resource limits:
   ```bash
   kubectl describe pod <pod-name> -n my-app
   ```

3. Check event history:
   ```bash
   kubectl get events -n my-app --sort-by='.lastTimestamp'
   ```

---

See [ONBOARDING.md](../ONBOARDING.md) for app-specific setup.
