# AI Context

## 项目结构

本项目是一个前后端分离的 AI 资源监控后台，技术栈为 `Vue 3 + Flask + PostgreSQL`，监控数据源统一使用内置 Prometheus 采集链路。

```text
AI-control/
├── backend/            # Flask API、鉴权、多租户、RBAC、监控/日志/聊天/分析接口
├── frontend/           # Vue 3 + Vite + Element Plus + ECharts
├── ollama-exporter/    # Ollama 模型元数据与推理指标 exporter
├── infra/prometheus/   # Prometheus scrape 配置
├── k8s/                # Kubernetes 部署清单
├── docker-compose.yml  # 本地联调
├── docker-compose.gpu.yml
├── README.md
├── AGENTS.md
└── CLAUDE.md
```

## 规范

- 所有业务改动走 `feature/*` 或 `fix/*` 分支，通过 PR 合并，不直接推送 `main`。
- 后端 API 统一使用 `/api/*` 前缀，路由层只做参数、鉴权和响应组织，业务逻辑放在 `services/`。
- Prometheus 访问统一经过 `backend/app/services/prometheus_client.py`，前端不能传任意 PromQL。
- 多租户上下文来自 JWT token，不从 query/header 临时传 `tenant_id`。
- 前端接口调用统一放在 `frontend/src/api/`，页面通过 Pinia store 管理业务状态。
- 表单提交前做前端校验，后端继续保留 schema 和权限校验。

## 当前 Roadmap

### 已完成

- Vue + Flask + PostgreSQL 项目骨架。
- 多租户登录、JWT access/refresh token、会话管理。
- 系统级与租户级 RBAC。
- 内置 Prometheus + node-exporter + backend `/metrics` 采集链路。
- GPU 指标扩展，支持可选 `dcgm-exporter`。
- Ollama exporter 与模型监控页。
- Prometheus 状态页和指标目录 API。
- Elasticsearch Logs API 和日志页。
- Ollama AI 分析与网页聊天。
- GitHub Actions CI/CD、镜像发布和 K8S 部署模板。

### 近期优先

- 继续补齐后端和前端集成测试，覆盖聊天、日志、Prometheus 状态和 GPU 边界场景。
- 完善错误提示映射，尤其是后端 `422/502` 到前端的用户可读消息。
- 强化 K8S 部署文档，明确 Ollama、Prometheus、Elasticsearch 外部依赖和 GPU 可选路径。

### 后续方向

- 从初始 SQL 文件升级到正式 Alembic migration 工作流。
- 增加用户邀请、重置密码、首次登录改密等账号生命周期流程。
- 增加审计日志，记录登录、成员管理、角色变更、会话吊销、AI 分析和聊天操作。
- 评估 Prometheus 指标维度上的租户隔离策略。
