# 项目开发规范

## 技术栈
- 前端：Vue 3 + Vite + Vue Router + Pinia + Element Plus + ECharts
- 后端：Python flask
- 数据库：PostgreSQL
- 部署：
  - local:docker-compose
  - web: kubernets

## 代码规范
- 使用 4 空格缩进
- 每行最多 100 字符
- 所有函数必须有类型注解

## 测试要求
- 新功能必须包含测试
- 使用 pytest 运行测试

## Git 提交
- 使用 Conventional Commits 格式
- 提交信息描述"为什么"
