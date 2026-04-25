# AI 资源监测平台

`AI-control` 是一个支持多租户登录、租户级 RBAC 和监控看板的后台系统，采用 `Vue 3 + Flask + PostgreSQL` 的前后端分离结构。前端始终访问 `/api/*`，后端通过 `JWT access token + refresh token` 维护会话，通过 `tenantSlug + email + password` 明确进入租户上下文。

## 目录结构

```text
AI-control/
├── backend/              # Flask API、SQLAlchemy、JWT、租户与成员管理
├── frontend/             # Vue 3 + Vite + Element Plus + ECharts
├── k8s/                  # Kubernetes 部署模板
├── mock-prometheus/      # Prometheus API mock，仅用于本地 demo
├── docker-compose.yml
├── docker-compose.mock.yml
├── .env.example
└── README.md
```

## 核心能力

- 多租户登录：登录时显式输入 `tenantSlug`
- 权限模型：
  - 系统级：`system_admin`
  - 租户级：`owner / admin / viewer`
- 监控接口默认受保护，必须先登录后访问
- 支持本地真实 Prometheus 和 mock Prometheus 两种数据源

## 默认引导账户

应用启动后会根据环境变量自动引导默认租户和系统管理员。

- 默认租户：`default`
- 默认管理员邮箱：`admin@example.local`
- 默认管理员密码：`ChangeMe123!`

首次启动后请立即修改这些值。

## 本地运行

### 1. 配置环境变量

```bash
cp .env.example .env
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Swagger 文档默认位于 `http://localhost:5000/api/docs/`。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认开发地址为 `http://localhost:5173`，并通过 Vite 代理访问后端 `/api`。

## Docker Compose

### 真实 Prometheus 模式

```bash
docker compose up --build
```

### Mock Demo 模式

```bash
docker compose -f docker-compose.yml -f docker-compose.mock.yml up --build
```

此模式会额外启动 `mock-prometheus` 服务，并把后端 `PROMETHEUS_BASE_URL` 覆盖为 `http://mock-prometheus:9090`。即使在 demo 模式下，监控接口也仍然要求先登录。

默认暴露：

- 前端：`http://localhost:8080`
- 后端：`http://localhost:5000`
- PostgreSQL：`localhost:5432`
- Mock Prometheus：`http://localhost:9090`

## 主要接口

认证与会话：

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET /api/auth/sessions`
- `DELETE /api/auth/sessions/{sessionId}`

系统管理员：

- `GET /api/system/tenants`
- `POST /api/system/tenants`
- `POST /api/system/tenants/{tenantId}/members`

租户管理：

- `GET /api/tenant`
- `PATCH /api/tenant`
- `GET /api/tenant/members`
- `POST /api/tenant/members`
- `PATCH /api/tenant/members/{membershipId}`
- `DELETE /api/tenant/members/{membershipId}`

监控接口：

- `GET /api/health`
- `GET /api/monitor/overview`
- `GET /api/monitor/timeseries?metric=cpu|memory|disk|gpu&range=1h|6h|24h&step=30s|1m`

Mock Prometheus 内部接口，仅供后端调用：

- `GET /api/v1/query`
- `GET /api/v1/query_range`

## 数据模型

- `Tenant`
- `User`
- `TenantMembership`
- `RefreshTokenSession`

数据库迁移初始 SQL 位于 [backend/migrations/001_initial_schema.sql](/e:/source/code/python3/AI-control/backend/migrations/001_initial_schema.sql:1)。

## 测试

后端测试：

```bash
cd backend
pytest
```

前端测试：

```bash
cd frontend
npm test
```

Mock Prometheus 测试：

```bash
cd mock-prometheus
pytest
```
