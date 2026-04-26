# AI Context

## 项目结构

本项目是一个前后端分离的 AI 资源监控后台，当前技术栈为 `Vue 3 + Flask + PostgreSQL`，并保留 `Prometheus / mock-prometheus` 两种数据源接入方式。

```text
AI-control/
├── backend/                # Flask 后端 API、鉴权、多租户、RBAC、Prometheus 访问
│   ├── app/
│   │   ├── api/            # auth / system / tenant / monitor / health 路由
│   │   ├── extensions/     # db, docs 等 Flask 扩展注册
│   │   ├── schemas/        # marshmallow schema / OpenAPI 契约
│   │   ├── services/       # auth、tenant、monitor、prometheus 业务逻辑
│   │   ├── config.py       # 环境变量与应用配置
│   │   ├── models.py       # Tenant / User / Membership / RefreshTokenSession
│   │   └── security.py     # JWT、鉴权上下文、角色校验
│   ├── migrations/         # 当前为初始 SQL schema
│   ├── tests/              # pytest 后端测试
│   ├── requirements.txt
│   └── run.py
├── frontend/               # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── api/            # axios 封装与业务 API
│   │   ├── components/     # 图表、统计卡片、页头等复用组件
│   │   ├── layouts/        # 后台布局
│   │   ├── router/         # 路由与权限守卫
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── types/          # TS 类型定义
│   │   ├── views/          # 登录、仪表盘、租户管理、会话管理等页面
│   │   └── __tests__/      # Vitest 前端测试
│   ├── nginx/              # 生产镜像中的 Nginx 反代配置
│   └── Dockerfile
├── mock-prometheus/        # 本地 demo 用的 Prometheus API mock
├── k8s/                    # K8S 部署模板
├── docker-compose.yml      # 标准本地联调
├── docker-compose.mock.yml # 覆盖为 demo/mock 数据源
├── README.md               # 面向使用者的启动与接口说明
├── AGENTS.md               # 强制 PR 工作流约束
└── CLAUDE.md               # 辅助型仓库上下文说明
```

## 规范

### Git 协作

- 禁止直接向 `main` 推送。
- 所有修改必须在 `feature/*` 或 `fix/*` 分支完成。
- 推送前至少完成一次本地验证，推送后通过 PR 合并。
- 提交信息使用 Conventional Commits：
  - `feat:` 新功能
  - `fix:` 修复
  - `docs:` 文档
  - `chore:` 配置或杂项维护

### 后端约定

- 使用 Flask app factory，不在模块导入阶段做重初始化。
- API 保持 `/api/*` 前缀，响应统一返回 JSON。
- 权限模型固定为：
  - 系统级：`system_admin`
  - 租户级：`owner / admin / viewer`
- 监控接口必须受鉴权保护，租户上下文从 token 获取，不从 query/header 临时传 `tenant_id`。
- Prometheus 访问统一收口到 `backend/app/services/prometheus_client.py`，不要在路由层直接拼 Prometheus 请求。
- 业务规则优先写在 `services/`，路由层只做参数接收、schema 校验和响应组织。

### 前端约定

- 业务 API 调用统一走 `frontend/src/api/`，不要在页面里直接写裸 `axios`。
- 登录态、token、当前租户和用户信息统一放在 `frontend/src/stores/auth.ts`。
- 页面权限控制同时做两层：
  - 路由守卫拦截未登录和越权访问
  - 组件级控制隐藏无权限按钮和入口
- 监控数据状态统一由 `frontend/src/stores/monitor.ts` 管理。
- 表单提交前做前端校验，尤其是邮箱格式、密码长度、必填字段。

### 测试与验证

- 后端测试：`cd backend && pytest`
- 前端测试：`cd frontend && npm test`
- 前端构建：`cd frontend && npm run build`
- Compose 联调：
  - 真实数据源：`docker compose up --build`
  - demo 数据源：`docker compose -f docker-compose.yml -f docker-compose.mock.yml up --build`

### 文档约定

- `README.md` 面向项目使用者，写启动方式、环境变量、接口入口。
- `ai-context.md` 面向协作开发者和 AI Agent，写结构、约束、roadmap。
- `AGENTS.md` 是 Git 协议约束文件，优先级高于一般性文档说明。

## 当前 Roadmap

### P0 已完成

- Vue + Flask + PostgreSQL 项目骨架搭建完成。
- `docker-compose` 与 `docker-compose.mock.yml` 本地联调链路可用。
- Prometheus 与 `mock-prometheus` 双数据源模式已接通。
- 多租户登录、JWT access/refresh token、会话管理已实现。
- 系统级与租户级 RBAC 已实现。
- 监控接口已接入鉴权保护。
- 基础前端页面已完成：
  - 登录页
  - 仪表盘
  - 系统租户管理
  - 租户成员管理
  - 租户设置
  - 个人会话页

### P1 近期优先

- 建立 GitHub Actions CI：
  - 后端测试
  - 前端测试与构建
  - Docker 镜像构建
- 补全 PR 工作流，确保所有改动走分支和 CI。
- 提升前端表单错误提示，把后端 `422` 具体校验错误映射到界面。
- 补更多鉴权与多租户集成测试，覆盖 refresh token、会话撤销、角色边界。

### P2 下一阶段

- 从“初始 SQL 文件”升级到正式迁移工作流，例如 Flask-Migrate/Alembic。
- 增加租户邀请、重置密码、首次登录改密等用户管理流程。
- 引入审计日志，记录登录、创建成员、角色变更、会话吊销等关键操作。
- 完善 K8S 部署流程，接入镜像发布和环境变量管理。

### P3 中长期

- 接入真实告警能力，例如阈值告警、通知渠道和事件记录。
- 评估 Prometheus 指标维度上的租户隔离策略，而不只是在应用层做访问隔离。
- 如果恢复 AI 对话场景，再补 SSE/流式输出与对应前端承载页。
- 增加更完整的运维能力，例如仪表盘配置化、监控项扩展、租户级资源视图。

## 当前项目判断

- 这个仓库已经不是“纯监控 demo”，而是一个具备多租户后台雏形的正式应用。
- 当前最缺的不是页面数量，而是发布流程、迁移体系和更稳的错误处理。
- 后续开发应优先避免直接在页面层堆逻辑，继续保持：
  - 后端：`api -> service -> model`
  - 前端：`view -> store -> api`
