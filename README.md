# AI Resource Monitor

`AI-control` is a Vue 3 + Flask + PostgreSQL monitoring console for AI runtime resources. It supports multi-tenant login, tenant-level RBAC, Prometheus-based host metrics, Ollama model monitoring, and Ollama-assisted log/metric analysis.

## Architecture

```text
AI-control/
|-- backend/              # Flask API, auth, RBAC, monitor APIs, analysis APIs
|-- frontend/             # Vue 3 + Vite + Element Plus + ECharts
|-- mock-prometheus/      # Prometheus API mock for local demo mode
|-- ollama-exporter/      # Ollama metadata and inference metric exporter
|-- infra/prometheus/     # Prometheus scrape config
|-- k8s/                  # Kubernetes manifests
|-- docker-compose.yml
|-- docker-compose.mock.yml
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
- Optional mock Prometheus mode for stable local demo data.
- Optional GPU metrics through `dcgm-exporter`.
- Ollama model monitor page at `/models`.
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

## Mock Demo Mode

Mock mode replaces the backend Prometheus source with `mock-prometheus`.

```bash
docker compose -f docker-compose.yml -f docker-compose.mock.yml up -d --build
```

This mode is for stable host-monitor demo data. It does not mock Ollama model monitoring. The model monitor still depends on a real Ollama exporter and a real or reachable Ollama instance.

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
- `GET /api/monitor/timeseries?metric=cpu|memory|disk|gpu&range=1h|6h|24h&step=30s|1m`

Model monitor:

- `GET /api/model-monitor/overview`
- `GET /api/model-monitor/models`
- `GET /api/model-monitor/timeseries?metric=request_rate|latency|concurrency&range=1h|6h|24h&step=30s|1m`

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

Mock Prometheus tests:

```bash
cd mock-prometheus
pytest
```

Docker-based backend test example:

```bash
docker run --rm -v "%cd%/backend/tests:/app/tests:ro" ai-control-backend sh -lc "PYTHONPATH=/app pytest tests -q"
```

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

Restart Prometheus so it reloads `infra/prometheus/prometheus.yml`:

```bash
docker compose restart prometheus
```

Then open:

```text
http://127.0.0.1:9090/targets
```
