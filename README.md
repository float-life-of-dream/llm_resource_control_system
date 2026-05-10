# AI Resource Monitor

`AI-control` is a Vue 3 + Flask + PostgreSQL monitoring console for AI runtime resources. It supports multi-tenant login, tenant-level RBAC, Prometheus-based host metrics, Ollama model monitoring, Elasticsearch log search, and Ollama-assisted log/metric analysis.

## Architecture

```text
AI-control/
|-- backend/              # Flask API, auth, RBAC, monitor APIs, analysis APIs
|-- frontend/             # Vue 3 + Vite + Element Plus + ECharts
|-- ollama-exporter/      # Ollama metadata and inference metric exporter
|-- infra/prometheus/     # Prometheus scrape config
|-- k8s/                  # Kubernetes manifests
|-- docker-compose.yml
|-- docker-compose.gpu.yml
`-- .env.example
```

## Core Features

- Multi-tenant login with `tenantSlug + email + password`.
- RBAC roles:
  - System level: `system_admin`
  - Tenant level: `owner / admin / viewer`
- Protected monitor APIs. Users must log in before accessing monitor data.
- Built-in Prometheus collector stack for local host metrics.
- Optional GPU metrics through `dcgm-exporter`.
- Ollama chat page at `/chat`.
- Ollama model monitor page at `/models`.
- Prometheus status page at `/prometheus`.
- Elasticsearch logs page at `/logs`.
- Ollama + Elasticsearch powered AI analysis panel.

## Default Account

The application bootstraps a default tenant and system admin from environment variables.

- Tenant slug: `default`
- Admin email: `admin@example.local`
- Admin password: `ChangeMe123!`

Change these values outside local development.

## Local Deployment

Copy the environment example first:

```bash
cp .env.example .env
```

Start the default local stack:

```bash
docker compose up -d --build
```

Default URLs:

- Frontend: `http://127.0.0.1:8080`
- Backend: `http://127.0.0.1:5000`
- Prometheus: `http://127.0.0.1:9090`
- Ollama exporter: `http://127.0.0.1:9500`
- PostgreSQL: `127.0.0.1:5432`

If only some monitor services are missing, start them directly:

```bash
docker compose up -d node-exporter ollama-exporter prometheus
```

## Prometheus Monitoring

The default Compose stack includes:

- `prometheus`
- `node-exporter`
- `backend /metrics`
- `ollama-exporter /metrics`

Prometheus config lives in:

```text
infra/prometheus/prometheus.yml
```

Main host metrics:

- CPU, memory, disk: `node-exporter`
- Backend HTTP and analysis metrics: backend `/metrics`
- Ollama model and inference metrics: `ollama-exporter`
- GPU metrics: optional `dcgm-exporter`

The Prometheus status page is available at:

```text
/prometheus
```

It shows Prometheus connectivity, scrape target health, and the backend-supported metric catalog. The backend deliberately does not expose a raw PromQL proxy; frontend pages can only request fixed metric keys.

## Ollama Model Monitor

The model monitor page is available at:

```text
/models
```

It shows:

- request rate
- average latency
- active requests
- loaded model count
- loaded model list
- parameter size
- quantization
- context window
- memory usage

The exporter target defaults to:

```env
OLLAMA_EXPORTER_TARGET_URL=http://host.docker.internal:11434
```

For model metadata to appear, Ollama must be running on the host and at least one model must be loaded. If no model is loaded, the page will show `0` values and an empty model list.

The backend default Ollama URL is:

```env
OLLAMA_BASE_URL=http://ollama-exporter:9500
```

This routes backend Ollama analysis requests through the exporter so request rate, latency, concurrency, and tokens-per-second can be counted.

## Ollama Chat

The chat page is available at:

```text
/chat
```

Chat requests are sent to the backend and streamed to the browser using SSE. The backend calls:

```env
OLLAMA_BASE_URL=http://ollama-exporter:9500
```

Keep this value pointed at `ollama-exporter` if you want `/models` to show chat request rate, latency, concurrency, error rate, and tokens/sec. Pointing the backend directly at Ollama will still allow chat, but model monitor inference metrics will not include those requests.

## Elasticsearch Logs

The logs page is available at:

```text
/logs
```

The backend connects to an external Elasticsearch endpoint. This repository does not start Elasticsearch, Kibana, or Logstash by default.

Required environment variables:

```env
ELASTICSEARCH_BASE_URL=http://localhost:9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_INDEX=logs-*
ELASTICSEARCH_TIMEOUT=10
```

Logs must include a tenant field so the API can enforce token-scoped tenant isolation. Supported tenant fields are:

- `tenant_id`
- `tenant.id`

Recommended log fields:

- `@timestamp`
- `log.level` or `level`
- `service.name` or `service`
- `message`
- `trace.id` or `traceId`
- `host.name` or `host`

The frontend never sends raw Elasticsearch DSL. It only calls the backend logs API with whitelisted filters.

## GPU Metrics

GPU metrics are optional and require NVIDIA runtime support.

Start the GPU extension with:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

The GPU exporter exposes:

```text
dcgm-exporter:9400
```

GPU data appears in two places:

- Overview cards and GPU trend charts on `/`
- Device-level GPU table on `/`

The backend reads these DCGM metrics:

- `DCGM_FI_DEV_FB_USED`
- `DCGM_FI_DEV_FB_TOTAL`
- `DCGM_FI_DEV_GPU_UTIL`
- `DCGM_FI_DEV_GPU_TEMP`
- `DCGM_FI_DEV_POWER_USAGE`

## Key APIs

Auth:

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/auth/sessions`
- `DELETE /api/auth/sessions/{sessionId}`

Host monitor:

- `GET /api/monitor/overview`
- `GET /api/monitor/timeseries?metric=cpu|memory|disk|gpu|gpu_memory_used|gpu_memory_utilization|gpu_utilization|gpu_temperature|gpu_power_usage&range=1h|6h|24h&step=30s|1m`
- `GET /api/monitor/gpus`

Model monitor:

- `GET /api/model-monitor/overview`
- `GET /api/model-monitor/models`
- `GET /api/model-monitor/timeseries?metric=request_rate|latency|concurrency|tokens_per_second|error_rate|loaded_models&range=1h|6h|24h&step=30s|1m`

Prometheus status:

- `GET /api/prometheus/health`
- `GET /api/prometheus/targets`
- `GET /api/prometheus/metrics`

Chat:

- `POST /api/chat/sessions`
- `GET /api/chat/sessions`
- `GET /api/chat/sessions/{sessionId}`
- `POST /api/chat/sessions/{sessionId}/stream`
- `DELETE /api/chat/sessions/{sessionId}`

Logs:

- `GET /api/logs/search?range=1h&query=timeout&level=error&service=backend&limit=100`
- `GET /api/logs/summary?range=1h&query=timeout`
- `GET /api/logs/services?range=24h`

AI analysis:

- `POST /api/analysis/run`
- `GET /api/analysis/history`
- `GET /api/analysis/history/{analysisId}`

Tenant management:

- `GET /api/tenant`
- `PATCH /api/tenant`
- `GET /api/tenant/members`
- `POST /api/tenant/members`
- `PATCH /api/tenant/members/{membershipId}`
- `DELETE /api/tenant/members/{membershipId}`

System admin:

- `GET /api/system/tenants`
- `POST /api/system/tenants`
- `POST /api/system/tenants/{tenantId}/members`

## Tests

Backend tests:

```bash
cd backend
pytest
```

Frontend tests:

```bash
cd frontend
npm test
```

Docker-based backend test example:

```bash
docker run --rm -v "%cd%/backend/tests:/app/tests:ro" ai-control-backend sh -lc "PYTHONPATH=/app pytest tests -q"
```

## CI/CD

GitHub Actions uses a protected branch workflow:

- `CI` runs on pull requests to `main` and pushes to `main`.
- `CI` covers backend tests, mock Prometheus tests, frontend tests/build, Docker image builds, Docker Compose validation, and K8S manifest rendering.
- `Publish Images` runs only after `CI` succeeds on `main`, then publishes images to GHCR.
- `Deploy K8S` is manually dispatched against a GitHub Environment such as `staging` or `production`.

Published images:

- `ghcr.io/<owner>/ai-control-backend`
- `ghcr.io/<owner>/ai-control-frontend`
- `ghcr.io/<owner>/ai-control-ollama-exporter`

Published tags:

- `latest`
- `sha-<commit-sha>`

Required GitHub Environment secrets for deploy:

- `KUBE_CONFIG`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `BOOTSTRAP_ADMIN_PASSWORD`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `GHCR_USERNAME`
- `GHCR_TOKEN`
- `ELASTICSEARCH_USERNAME`
- `ELASTICSEARCH_PASSWORD`

`ELASTICSEARCH_USERNAME` and `ELASTICSEARCH_PASSWORD` may be empty if your Elasticsearch endpoint does not require basic auth.

## Troubleshooting

### `/api/model-monitor/overview` returns 502

The backend could not query Prometheus. Check that these services are running:

```bash
docker compose ps
```

Required services:

- `prometheus`
- `ollama-exporter`
- `backend`

Start missing services:

```bash
docker compose up -d node-exporter ollama-exporter prometheus
```

Verify:

```bash
curl http://127.0.0.1:9090/-/healthy
curl http://127.0.0.1:9500/health
```

### Model monitor shows empty data

Check that Ollama is running on the host:

```bash
curl http://127.0.0.1:11434/api/ps
```

If no model is loaded, run a model once:

```bash
ollama run llama3.1:8b
```

Then refresh `/models`.

## Kubernetes Deployment

The base K8S manifests include an in-cluster Ollama runtime:

- Service: `ollama:11434`
- StatefulSet: `ollama`
- Persistent volume claim: `ollama-data`

The backend still calls Ollama through `ollama-exporter`:

```env
OLLAMA_BASE_URL=http://ollama-exporter:9500
OLLAMA_EXPORTER_TARGET_URL=http://ollama:11434
```

After deploying to Kubernetes, pull a model into the Ollama pod before running analysis:

```bash
kubectl exec -n ai-monitor statefulset/ollama -- ollama pull llama3.1:8b
```

For local Docker Desktop Kubernetes:

```bash
kubectl apply -n ai-monitor -k k8s
kubectl get pods -n ai-monitor
```

### Prometheus target is missing

Open `/prometheus` after logging in to inspect target health from the application. The same data is available from the backend:

```bash
curl -H "Authorization: Bearer <access-token>" http://127.0.0.1:8080/api/prometheus/targets
```

If a target is missing, restart Prometheus so it reloads `infra/prometheus/prometheus.yml`:

```bash
docker compose restart prometheus
```

Then open:

```text
http://127.0.0.1:9090/targets
```

Expected jobs are:

- `backend`
- `node-exporter`
- `ollama-exporter`
- `dcgm-exporter` when GPU mode is enabled
