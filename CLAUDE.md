# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI‑control is an AI workload resource monitoring dashboard. It fetches CPU, memory, disk, and GPU metrics from a Prometheus instance and presents them in a Vue‑3 frontend via a Flask backend. The system is designed for Kubernetes‑native deployment but can be run locally with Docker Compose.

**Key characteristics:**
- Backend: Flask + Flask‑Smorest (OpenAPI) + Prometheus client
- Frontend: Vue 3 + Vite + Element Plus + ECharts, with Pinia state management
- Data flow: Frontend calls backend REST endpoints; backend queries Prometheus using configurable PromQL queries defined in `METRIC_CONFIG`
- No authentication in the first version; PostgreSQL is containerized but not yet integrated into the main flow

## Development Environment

### Environment variables
Copy `.env.example` to `.env` and adjust as needed. The most important variable is `PROMETHEUS_BASE_URL` (default `http://prometheus:9090`). The backend also expects PostgreSQL connection variables, though they are currently unused.

### Backend (Flask)
- **Run locally** (from `backend/`):
  ```bash
  python -m venv .venv
  .venv\Scripts\activate          # Windows
  source .venv/bin/activate       # Unix
  pip install -r requirements.txt
  python run.py
  ```
  Swagger UI will be available at `http://localhost:5000/api/docs/`.

- **Run tests** (pytest):
  ```bash
  cd backend
  python -m pytest tests/ -v
  ```
  To run a single test file: `python -m pytest tests/test_monitor_api.py -v`.

- **Docker build** (from project root):
  ```bash
  docker compose build backend
  ```

### Frontend (Vue 3)
- **Run locally** (from `frontend/`):
  ```bash
  npm install
  npm run dev
  ```
  Development server runs at `http://localhost:5173` with Vite proxying `/api` to `http://localhost:5000`.

- **Build for production**:
  ```bash
  npm run build
  ```

- **Run tests** (Vitest):
  ```bash
  npm test
  ```
  Tests are in `src/__tests__/`. To run a single test file: `npx vitest run src/__tests__/monitor.test.ts`.

- **Docker build**:
  ```bash
  docker compose build frontend
  ```

### Full stack with Docker Compose
```bash
docker compose up --build
```
- Frontend: `http://localhost:8080`
- Backend: `http://localhost:5000`
- PostgreSQL: `localhost:5432` (reserved for future use)

The Compose stack includes an nginx reverse proxy in the frontend container that forwards `/api` to the backend.

## Architecture Details

### Backend structure
- `run.py` – entry point that creates the Flask app via `create_app()`
- `app/__init__.py` – app factory, registers blueprints and CORS
- `app/api/` – REST endpoints (health, monitor) using Flask‑Smorest blueprints
- `app/services/` – business logic:
  - `prometheus_client.py` – thin wrapper around Prometheus HTTP API
  - `monitor_service.py` – transforms Prometheus results using `METRIC_CONFIG`
- `app/schemas/` – Marshmallow schemas for request/response validation and OpenAPI documentation
- `app/extensions/` – Flask‑Smorest API instance
- `app/config.py` – configuration loaded from environment variables

**Metric configuration:** `METRIC_CONFIG` in `monitor_service.py` defines the PromQL queries for each metric (cpu, memory, disk, gpu). Changes here affect both the overview and timeseries endpoints.

### Frontend structure
- `src/main.ts` – Vue app setup with Pinia, Element Plus, and router
- `src/views/DashboardView.vue` – main dashboard page; uses `AdminLayout`
- `src/stores/monitor.ts` – Pinia store that coordinates loading overview and timeseries data
- `src/api/monitor.ts` – thin wrapper around `http` client
- `src/api/http.ts` – Axios instance with configurable base URL (default `/api`)
- `src/components/` – reusable components:
  - `PageHeader.vue` – dashboard title and timestamp
  - `StatCard.vue` – displays a single metric value
  - `MonitorChart.vue` – ECharts time‑series graph
- `src/types/monitor.ts` – TypeScript interfaces for API responses

**Data flow:** `DashboardView` calls `store.loadDashboard()` on mount; the store fetches overview data, then concurrently fetches timeseries for all four metrics. The store holds `seriesMap` keyed by metric for easy access by chart components.

### Kubernetes deployment
Manifests are in `k8s/`. They assume a ConfigMap (`ai-monitor-config`) and Secret (`ai-monitor-secrets`) containing the same environment variables used in Docker Compose. The frontend service uses a NodePort (default 30080) and the backend uses ClusterIP.

### Important notes
- The backend expects a running Prometheus instance; the default URL points to `http://prometheus:9090`. For local development, you may need to adjust `PROMETHEUS_BASE_URL` in `.env`.
- PostgreSQL is included in the Docker Compose stack but is not yet used by the application. It is reserved for future extensions.
- The nginx configuration (`frontend/nginx/default.conf`) disables `proxy_buffering` to support future SSE/streaming endpoints.
- No linting or formatting tools are currently configured; only unit tests are set up.

## Git 协作协议 (强制性 PR 工作流)

作为本项目的执行 Agent，必须严格遵守以下 Git 协作协议，利用 CI 流水线保护 `main` 分支的稳定性。

### 1. 核心规则 (Golden Rules)
- **禁止直推**：严禁直接在 `main` 分支执行 `git push`。
- **分支隔离**：所有代码变更（包括文档更新）必须在 `feature/*` 或 `fix/*` 分支进行。
- **验证优先**：在建议合并前，必须确保本地或远程 CI 的 `build` 任务已成功运行。

### 2. 标准作业程序 (SOP)

**阶段一：环境对齐** — 在开始任何任务之前，必须同步主分支状态：
```bash
git checkout main
git pull origin main
```

**阶段二：功能分支开发**
1. 创建并切换分支（命名应具有语义化）：`git checkout -b feature/your-topic-name`
2. 执行修改。
3. 如果本项目包含 `mkdocs`，在提交前建议执行本地构建检查：`pip install -r requirements.txt && mkdocs build --strict`

**阶段三：提交与推送**
1. 提交信息须遵循约定式提交（Conventional Commits）：
   - `feat:` 新内容/新文章
   - `fix:` 修复错误
   - `docs:` 仅文档修改
   - `chore:` 配置更新
2. 推送至远程：`git push -u origin feature/your-topic-name`

**阶段四：引导 PR 创建** — 推送完成后，必须主动向用户确认，并提供创建 Pull Request 的链接，等待 CI 检查通过后再行合并。

### 3. 异常处理
- 如果发现当前处于 `main` 分支且有未提交的更改，必须执行 `git stash`，切换到新分支后再 `git stash pop`。
- 如果 CI 报告 `build` 失败，必须根据日志在当前功能分支修复，直至绿勾出现。

**注意：** 即使当前仓库只有一名维护者，也必须执行此流程以触发 GitHub Actions 自动化部署逻辑。