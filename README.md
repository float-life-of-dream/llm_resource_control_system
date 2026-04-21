# AI 资源监测平台

`AI-control` 是一个面向 AI 工作负载的资源监控后台，当前脚手架采用 `Vue 3 + Flask + PostgreSQL` 的前后端分离结构，监控主数据通过 Prometheus 获取。

## 目录结构

```text
AI-control/
├── backend/              # Flask API、Prometheus 查询封装、Swagger
├── frontend/             # Vue 3 + Vite + Element Plus + ECharts
├── k8s/                  # Kubernetes 部署模板
├── docker-compose.yml    # 本地联调编排
├── .env.example          # 环境变量示例
└── README.md
```

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

### 4. Docker Compose

```bash
docker compose up --build
```

默认暴露：

- 前端：`http://localhost:8080`
- 后端：`http://localhost:5000`
- PostgreSQL：`localhost:5432`

## 当前接口

- `GET /api/health`
- `GET /api/monitor/overview`
- `GET /api/monitor/timeseries?metric=cpu|memory|disk|gpu&range=1h|6h|24h&step=30s|1m`

## 说明

- 第一版不做登录鉴权。
- PostgreSQL 目前只做容器化和后续扩展预留，不进入主业务流程。
- Nginx 已预留 `proxy_buffering off;` 以兼容后续 SSE/流式接口。
