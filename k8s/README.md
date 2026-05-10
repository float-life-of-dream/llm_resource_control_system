# K8S Deploy Guide

This directory contains the base Kubernetes manifests used by the GitHub Actions deploy workflow.

## Image publishing

Images are published to GHCR by `.github/workflows/publish-images.yml`:

- `ghcr.io/<owner>/ai-control-backend`
- `ghcr.io/<owner>/ai-control-frontend`
- `ghcr.io/<owner>/ai-control-ollama-exporter`

Published tags:

- `latest` on `main`
- `sha-<commit>`

## GitHub Environment variables

Create GitHub Environments such as `staging` and `production`, then configure:

### Variables

- `FRONTEND_ORIGIN`
- `JWT_ACCESS_TTL_MINUTES`
- `JWT_REFRESH_TTL_DAYS`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_DEFAULT_TENANT_NAME`
- `BOOTSTRAP_DEFAULT_TENANT_SLUG`
- `PROMETHEUS_BASE_URL`
- `PROMETHEUS_TIMEOUT`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT`
- `OLLAMA_EXPORTER_TARGET_URL`
- `OLLAMA_EXPORTER_TIMEOUT`
- `OLLAMA_EXPORTER_PORT`
- `ELASTICSEARCH_BASE_URL`
- `ELASTICSEARCH_INDEX`
- `ELASTICSEARCH_TIMEOUT`
- `ANALYSIS_LOG_LIMIT_DEFAULT`
- `ANALYSIS_LOG_LIMIT_MAX`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`

### Secrets

- `KUBE_CONFIG`
  - base64 encoded kubeconfig
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `BOOTSTRAP_ADMIN_PASSWORD`
- `ELASTICSEARCH_USERNAME`
- `ELASTICSEARCH_PASSWORD`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `GHCR_USERNAME`
- `GHCR_TOKEN`

## CI/CD flow

Pull requests to `main` run `.github/workflows/ci.yml`. The CI workflow validates:

- backend tests
- frontend tests and production build
- Docker image builds
- `docker compose config`
- `kubectl kustomize k8s`

After CI succeeds on `main`, `.github/workflows/publish-images.yml` publishes GHCR images with `latest` and `sha-<commit-sha>` tags.

## Deployment

Run `.github/workflows/deploy-k8s.yml` manually with:

- `environment`: `staging` or `production`
- `namespace`: target namespace, default `ai-monitor`
- `image_tag`: `latest` or a published `sha-...` tag

The workflow will:

- ensure the namespace exists
- create/update the GHCR pull secret
- create/update ConfigMap and Secret from GitHub Environment values
- apply the base manifests
- set backend/frontend images to the requested tag
- set the ollama-exporter image to the requested tag
- wait for backend, frontend, ollama-exporter, ollama, and postgres rollout completion
- print a pod/service deployment summary

## Prometheus stack

The default `kustomization.yaml` now includes:

- `prometheus`
- `node-exporter`
- `ollama-exporter`
- `ollama`
- `backend`
- `frontend`
- `postgres`

GPU metrics remain optional. To enable them, apply:

- `k8s/dcgm-exporter-daemonset.yaml`
- `k8s/dcgm-exporter-service.yaml`

Example:

```bash
kubectl apply -n ai-monitor -f k8s/dcgm-exporter-daemonset.yaml
kubectl apply -n ai-monitor -f k8s/dcgm-exporter-service.yaml
```

Metric dependencies:

- CPU / memory / disk: `node-exporter`
- GPU: `dcgm-exporter`
- App / HTTP / analysis metrics: backend `/metrics`
- Loaded Ollama models and proxied inference metrics: `ollama-exporter`

## Model monitor

The model monitor page uses backend APIs under `/api/model-monitor/*`. Backend reads model metrics from Prometheus, while `ollama-exporter` scrapes `OLLAMA_EXPORTER_TARGET_URL` through Ollama `/api/ps` and `/api/show`.

The base manifests include an in-cluster Ollama StatefulSet exposed as `http://ollama:11434`. For inference latency, throughput, concurrency, tokens/sec, and chat traffic to be counted, Ollama requests must go through `ollama-exporter` at `http://ollama-exporter:9500`. The default backend `OLLAMA_BASE_URL` is set to that service.

Pull the configured model after first deployment:

```bash
kubectl exec -n ai-monitor statefulset/ollama -- ollama pull llama3.1:8b
```

## Elasticsearch logs

The logs page uses backend APIs under `/api/logs/*` and connects to an external Elasticsearch endpoint through:

- `ELASTICSEARCH_BASE_URL`
- `ELASTICSEARCH_INDEX`
- `ELASTICSEARCH_TIMEOUT`
- `ELASTICSEARCH_USERNAME`
- `ELASTICSEARCH_PASSWORD`

The base manifests do not deploy Elasticsearch, Kibana, or Logstash. Configure the external endpoint in the generated `ai-monitor-config` ConfigMap and credentials in `ai-monitor-secrets`.

Logs must contain `tenant_id` or `tenant.id` so the backend can enforce token-scoped tenant isolation.
