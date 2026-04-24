# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Flask)
- `cd backend && pip install -r requirements.txt` — install dependencies
- `cd backend && python run.py` — start dev server on :5000
- `cd backend && pytest` — run all backend tests
- `cd backend && pytest tests/test_monitor_api.py -k test_overview` — single test

### Frontend (Vue 3 + Vite)
- `cd frontend && npm install` — install dependencies
- `cd frontend && npm run dev` — start dev server on :5173
- `cd frontend && npm run build` — type-check + production build
- `cd frontend && npm run test` — run vitest tests
- `cd frontend && npx vitest run src/__tests__/monitor.test.ts` — single test file

### Docker
- `docker compose up --build` — full stack (frontend :8080, backend :5000, postgres :5432)

### Kubernetes
- `kubectl apply -f k8s/` — deploy all manifests

## Architecture

### Data flow
```
Prometheus  <--  Backend (Flask :5000)  <--  Frontend (Vue 3 :5173)
                        |
                   PostgreSQL (reserved, not in main flow)
```

### Backend structure
- **Factory pattern** — `app/__init__.py` creates the Flask app via `create_app()`, registers CORS, flask-smorest API, and blueprints
- **API layer** — `app/api/` contains flask-smorest Blueprints with MethodView classes. Request/response validation via Marshmallow schemas (`app/schemas/`). Swagger auto-generated at `/api/docs/`
- **Service layer** — `MonitorService` in `app/services/monitor_service.py` maps metric keys ("cpu", "memory", "disk", "gpu") to PromQL queries via `METRIC_CONFIG`, wraps `PrometheusClient` for query/query_range calls
- **Prometheus client** — `PrometheusClient` in `app/services/prometheus_client.py` is a thin dataclass wrapper around `requests.get` to Prometheus HTTP API. Raises `PrometheusClientError` on timeout/failure/error status
- **Error handling** — API endpoints catch `PrometheusClientError` and return 502 with the error message

### Frontend structure
- **Entry** — `main.ts` creates the Vue app with Pinia, Vue Router, Element Plus
- **Router** — single route (`/`) rendering `DashboardView`
- **State** — Pinia store (`stores/monitor.ts`) manages `range`, `step`, `overview`, `seriesMap`, `isLoading`, `error`. `loadDashboard()` fetches overview + all 4 metrics' timeseries in parallel
- **API** — `api/monitor.ts` wraps axios calls; `api/http.ts` creates axios instance with `VITE_API_BASE_URL` (defaults to `/api`), 8s timeout
- **Types** — `types/monitor.ts` defines common types: `MetricKey`, `RangeKey`, `StepKey`, `OverviewItem`, `TimeseriesPoint`
- **Components** — `StatCard` (overview metric), `MonitorChart` (ECharts line chart with lazy component registration), `PageHeader`, `AdminLayout` (dark-themed shell with grid background)

### Infrastructure
- **Docker Compose** — frontend (nginx serving static build), backend (gunicorn), postgres (16-alpine, with persistent volume)
- **K8s** — separate deployments/services for frontend, backend, postgres; configmap for env vars; secrets example
- **Nginx** — configured with `proxy_buffering off` for future SSE/streaming support
- **No auth** — v1 has no authentication

### Key conventions
- Python: `from __future__ import annotations` throughout
- Backend config via env vars with defaults (Prometheus URL, Postgres connection)
- Frontend: Element Plus `el-segmented` for range switcher, ECharts registered per-component (not globally)
- Vite proxies `/api` to `localhost:5000` in dev mode
