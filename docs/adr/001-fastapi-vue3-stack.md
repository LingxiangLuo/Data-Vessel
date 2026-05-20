# ADR 001: FastAPI + Vue 3 技术栈选型

## 状态

已接受

## 背景

数据中台门户需要一套前后端分离的技术栈，要求：
- 后端：Python 生态（团队主力语言），高性能异步 API
- 前端：现代响应式框架，中后台系统

## 决策

- **后端**: FastAPI + SQLAlchemy + uvicorn
- **前端**: Vue 3 + Vite + TypeScript + Arco Design
- **数据库**: MySQL 8
- **调度引擎**: DolphinScheduler 3.x

## 后果

### 正面
- FastAPI 自动生成 OpenAPI 文档，前后端对接成本低
- Vue 3 Composition API 适合复杂状态管理
- Arco Design 提供完整中后台组件库

### 负面
- FastAPI 异步 + SQLAlchemy sync 混合，易出现 async/await 遗漏
- Vue 3 无 `@/` 路径别名，所有导入用相对路径
