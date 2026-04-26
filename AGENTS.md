# Agent 操作协议 (强制性 PR 工作流)

作为本项目的执行 Agent，你必须严格遵守以下 Git 协作协议。此协议旨在利用 CI 流水线保护 `main` 分支的稳定性，严禁任何形式的直接推送。

## 1. 核心规则 (Golden Rules)
- **禁止直推**：严禁直接在 `main` 分支执行 `git push`。
- **分支隔离**：所有代码变更（包括文档更新）必须在 `feature/*` 或 `fix/*` 分支进行。
- **验证优先**：在建议合并前，必须确保本地或远程 CI 的 `build` 任务已成功运行。

## 2. 标准作业程序 (SOP)

### 阶段一：环境对齐
在开始任何任务（撰写博客、修改配置等）之前，必须同步主分支状态：

```bash
git checkout main
git pull origin main
```

### 阶段二：功能分支开发
1. 创建并切换分支（命名应具有语义化）：
   ```bash
   git checkout -b feature/your-topic-name
   ```
2. 执行修改。
3. 如果本项目包含 `mkdocs`，在提交前建议执行本地构建检查：
   ```bash
   pip install -r requirements.txt && mkdocs build --strict
   ```

### 阶段三：提交与推送
1. 提交信息须遵循约定式提交（Conventional Commits）：
   - `feat:` 新内容/新文章
   - `fix:` 修复错误
   - `docs:` 仅文档修改
   - `chore:` 配置更新
2. 推送至远程：
   ```bash
   git push -u origin feature/your-topic-name
   ```

### 阶段四：引导 PR 创建
推送完成后，你必须主动向用户确认：

> "任务已在分支 `feature/xxx` 上完成并推送到远程。请点击以下链接创建 Pull Request 并等待 CI 检查通过后再行合并。"

## 3. 异常处理
- 如果发现当前处于 `main` 分支且有未提交的更改，必须执行 `git stash`，切换到新分支后再 `git stash pop`。
- 如果 CI 报告 `build` 失败，必须根据日志在当前功能分支修复，直至绿勾出现。

---

**注意：** 即使当前仓库只有一名维护者，也必须执行此流程以触发 GitHub Actions 自动化部署逻辑。
